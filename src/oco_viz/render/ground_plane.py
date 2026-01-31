"""Translucent ground plane grid actor for VTK scenes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import vtk

if TYPE_CHECKING:
    from oco_viz.config.schema import GridConfig, GroundPlaneConfig


def create_ground_plane(
    config: GroundPlaneConfig,
    grid: GridConfig,
) -> vtk.vtkActor:
    """Create a translucent grid plane at z=0 matching the domain extent.

    Grid lines are spaced at ``config.grid_spacing_km`` kilometer intervals
    converted to meters via the grid spacing.
    """
    # Domain extent in grid units
    x_extent = grid.nx * grid.dx
    y_extent = grid.ny * grid.dy

    # Grid spacing in meters (config is in km)
    spacing_m = config.grid_spacing_km * 1000.0

    x_divs = max(int(x_extent / spacing_m), 1)
    y_divs = max(int(y_extent / spacing_m), 1)

    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(0.0, 0.0, 0.0)
    plane.SetPoint1(float(x_extent), 0.0, 0.0)
    plane.SetPoint2(0.0, float(y_extent), 0.0)
    plane.SetXResolution(x_divs)
    plane.SetYResolution(y_divs)
    plane.Update()

    edges = vtk.vtkExtractEdges()
    edges.SetInputConnection(plane.GetOutputPort())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(edges.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*config.color)
    actor.GetProperty().SetOpacity(config.opacity)
    actor.GetProperty().SetLineWidth(1.0)

    return actor
