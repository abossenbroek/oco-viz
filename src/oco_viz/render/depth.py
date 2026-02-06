"""Extract RGB and depth buffers from VTK render window."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _make_w2i_filter(
    render_window: vtk.vtkRenderWindow,
) -> vtk.vtkWindowToImageFilter:
    """Create a VTK window-to-image filter for the given render window."""
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(render_window)
    return w2i


def extract_rgb(render_window: vtk.vtkRenderWindow) -> NDArray[np.float32]:
    """Extract RGB buffer as float32 array in [0, 1], shape [H, W, 3]."""
    w2i = _make_w2i_filter(render_window)
    w2i.SetInputBufferTypeToRGB()
    w2i.Update()

    image = w2i.GetOutput()
    w, h, _ = image.GetDimensions()
    vtk_arr = image.GetPointData().GetScalars()
    np_arr = vtk_to_numpy(vtk_arr).reshape(h, w, 3)
    # VTK returns bottom-up, flip to top-down
    result: NDArray[np.float32] = np.flipud(np_arr).astype(np.float32) / 255.0
    return result


def extract_depth(render_window: vtk.vtkRenderWindow) -> NDArray[np.float32]:
    """Extract linearized depth buffer as float32 array, shape [H, W].

    Values are in the range [near, far] of the clipping range.
    """
    w2i = _make_w2i_filter(render_window)
    w2i.SetInputBufferTypeToZBuffer()
    w2i.Update()

    image = w2i.GetOutput()
    w, h, _ = image.GetDimensions()
    vtk_arr = image.GetPointData().GetScalars()
    np_arr = vtk_to_numpy(vtk_arr).reshape(h, w)
    result: NDArray[np.float32] = np.flipud(np_arr).astype(np.float32)
    return result
