"""VTK volume rendering from numpy arrays with scattering support."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import ScatteringConfig

from oco_viz.render.transfer import TransferFunction
from oco_viz.render.window import create_render_window


def make_gaussian_blob(
    shape: tuple[int, int, int] = (60, 100, 100),
) -> NDArray[np.float32]:
    """Create a 3D Gaussian blob centered in the volume."""
    zz, yy, xx = np.mgrid[
        0 : shape[0],
        0 : shape[1],
        0 : shape[2],
    ]
    cz, cy, cx = shape[0] / 2, shape[1] / 2, shape[2] / 2
    sz, sy, sx = shape[0] / 6, shape[1] / 6, shape[2] / 6
    blob = np.exp(
        -((xx - cx) ** 2) / (2 * sx**2)
        - (yy - cy) ** 2 / (2 * sy**2)
        - (zz - cz) ** 2 / (2 * sz**2)
    )
    result: NDArray[np.float32] = blob.astype(np.float32)
    return result


def numpy_to_vtk_image(data: NDArray[np.float32]) -> vtk.vtkImageData:
    """Convert a 3D numpy array to vtkImageData."""
    image = vtk.vtkImageData()
    nz, ny, nx = data.shape
    image.SetDimensions(nx, ny, nz)
    image.SetSpacing(1.0, 1.0, 1.0)
    image.SetOrigin(0.0, 0.0, 0.0)

    flat = np.ascontiguousarray(data.ravel(order="F"))
    vtk_arr = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_arr.SetName("density")
    image.GetPointData().SetScalars(vtk_arr)
    return image


def create_volume(
    image_data: vtk.vtkImageData,
    color_tf: vtk.vtkColorTransferFunction,
    opacity_tf: vtk.vtkPiecewiseFunction,
    *,
    scattering: ScatteringConfig | None = None,
) -> vtk.vtkVolume:
    """Create a VTK volume actor with scattering parameters.

    Parameters
    ----------
    image_data:
        3D scalar field as vtkImageData.
    color_tf:
        Color transfer function.
    opacity_tf:
        Opacity transfer function.
    scattering:
        Optional scattering configuration. Uses defaults if None.

    """
    volume_property = vtk.vtkVolumeProperty()
    volume_property.SetColor(color_tf)
    volume_property.SetScalarOpacity(opacity_tf)
    volume_property.SetInterpolationTypeToLinear()

    if scattering is None or scattering.shade:
        volume_property.ShadeOn()
    else:
        volume_property.ShadeOff()

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputData(image_data)

    if scattering is not None:
        mapper.SetGlobalIlluminationReach(scattering.global_illumination_reach)
        mapper.SetVolumetricScatteringBlending(scattering.volumetric_scattering_blending)
        volume_property.SetScatteringAnisotropy(scattering.anisotropy)

        if scattering.jittering:
            mapper.SetUseJittering(True)

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(volume_property)
    return volume


def render_blob_to_png(
    output_path: Path,
    *,
    width: int = 512,
    height: int = 512,
    shape: tuple[int, int, int] = (60, 100, 100),
) -> None:
    """Render a Gaussian blob volume to a PNG file."""
    blob = make_gaussian_blob(shape)
    image_data = numpy_to_vtk_image(blob)

    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()

    volume = create_volume(image_data, color_tf, opacity_tf)

    renderer = vtk.vtkRenderer()
    renderer.AddVolume(volume)
    renderer.SetBackground(0.1, 0.1, 0.15)
    renderer.ResetCamera()

    win = create_render_window(width=width, height=height)
    win.AddRenderer(renderer)
    win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

    win.Finalize()
