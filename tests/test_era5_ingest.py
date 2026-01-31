"""Tests for ERA5 3D wind field ingest (ticket 2-3)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import DomainConfig, ERA5Config, GridConfig
from oco_viz.data.era5 import build_era5_request_for_domain, load_era5_winds

_FIXTURES = Path(__file__).parent / "fixtures"
_ERA5_PATH = _FIXTURES / "era5_secunda_sample.nc"

pytestmark = pytest.mark.skipif(
    not _ERA5_PATH.exists(),
    reason="ERA5 fixture not found — run tests/create_test_fixtures.py",
)


@pytest.fixture
def domain() -> DomainConfig:
    return DomainConfig()


@pytest.fixture
def grid() -> GridConfig:
    return GridConfig(nx=10, ny=10, nz=5, dx=1000.0, dy=1000.0, dz=500.0)


def test_load_era5_winds_returns_dataset(domain, grid):
    ds = load_era5_winds(_ERA5_PATH, domain, grid)
    assert isinstance(ds, xr.Dataset)


def test_load_era5_winds_has_wind_vars(domain, grid):
    ds = load_era5_winds(_ERA5_PATH, domain, grid)
    assert "u_wind" in ds
    assert "v_wind" in ds


def test_load_era5_winds_shape(domain, grid):
    ds = load_era5_winds(_ERA5_PATH, domain, grid)
    # Should have (time, z, y, x) dimensions
    assert set(ds["u_wind"].dims) == {"time", "z", "y", "x"}
    assert ds["u_wind"].shape[1] == grid.nz
    assert ds["u_wind"].shape[2] == grid.ny
    assert ds["u_wind"].shape[3] == grid.nx


def test_load_era5_winds_dtype(domain, grid):
    ds = load_era5_winds(_ERA5_PATH, domain, grid)
    assert ds["u_wind"].dtype == np.float32
    assert ds["v_wind"].dtype == np.float32


def test_load_era5_winds_physically_reasonable(domain, grid):
    ds = load_era5_winds(_ERA5_PATH, domain, grid)
    u = ds["u_wind"].values
    v = ds["v_wind"].values
    speed = np.sqrt(u**2 + v**2)
    # Wind speeds should be in 0-50 m/s range
    assert np.nanmax(speed) < 50.0
    assert np.nanmin(speed) >= 0.0


def test_build_era5_request_for_domain():
    domain = DomainConfig()
    era5_cfg = ERA5Config()
    req = build_era5_request_for_domain(domain, era5_cfg, "2024-01-15")
    assert req["year"] == "2024"
    assert req["month"] == "01"
    # Bounding box should cover domain extent
    area = req["area"]
    assert len(area) == 4  # [N, W, S, E]
