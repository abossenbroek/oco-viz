"""Tier-conditional lighting dispatch."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from oco_viz.render.lighting import apply_lighting

if TYPE_CHECKING:
    import vtk


class LightingMode(str, Enum):
    """Lighting mode selected by tier.

    none: no lighting computation (sketch)
    basic: three-point lighting rig (study)
    smoldering: internal glow only, no external lights (exhibition)
    """

    none = "none"
    basic = "basic"
    smoldering = "smoldering"


def apply_lighting_for_tier(
    renderer: vtk.vtkRenderer,
    volume_property: vtk.vtkVolumeProperty,
    mode: str,
) -> None:
    """Apply lighting based on tier mode.

    Parameters
    ----------
    renderer
        VTK renderer to configure lighting on.
    volume_property
        Volume property to adjust shading parameters.
    mode
        One of "none", "basic", "smoldering".
    """
    resolved = LightingMode(mode)

    if resolved is LightingMode.none:
        volume_property.ShadeOff()

    elif resolved is LightingMode.basic:
        apply_lighting(renderer)

    elif resolved is LightingMode.smoldering:
        renderer.RemoveAllLights()
        volume_property.SetAmbient(0.4)
        volume_property.SetDiffuse(0.0)
        volume_property.SetSpecular(0.0)
