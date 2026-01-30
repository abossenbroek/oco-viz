import os

import pytest
import vtk

from oco_viz.render.backend import Backend, detect_backend
from oco_viz.render.window import create_render_window

_skip_ci = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="VTK EGL segfaults on headless CI",
)


@_skip_ci
def test_detect_backend_returns_valid_enum():
    backend = detect_backend()
    assert isinstance(backend, Backend)


@_skip_ci
def test_create_render_window_returns_vtk_window():
    win = create_render_window(width=128, height=128)
    assert win.GetOffScreenRendering() == 1
    assert win.GetSize() == (128, 128)
    win.Finalize()


@_skip_ci
def test_create_render_window_can_render():
    win = create_render_window(width=64, height=64)
    renderer = vtk.vtkRenderer()
    win.AddRenderer(renderer)
    win.Render()
    win.Finalize()


@_skip_ci
def test_create_render_window_explicit_backend():
    backend = detect_backend()
    win = create_render_window(width=32, height=32, backend=backend)
    assert win.GetOffScreenRendering() == 1
    win.Finalize()
