"""Unified gallery infrastructure: wave registry, module loading, and constants."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

# Canonical wave names — order determines default rendering sequence.
WAVE_NAMES: list[str] = [
    "base",
    "2",
    "3",
    "4",
    "5",
    "6",
    "exhibition",
    "real_data",
]

# Map wave name -> script module path
_WAVE_MODULES: dict[str, str] = {
    "base": "scripts.render_gallery",
    "2": "scripts.render_wave2_gallery",
    "3": "scripts.render_wave3_gallery",
    "4": "scripts.render_wave4_gallery",
    "5": "scripts.render_wave5_gallery",
    "6": "scripts.render_wave6_gallery",
    "exhibition": "scripts.render_exhibition_gallery",
    "real_data": "scripts.render_real_data_gallery",
}

# Default tier for each wave when no --tier is specified.
WAVE_DEFAULT_TIER: dict[str, str] = {
    "base": "study",
    "2": "study",
    "3": "study",
    "4": "study",
    "5": "study",
    "6": "study",
    "exhibition": "exhibition",
    "real_data": "study",
}


def load_wave_module(wave_name: str) -> ModuleType:
    """Dynamically import and return the gallery module for *wave_name*.

    Raises ``KeyError`` if *wave_name* is not in ``WAVE_NAMES`` and
    ``ImportError`` if the module cannot be loaded.
    """
    if wave_name not in _WAVE_MODULES:
        msg = f"unknown wave: {wave_name!r} (valid: {', '.join(WAVE_NAMES)})"
        raise KeyError(msg)
    return importlib.import_module(_WAVE_MODULES[wave_name])
