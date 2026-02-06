"""Sky gradient background for VTK renderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import vtk

    from oco_viz.config.schema import SkyConfig


def apply_sky_gradient(renderer: vtk.vtkRenderer, config: SkyConfig) -> None:
    """Apply a vertical gradient background to the VTK renderer.

    Uses VTK's built-in two-color gradient: ``SetBackground`` is the bottom
    color (horizon), ``SetBackground2`` is the top color (zenith).
    """
    if not config.enabled:
        renderer.GradientBackgroundOff()
        renderer.SetBackground(0.0, 0.0, 0.0)
        return

    renderer.SetBackground(*config.bottom_color)
    renderer.SetBackground2(*config.top_color)
    renderer.GradientBackgroundOn()
