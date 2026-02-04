"""Tests for data pipeline orchestrator (ticket 2-5)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import AppConfig, load_config
from oco_viz.data.pipeline import (
    attach_oco3_overlay,
    build_wind_driven_plume,
    run_data_pipeline,
)
from oco_viz.data.zarr_store import read_zarr

_FIXTURES = Path(__file__).parent / "fixtures"
_ERA5_PATH = _FIXTURES / "era5_secunda_2025-10-13.nc"
_OCO3_PATH = _FIXTURES / "oco3_secunda_2025-10-26.nc4"

_has_era5 = _ERA5_PATH.exists()
_has_oco3 = _OCO3_PATH.exists()


@pytest.fixture
def config() -> AppConfig:
    return load_config(
        overrides={
            "grid": {"nx": 10, "ny": 10, "nz": 5, "dx": 1000.0, "dy": 1000.0, "dz": 500.0},
        }
    )


# --- build_wind_driven_plume ---


@pytest.mark.skipif(not _has_era5, reason="ERA5 fixture not found")
def test_build_wind_driven_plume_returns_dataset(config: AppConfig) -> None:
    ds = build_wind_driven_plume(config, _ERA5_PATH, num_timesteps=3)
    assert isinstance(ds, xr.Dataset)


@pytest.mark.skipif(not _has_era5, reason="ERA5 fixture not found")
def test_build_wind_driven_plume_has_concentration(config: AppConfig) -> None:
    ds = build_wind_driven_plume(config, _ERA5_PATH, num_timesteps=3)
    assert "concentration" in ds
    assert set(ds["concentration"].dims) == {"time", "z", "y", "x"}


@pytest.mark.skipif(not _has_era5, reason="ERA5 fixture not found")
def test_build_wind_driven_plume_has_wind_vars(config: AppConfig) -> None:
    ds = build_wind_driven_plume(config, _ERA5_PATH, num_timesteps=3)
    assert "u_wind" in ds
    assert "v_wind" in ds


@pytest.mark.skipif(not _has_era5, reason="ERA5 fixture not found")
def test_build_wind_driven_plume_shape(config: AppConfig) -> None:
    ds = build_wind_driven_plume(config, _ERA5_PATH, num_timesteps=3)
    assert ds["concentration"].shape[0] == 3
    assert ds["concentration"].shape[1] == config.grid.nz
    assert ds["concentration"].shape[2] == config.grid.ny
    assert ds["concentration"].shape[3] == config.grid.nx


# --- attach_oco3_overlay ---


@pytest.mark.skipif(not _has_oco3, reason="OCO-3 fixture not found")
def test_attach_oco3_overlay(config: AppConfig) -> None:
    # Create a minimal 4D dataset
    ds = xr.Dataset(
        {
            "concentration": (
                ["time", "z", "y", "x"],
                np.zeros((2, config.grid.nz, config.grid.ny, config.grid.nx), dtype=np.float32),
            ),
        },
    )
    result = attach_oco3_overlay(ds, [_OCO3_PATH], config.data_source.domain, config.grid)
    assert "xco2_observed" in result


# --- run_data_pipeline (fallback) ---


def test_run_data_pipeline_fallback(config: AppConfig, tmp_path: Path) -> None:
    """Without ERA5 path, should fall back to Gaussian plume."""
    ds = run_data_pipeline(config, num_timesteps=3, output_zarr=tmp_path / "out.zarr")
    assert isinstance(ds, xr.Dataset)
    assert "concentration" in ds
    assert ds["concentration"].shape[0] == 3


def test_run_data_pipeline_writes_zarr(config: AppConfig, tmp_path: Path) -> None:
    zarr_path = tmp_path / "out.zarr"
    run_data_pipeline(config, num_timesteps=3, output_zarr=zarr_path)
    assert zarr_path.exists()
    # Verify readable
    ds = read_zarr(zarr_path)
    assert "concentration" in ds


@pytest.mark.skipif(not _has_era5, reason="ERA5 fixture not found")
def test_run_data_pipeline_with_era5(config: AppConfig, tmp_path: Path) -> None:
    ds = run_data_pipeline(
        config,
        era5_path=_ERA5_PATH,
        num_timesteps=3,
        output_zarr=tmp_path / "out.zarr",
    )
    assert "concentration" in ds
    assert "u_wind" in ds
    assert "v_wind" in ds
