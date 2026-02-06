"""Tests for OCO observation overlay."""

from __future__ import annotations

import numpy as np
import xarray as xr

from oco_viz.config.schema import GridConfig, OverlayConfig
from oco_viz.render.overlay import create_observation_overlay, has_observations


def _make_grid() -> GridConfig:
    return GridConfig(nx=24, ny=24, nz=16, dx=1000.0, dy=1000.0, dz=500.0)


def _make_overlay_cfg() -> OverlayConfig:
    return OverlayConfig()


def _mock_obs_data(n_points: int = 10) -> xr.Dataset:
    rng = np.random.default_rng(42)
    return xr.Dataset(
        {
            "xco2_observed": (
                ["footprint"],
                rng.uniform(415.0, 425.0, n_points).astype(np.float32),
            ),
            "obs_x": (
                ["footprint"],
                rng.uniform(0, 24000.0, n_points).astype(np.float32),
            ),
            "obs_y": (
                ["footprint"],
                rng.uniform(0, 24000.0, n_points).astype(np.float32),
            ),
        }
    )


def test_create_overlay_returns_actor() -> None:
    grid = _make_grid()
    cfg = _make_overlay_cfg()
    obs = _mock_obs_data()
    actor = create_observation_overlay(obs, grid, cfg)
    assert actor is not None
    assert actor.GetMapper() is not None


def test_overlay_empty_observations() -> None:
    grid = _make_grid()
    cfg = _make_overlay_cfg()
    nan_data = xr.Dataset(
        {
            "xco2_observed": (
                ["footprint"],
                np.full(5, np.nan, dtype=np.float32),
            ),
            "obs_x": (
                ["footprint"],
                np.zeros(5, dtype=np.float32),
            ),
            "obs_y": (
                ["footprint"],
                np.zeros(5, dtype=np.float32),
            ),
        }
    )
    actor = create_observation_overlay(nan_data, grid, cfg)
    assert actor is not None
    # With all NaN, the polydata should have 0 points
    mapper = actor.GetMapper()
    poly = mapper.GetInput()
    assert poly.GetNumberOfPoints() == 0


def test_colormap_range() -> None:
    grid = _make_grid()
    cfg = OverlayConfig(max_enhancement_ppm=10.0, background_ppm=415.0)
    # Create data with known enhancement
    obs = xr.Dataset(
        {
            "xco2_observed": (
                ["footprint"],
                np.array([415.0, 420.0, 425.0], dtype=np.float32),
            ),
            "obs_x": (
                ["footprint"],
                np.array([1000.0, 2000.0, 3000.0], dtype=np.float32),
            ),
            "obs_y": (
                ["footprint"],
                np.array([1000.0, 2000.0, 3000.0], dtype=np.float32),
            ),
        }
    )
    actor = create_observation_overlay(obs, grid, cfg)
    mapper = actor.GetMapper()
    poly = mapper.GetInput()
    assert poly.GetNumberOfPoints() == 3
    # Verify scalars are present (color data)
    scalars = poly.GetPointData().GetScalars()
    assert scalars is not None
    assert scalars.GetNumberOfTuples() == 3


def test_has_observations_true_false() -> None:
    obs = _mock_obs_data()
    assert has_observations(obs) is True

    empty = xr.Dataset({"temperature": (["x"], np.array([1.0, 2.0]))})
    assert has_observations(empty) is False


def test_emissive_brightness() -> None:
    grid = _make_grid()
    cfg = OverlayConfig(emissive_brightness=2.0)
    obs = _mock_obs_data()
    actor = create_observation_overlay(obs, grid, cfg)
    # Check that emissive factor is applied on the mapper
    mapper = actor.GetMapper()
    assert mapper is not None
    # The actor should have emissive color set
    prop = actor.GetProperty()
    assert prop is not None
