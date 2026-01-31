"""Detect available VTK rendering backend (EGL, OSMesa, or native offscreen)."""

from __future__ import annotations

import enum
import logging
import sys

import vtk

logger = logging.getLogger(__name__)


class Backend(enum.Enum):
    """Supported offscreen rendering backends."""

    EGL = "egl"
    OSMESA = "osmesa"
    NATIVE = "native"  # Cocoa/X11 offscreen


def _try_egl() -> bool:
    cls = getattr(vtk, "vtkEGLRenderWindow", None)
    if cls is None:
        return False
    try:
        win = cls()
        win.SetOffScreenRendering(True)
        win.SetSize(8, 8)
        win.Render()
        win.Finalize()
        return True
    except Exception:  # noqa: BLE001
        return False


def _try_osmesa() -> bool:
    if sys.platform == "darwin":
        return False
    cls = getattr(vtk, "vtkOSOpenGLRenderWindow", None)
    if cls is None:
        return False
    try:
        win = cls()
        win.SetOffScreenRendering(True)
        win.SetSize(8, 8)
        win.Render()
        win.Finalize()
        return True
    except Exception:  # noqa: BLE001
        return False


def _try_native() -> bool:
    try:
        win = vtk.vtkRenderWindow()
        win.SetOffScreenRendering(True)
        win.SetSize(8, 8)
        win.Render()
        win.Finalize()
        return True
    except Exception:  # noqa: BLE001
        return False


def detect_backend() -> Backend:
    """Probe EGL > OSMesa > native offscreen. Raise RuntimeError if none works."""
    if _try_egl():
        logger.info("Using EGL backend")
        return Backend.EGL

    if _try_osmesa():
        logger.info("Using OSMesa backend")
        return Backend.OSMESA

    if _try_native():
        logger.info("Using native offscreen backend")
        return Backend.NATIVE

    msg = "No usable offscreen VTK backend found."
    raise RuntimeError(msg)
