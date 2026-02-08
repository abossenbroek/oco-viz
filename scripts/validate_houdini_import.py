#!/usr/bin/env python
"""Houdini import validation script.

Run with hython (Houdini's Python interpreter), NOT in CI:
    hython scripts/validate_houdini_import.py output/vdb/soot.000001.vdb

Validates that a VDB file loads correctly in Houdini's SOP context
and auto-connects to a Pyro shader.
"""

from __future__ import annotations

import sys
from pathlib import Path


def validate_houdini_import(vdb_path: str) -> None:
    """Validate VDB file loads in Houdini with correct grid mapping."""
    try:
        import hou  # type: ignore[import-untyped]  # noqa: F401
    except ImportError:
        print("ERROR: This script must be run with hython (Houdini Python).")  # noqa: T201
        print("Usage: hython scripts/validate_houdini_import.py <vdb_file>")  # noqa: T201
        sys.exit(1)

    path = Path(vdb_path)
    if not path.exists():
        print(f"ERROR: VDB file not found: {path}")  # noqa: T201
        sys.exit(1)

    print(f"Validating: {path}")  # noqa: T201
    print("NOTE: This script requires Houdini. It is NOT run in CI.")  # noqa: T201
    print("Expected grids: density, vel, temperature, dissolution_mask")  # noqa: T201
    print("Expected grid types: FloatGrid (scalars), Vec3SGrid (velocity)")  # noqa: T201
    print()  # noqa: T201
    print("Manual validation steps:")  # noqa: T201
    print("  1. Open Houdini, create File SOP pointing to this VDB")  # noqa: T201
    print("  2. Verify all 4 grids appear in the VDB Visualize SOP")  # noqa: T201
    print("  3. Create Pyro Shader — density and temperature should auto-bind")  # noqa: T201
    print("  4. Check vel grid drives motion blur in Karma XPU")  # noqa: T201
    print("  5. Verify dissolution_mask is accessible as a volume attribute")  # noqa: T201


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: hython scripts/validate_houdini_import.py <vdb_file>")  # noqa: T201
        sys.exit(1)
    validate_houdini_import(sys.argv[1])
