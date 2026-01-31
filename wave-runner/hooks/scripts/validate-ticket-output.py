#!/usr/bin/env python3
"""PostToolUse hook: validate ticket output conventions.

Reads PostToolUse JSON from stdin. Checks:
- Python files have `from __future__ import annotations`
- Files are under src/, tests/, or scripts/
- Config file edits get CONFIG-FIX classification warning

Always exits 0 — warnings go to stderr, never blocks.
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input or invalid JSON — nothing to validate
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    file_path = data.get("file_path", "") or data.get("input", {}).get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Check: Python files should have future annotations
    if tool_name == "Write" and file_path.endswith(".py"):
        content = data.get("content", "") or data.get("input", {}).get("content", "")
        if content and "from __future__ import annotations" not in content:
            print(
                f"WARNING: {file_path} missing `from __future__ import annotations`",
                file=sys.stderr,
            )

    # Check: files should be under src/, tests/, or scripts/
    if tool_name == "Write":
        allowed_prefixes = ("src/", "tests/", "scripts/", "configs/", "plan/")
        path_parts = file_path.replace("\\", "/")
        # Check if any allowed prefix appears in the path
        if not any(f"/{prefix}" in f"/{path_parts}" or path_parts.startswith(prefix) for prefix in allowed_prefixes):
            # Allow config files at root
            root_allowed = ("pyproject.toml", "pixi.toml", "setup.cfg", "setup.py")
            basename = path_parts.rsplit("/", 1)[-1] if "/" in path_parts else path_parts
            if basename not in root_allowed:
                print(
                    f"WARNING: {file_path} is outside standard directories (src/, tests/, scripts/)",
                    file=sys.stderr,
                )

    # Check: config file edits should be classified as CONFIG-FIX
    if tool_name in ("Write", "Edit"):
        config_files = ("pyproject.toml", "pixi.toml", "ruff.toml", ".mypy.ini")
        basename = file_path.rsplit("/", 1)[-1] if "/" in file_path else file_path
        if basename in config_files:
            print(
                f"INFO: Config file edit ({basename}) — classify as CONFIG-FIX if gate-related",
                file=sys.stderr,
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
