"""Integration tests for real-data pipeline (ERA5 winds + OCO-2/3 overlay).

All tests are fixture-guarded: they skip when the required NetCDF fixtures
are not present on disk (CI runs without large satellite data files).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import AppConfig, GridConfig
from oco_viz.data.era5 import load_era5_winds
from oco_viz.data.pipeline import attach_satellite_overlay, run_data_pipeline
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_sequence

FIXTURES_DIR = Path("tests/fixtures")
ERA5_OCT13 = FIXTURES_DIR / "era5_secunda_2025-10-13.nc"
OCO2_FIXTURE = FIXTURES_DIR / "oco2_secunda_2025-10-13.nc4"
OCO3_FIXTURE = FIXTURES_DIR / "oco3_secunda_2025-10-26.nc4"


def _small_config() -> AppConfig:
    """Build a minimal config for fast integration tests."""
    return AppConfig(
        grid=GridConfig(nx=16, ny=16, nz=8, dx=1000.0, dy=1000.0, dz=500.0),
    )


# ── ERA5 wind loading ─────────────────────────────────────────────


@pytest.mark.skipif(not ERA5_OCT13.exists(), reason="ERA5 Oct 13 fixture not present")
def test_load_era5_oct13_returns_valid_wind() -> None:
    """ERA5 loader returns a Dataset with u_wind and v_wind on (time, z, y, x)."""
    config = _small_config()
    ds = load_era5_winds(ERA5_OCT13, config.data_source.domain, config.grid)

    assert isinstance(ds, xr.Dataset)
    assert "u_wind" in ds
    assert "v_wind" in ds
    assert ds["u_wind"].dims == ("time", "z", "y", "x")
    # Wind speed should be finite and non-trivial
    speed = np.sqrt(ds["u_wind"].values ** 2 + ds["v_wind"].values ** 2)
    assert np.all(np.isfinite(speed))
    assert float(np.max(speed)) > 0.01, "Wind field is all zeros"


# ── Advection with real ERA5 ──────────────────────────────────────


@pytest.mark.skipif(not ERA5_OCT13.exists(), reason="ERA5 Oct 13 fixture not present")
def test_advect_with_real_era5_winds() -> None:
    """Semi-Lagrangian advection produces non-trivial output with real ERA5 winds."""
    config = _small_config()
    grid = config.grid
    domain = config.data_source.domain
    wind_ds = load_era5_winds(ERA5_OCT13, domain, grid)

    ds = advect_sequence(
        config.plume,
        grid,
        wind_ds,
        config.turbulence,
        n_steps=3,
        adv_cfg=config.advection,
    )

    assert "concentration" in ds
    assert ds["concentration"].dims == ("time", "z", "y", "x")
    # At least the initial frame should have non-zero values
    assert float(ds["concentration"].isel(time=0).max()) > 0


# ── Satellite overlay ─────────────────────────────────────────────


@pytest.mark.skipif(not OCO2_FIXTURE.exists(), reason="OCO-2 fixture not present")
def test_attach_satellite_overlay_oco2() -> None:
    """Attaching OCO-2 overlay adds xco2_observed to the dataset."""
    config = _small_config()
    ds = generate_sequence(config.plume, config.grid, num_timesteps=2)
    ds = attach_satellite_overlay(
        ds,
        [OCO2_FIXTURE],
        config.data_source.domain,
        config.grid,
    )

    assert "xco2_observed" in ds


@pytest.mark.skipif(not OCO3_FIXTURE.exists(), reason="OCO-3 fixture not present")
def test_attach_satellite_overlay_oco3() -> None:
    """Attaching OCO-3 overlay adds xco2_observed to the dataset."""
    config = _small_config()
    ds = generate_sequence(config.plume, config.grid, num_timesteps=2)
    ds = attach_satellite_overlay(
        ds,
        [OCO3_FIXTURE],
        config.data_source.domain,
        config.grid,
    )

    assert "xco2_observed" in ds


# ── Full pipeline ─────────────────────────────────────────────────


@pytest.mark.skipif(
    not (ERA5_OCT13.exists() and OCO2_FIXTURE.exists()),
    reason="ERA5 + OCO-2 fixtures not present",
)
def test_full_pipeline_oct13() -> None:
    """ERA5 advection + OCO-2 overlay produces a renderable dataset."""
    config = _small_config()
    ds = run_data_pipeline(
        config,
        mode="advected",
        era5_path=ERA5_OCT13,
        oco3_paths=[OCO2_FIXTURE],
        num_timesteps=3,
    )

    assert "concentration" in ds
    assert "xco2_observed" in ds
    assert ds["concentration"].dims == ("time", "z", "y", "x")
    # Verify the concentration is non-trivial
    assert float(ds["concentration"].max()) > 0
