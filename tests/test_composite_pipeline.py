"""Tests for composite pipeline mode (CAMS background + plume + turbulence)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path
import pytest
import xarray as xr

from oco_viz.config.schema import AppConfig, load_config
from oco_viz.data.pipeline import build_composite_field, run_data_pipeline
from oco_viz.render.normalize import normalize_concentration


def _make_cams_fixture(tmp_path: Path, grid_cfg: AppConfig) -> Path:
    """Create a synthetic CAMS NetCDF matching the expected format."""
    n_lev, n_lat, n_lon = 10, 8, 8
    domain = grid_cfg.data_source.domain
    lats = np.linspace(domain.origin_lat - 0.5, domain.origin_lat + 0.5, n_lat)
    lons = np.linspace(domain.origin_lon - 0.5, domain.origin_lon + 0.5, n_lon)

    co2 = np.full((n_lev, n_lat, n_lon), 420.0, dtype=np.float64)
    temp = np.full((n_lev, n_lat, n_lon), 280.0, dtype=np.float64)

    ds = xr.Dataset(
        {
            "co2": (["level", "latitude", "longitude"], co2),
            "t": (["level", "latitude", "longitude"], temp),
        },
        coords={
            "level": np.arange(n_lev),
            "latitude": lats,
            "longitude": lons,
        },
    )
    path = tmp_path / "cams_composite.nc"
    ds.to_netcdf(str(path))
    return path


@pytest.fixture
def small_config() -> AppConfig:
    return load_config(overrides={"grid": {"nx": 16, "ny": 16, "nz": 10}})


def test_build_composite_field_shape(tmp_path: Path, small_config: AppConfig) -> None:
    """Composite field matches grid shape."""
    cams_path = _make_cams_fixture(tmp_path, small_config)
    ds = build_composite_field(small_config, cams_path, num_timesteps=2)
    grid = small_config.grid
    assert ds["concentration"].shape == (2, grid.nz, grid.ny, grid.nx)


def test_composite_exceeds_background(tmp_path: Path, small_config: AppConfig) -> None:
    """Composite field should be >= background everywhere (plume adds, never subtracts)."""
    cams_path = _make_cams_fixture(tmp_path, small_config)
    ds = build_composite_field(small_config, cams_path, num_timesteps=1)
    conc = ds["concentration"].values[0]
    # The minimum should be >= background level (420 ppm, though regridding may shift slightly)
    assert float(np.nanmin(conc)) >= 400.0


def test_composite_anomaly_range(tmp_path: Path, small_config: AppConfig) -> None:
    """In anomaly mode, enhancement should be in 0-N ppm range."""
    cams_path = _make_cams_fixture(tmp_path, small_config)
    ds = build_composite_field(small_config, cams_path, num_timesteps=1)
    conc = ds["concentration"].values[0]
    normalized = normalize_concentration(conc, small_config.rendering)
    assert float(np.nanmin(normalized)) >= 0.0
    assert float(np.nanmax(normalized)) <= 1.0


def test_run_data_pipeline_gaussian(small_config: AppConfig) -> None:
    """Backward compat: mode=gaussian still works."""
    ds = run_data_pipeline(small_config, mode="gaussian", num_timesteps=2)
    assert "concentration" in ds


def test_run_data_pipeline_turbulent(small_config: AppConfig) -> None:
    """Backward compat: mode=turbulent still works."""
    ds = run_data_pipeline(small_config, mode="turbulent", num_timesteps=2)
    assert "concentration" in ds


def test_run_data_pipeline_composite(tmp_path: Path, small_config: AppConfig) -> None:
    """Composite mode via run_data_pipeline."""
    cams_path = _make_cams_fixture(tmp_path, small_config)
    ds = run_data_pipeline(
        small_config,
        mode="composite",
        cams_path=cams_path,
        num_timesteps=2,
    )
    assert "concentration" in ds


def test_run_data_pipeline_composite_requires_cams(small_config: AppConfig) -> None:
    """mode=composite without cams_path raises ValueError."""
    with pytest.raises(ValueError, match="cams_path"):
        run_data_pipeline(small_config, mode="composite", num_timesteps=1)
