"""Three-point lighting for late-afternoon sun over South Africa."""

from __future__ import annotations

import vtk


def apply_lighting(renderer: vtk.vtkRenderer) -> None:
    """Apply key/fill/rim three-point lighting to the renderer.

    Simulates late-afternoon sun (northwest, warm) with cool fill and rim.
    """
    renderer.RemoveAllLights()

    # Key light: warm afternoon sun from northwest
    key = vtk.vtkLight()
    key.SetLightTypeToSceneLight()
    key.SetPosition(-1.0, -1.0, 0.8)
    key.SetFocalPoint(0.0, 0.0, 0.0)
    key.SetColor(1.0, 0.9, 0.7)
    key.SetIntensity(1.2)
    renderer.AddLight(key)

    # Fill light: cool ambient from opposite side
    fill = vtk.vtkLight()
    fill.SetLightTypeToSceneLight()
    fill.SetPosition(1.0, 0.5, 0.3)
    fill.SetFocalPoint(0.0, 0.0, 0.0)
    fill.SetColor(0.6, 0.7, 1.0)
    fill.SetIntensity(0.45)
    renderer.AddLight(fill)

    # Rim light: from behind and above
    rim = vtk.vtkLight()
    rim.SetLightTypeToSceneLight()
    rim.SetPosition(0.0, 1.0, 1.0)
    rim.SetFocalPoint(0.0, 0.0, 0.0)
    rim.SetColor(1.0, 0.95, 0.9)
    rim.SetIntensity(0.7)
    renderer.AddLight(rim)
