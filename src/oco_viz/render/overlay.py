"""OCO satellite observation overlay using VTK point gaussians."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib as mpl
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

if TYPE_CHECKING:
    import xarray as xr

    from oco_viz.config.schema import GridConfig, OverlayConfig


def has_observations(ds: xr.Dataset) -> bool:
    """Return True if dataset contains at least one non-NaN xco2 observation."""
    if "xco2_observed" not in ds.data_vars:
        return False
    values = ds["xco2_observed"].values
    return bool(np.any(np.isfinite(values)))


def create_observation_overlay(
    obs_data: xr.Dataset,
    grid: GridConfig,
    overlay_cfg: OverlayConfig,
) -> vtk.vtkActor:
    """Create a VTK actor with point gaussians for OCO observation footprints.

    Each observation is rendered as a soft dot at ground level, colored by
    XCO2 enhancement above the configured background concentration.

    Parameters
    ----------
    obs_data
        Dataset with ``xco2_observed``, ``obs_x``, ``obs_y`` variables.
    grid
        Grid configuration for coordinate scaling.
    overlay_cfg
        Overlay visual parameters (colormap, dot scale, etc.).

    Returns
    -------
    vtkActor
        Point gaussian actor ready to add to a VTK renderer.
    """
    xco2 = obs_data["xco2_observed"].values.astype(np.float64)
    obs_x = obs_data["obs_x"].values.astype(np.float64)
    obs_y = obs_data["obs_y"].values.astype(np.float64)

    # Filter NaN values
    valid = np.isfinite(xco2)
    xco2 = xco2[valid]
    obs_x = obs_x[valid]
    obs_y = obs_y[valid]

    # Create polydata
    points = vtk.vtkPoints()
    poly = vtk.vtkPolyData()

    if len(xco2) > 0:
        # Compute enhancement and normalize to [0, 1]
        enhancement = xco2 - overlay_cfg.background_ppm
        normalized = np.clip(enhancement / overlay_cfg.max_enhancement_ppm, 0.0, 1.0)

        # Map to colors using matplotlib colormap
        cmap = mpl.colormaps[overlay_cfg.colormap]
        rgba = cmap(normalized)  # (N, 4) float64 in [0, 1]
        colors_uint8 = (rgba[:, :3] * 255).astype(np.uint8)

        # Build VTK points at ground level with slight z-offset
        coords = np.column_stack(
            [obs_x / grid.dx, obs_y / grid.dy, np.full(len(xco2), 0.1)]
        )
        vtk_points = numpy_to_vtk(coords, deep=True)
        points.SetData(vtk_points)

        # Build color array via numpy_to_vtk (vectorized)
        colors_contiguous = np.ascontiguousarray(colors_uint8)
        vtk_colors = numpy_to_vtk(colors_contiguous, deep=True)
        vtk_colors.SetNumberOfComponents(3)
        vtk_colors.SetName("Colors")

        # Build vertex cells from numpy connectivity array (vectorized)
        n_pts = len(xco2)
        connectivity = np.arange(n_pts, dtype=np.int64)
        offsets = np.arange(n_pts + 1, dtype=np.int64)
        verts = vtk.vtkCellArray()
        vtk_conn = numpy_to_vtk(connectivity, deep=True)
        vtk_offs = numpy_to_vtk(offsets, deep=True)
        verts.SetData(vtk_offs, vtk_conn)

        poly.SetPoints(points)
        poly.SetVerts(verts)
        poly.GetPointData().SetScalars(vtk_colors)
    else:
        poly.SetPoints(points)

    # Point gaussian mapper for soft dot rendering
    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(poly)
    mapper.SetScaleFactor(overlay_cfg.dot_scale)
    mapper.EmissiveOff()
    mapper.SetSplatShaderCode("")

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Configure emissive appearance
    prop = actor.GetProperty()
    brightness = overlay_cfg.emissive_brightness
    prop.SetAmbient(min(brightness, 1.0))
    prop.SetDiffuse(max(0.0, 1.0 - brightness * 0.5))

    return actor
