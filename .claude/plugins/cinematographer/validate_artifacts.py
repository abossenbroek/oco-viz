"""Artifact format validator."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import yaml


PLUGIN_ROOT = Path(__file__).parent

# Extensions mapped to validation functions.
VALIDATORS: dict[str, str] = {
    ".py": "python",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".ocio": "ocio",
    ".usda": "usd",
}


# ---------------------------------------------------------------------------
# Per-format validators
# ---------------------------------------------------------------------------


def validate_python(path: Path) -> str | None:
    """Check Python file with ast.parse(). Returns error message or None."""
    try:
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return f"SyntaxError: {exc.msg} (line {exc.lineno})"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading file: {exc}"
    return None


def validate_yaml(path: Path) -> str | None:
    """Check YAML file with yaml.safe_load(). Returns error message or None."""
    try:
        text = path.read_text(encoding="utf-8")
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return f"YAML error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading file: {exc}"
    return None


def validate_json(path: Path) -> str | None:
    """Check JSON file with json.loads(). Returns error message or None."""
    try:
        text = path.read_text(encoding="utf-8")
        json.loads(text)
    except json.JSONDecodeError as exc:
        return f"JSON error: {exc.msg} (line {exc.lineno})"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading file: {exc}"
    return None


def validate_ocio(path: Path) -> str | None:
    """Check OCIO config: correct extension + basic structure."""
    if path.suffix != ".ocio":
        return f"Expected .ocio extension, got {path.suffix}"
    try:
        text = path.read_text(encoding="utf-8")
        if "ocio_profile_version" not in text and "colorspaces" not in text:
            return "OCIO file missing expected keys (ocio_profile_version or colorspaces)"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading file: {exc}"
    return None


def validate_usd(path: Path) -> str | None:
    """Check USD (.usda) text format: correct extension + basic structure."""
    if path.suffix != ".usda":
        return f"Expected .usda extension, got {path.suffix}"
    try:
        text = path.read_text(encoding="utf-8")
        if "#usda" not in text[:100]:
            return "USD file missing '#usda' header in first 100 characters"
    except Exception as exc:  # noqa: BLE001
        return f"Error reading file: {exc}"
    return None


VALIDATE_DISPATCH = {
    "python": validate_python,
    "yaml": validate_yaml,
    "json": validate_json,
    "ocio": validate_ocio,
    "usd": validate_usd,
}


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_files(root: Path) -> list[Path]:
    """Collect all files under *root* whose extension we can validate."""
    results: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in VALIDATORS:
            results.append(path)
    return results


def validate_file(path: Path) -> tuple[str, str | None]:
    """Validate a single file. Returns (format_name, error_or_none)."""
    fmt = VALIDATORS.get(path.suffix, "unknown")
    fn = VALIDATE_DISPATCH.get(fmt)
    if fn is None:
        return fmt, f"No validator for format '{fmt}'"
    return fmt, fn(path)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------


def self_test() -> int:
    """Validate all supported files within the plugin directory itself."""
    print(f"Self-test: scanning {PLUGIN_ROOT}")
    print("=" * 50)

    files = scan_files(PLUGIN_ROOT)
    if not files:
        print("  No validatable files found.")
        return 0

    errors = 0
    for path in files:
        rel = path.relative_to(PLUGIN_ROOT)
        fmt, err = validate_file(path)
        if err:
            print(f"  FAIL  [{fmt}] {rel}: {err}")
            errors += 1
        else:
            print(f"  PASS  [{fmt}] {rel}")

    print(f"\n{len(files)} files checked, {errors} error(s)")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# General validation
# ---------------------------------------------------------------------------


def validate_paths(paths: list[Path]) -> int:
    """Validate a list of explicit file paths."""
    errors = 0
    for path in paths:
        if not path.exists():
            print(f"  FAIL  {path}: file not found")
            errors += 1
            continue
        fmt, err = validate_file(path)
        if err:
            print(f"  FAIL  [{fmt}] {path}: {err}")
            errors += 1
        else:
            print(f"  PASS  [{fmt}] {path}")

    print(f"\n{len(paths)} files checked, {errors} error(s)")
    return 1 if errors else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point."""
    args = sys.argv[1:]

    if "--self-test" in args:
        return self_test()

    if not args:
        print("Usage:")
        print("  python validate_artifacts.py --self-test")
        print("  python validate_artifacts.py FILE [FILE ...]")
        return 0

    return validate_paths([Path(a) for a in args])


if __name__ == "__main__":
    sys.exit(main())
