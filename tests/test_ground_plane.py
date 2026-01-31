"""Tests for ground plane grid actor."""

from __future__ import annotations

from oco_viz.config.schema import GridConfig, GroundPlaneConfig
from oco_viz.render.ground_plane import create_ground_plane


def test_create_ground_plane_returns_actor():
    config = GroundPlaneConfig()
    grid = GridConfig()
    actor = create_ground_plane(config, grid)
    assert actor is not None
    assert actor.GetMapper() is not None


def test_ground_plane_opacity():
    config = GroundPlaneConfig(opacity=0.15)
    grid = GridConfig()
    actor = create_ground_plane(config, grid)
    assert abs(actor.GetProperty().GetOpacity() - 0.15) < 1e-6


def test_ground_plane_color():
    config = GroundPlaneConfig(color=(0.5, 0.5, 0.5))
    grid = GridConfig()
    actor = create_ground_plane(config, grid)
    assert actor.GetProperty().GetColor() == (0.5, 0.5, 0.5)


def test_ground_plane_config_defaults():
    config = GroundPlaneConfig()
    assert config.enabled is True
    assert abs(config.opacity - 0.08) < 1e-6
    assert abs(config.grid_spacing_km - 10.0) < 1e-6
    assert config.color == (0.3, 0.3, 0.3)
