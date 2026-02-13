"""Tier-conditional lighting dispatch."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import vtk

from oco_viz.render.lighting import apply_lighting

if TYPE_CHECKING:
    from oco_viz.config.schema import ScatteringConfig


class LightingMode(str, Enum):
    """Lighting mode selected by tier.

    none: no lighting computation (sketch)
    basic: three-point lighting rig (study)
    smoldering: internal glow only, no external lights (exhibition)
    """

    none = "none"
    basic = "basic"
    smoldering = "smoldering"
    smoldering_key = "smoldering_key"


def apply_lighting_for_tier(
    renderer: vtk.vtkRenderer,
    volume_property: vtk.vtkVolumeProperty,
    mode: str,
    scattering: ScatteringConfig,
) -> None:
    """Apply lighting and material properties based on tier mode.

    Parameters
    ----------
    renderer
        VTK renderer to configure lighting on.
    volume_property
        Volume property to adjust shading parameters.
    mode
        One of "none", "basic", "smoldering".
    scattering
        Scattering config providing material property values.
    """
    resolved = LightingMode(mode)

    if resolved is LightingMode.none:
        volume_property.ShadeOff()
        return

    # Both basic and smoldering use shading — apply material props from config
    volume_property.ShadeOn()
    volume_property.SetAmbient(scattering.ambient)
    volume_property.SetDiffuse(scattering.diffuse)
    volume_property.SetSpecular(scattering.specular)

    if resolved is LightingMode.basic:
        apply_lighting(renderer)

    elif resolved is LightingMode.smoldering:
        renderer.RemoveAllLights()

    elif resolved is LightingMode.smoldering_key:
        renderer.RemoveAllLights()
        key = vtk.vtkLight()
        key.SetPosition(-1.0, -0.8, 0.6)
        key.SetIntensity(0.8)
        key.SetColor(0.95, 0.92, 0.85)
        renderer.AddLight(key)
