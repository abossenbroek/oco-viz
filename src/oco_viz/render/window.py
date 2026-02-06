"""Create offscreen VTK render window for the detected backend."""

from __future__ import annotations

import vtk

from oco_viz.render.backend import Backend, detect_backend


def create_render_window(
    width: int = 1920,
    height: int = 1080,
    *,
    backend: Backend | None = None,
) -> vtk.vtkRenderWindow:
    """Create an offscreen VTK render window.

    Parameters
    ----------
    width, height:
        Pixel dimensions of the render target.
    backend:
        Force a specific backend. Auto-detected if None.

    """
    if backend is None:
        backend = detect_backend()

    win: vtk.vtkRenderWindow
    if backend == Backend.EGL:
        win = vtk.vtkEGLRenderWindow()
    elif backend == Backend.OSMESA:
        win = vtk.vtkOSOpenGLRenderWindow()
    else:
        win = vtk.vtkRenderWindow()

    win.SetOffScreenRendering(True)
    win.SetMultiSamples(0)
    win.SetSize(width, height)
    return win
