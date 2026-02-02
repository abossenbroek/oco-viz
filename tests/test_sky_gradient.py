"""Tests for sky gradient background."""

from __future__ import annotations

import vtk

from oco_viz.config.schema import SkyConfig
from oco_viz.render.sky_gradient import apply_sky_gradient


def test_apply_sky_gradient_sets_colors() -> None:
    renderer = vtk.vtkRenderer()
    config = SkyConfig()
    apply_sky_gradient(renderer, config)

    bg = renderer.GetBackground()
    bg2 = renderer.GetBackground2()
    assert bg == config.bottom_color
    assert bg2 == config.top_color
    assert renderer.GetGradientBackground() is True


def test_apply_sky_gradient_disabled() -> None:
    renderer = vtk.vtkRenderer()
    original_bg = renderer.GetBackground()
    config = SkyConfig(enabled=False)
    apply_sky_gradient(renderer, config)

    # Background should be unchanged
    assert renderer.GetBackground() == original_bg
    assert renderer.GetGradientBackground() is False


def test_apply_sky_gradient_custom_colors() -> None:
    renderer = vtk.vtkRenderer()
    config = SkyConfig(top_color=(0.5, 0.5, 0.5), bottom_color=(0.2, 0.2, 0.2))
    apply_sky_gradient(renderer, config)

    assert renderer.GetBackground() == (0.2, 0.2, 0.2)
    assert renderer.GetBackground2() == (0.5, 0.5, 0.5)


def test_sky_config_defaults() -> None:
    config = SkyConfig()
    assert config.enabled is True
    assert config.top_color == (0.01, 0.01, 0.04)
    assert config.bottom_color == (0.08, 0.08, 0.12)
