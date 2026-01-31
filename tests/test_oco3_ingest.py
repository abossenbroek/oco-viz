"""Tests for OCO-3 spatial XCO2 loader (ticket 2-4)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import DomainConfig, GridConfig
from oco_viz.data.oco3 import load_and_grid_granules, load_granule

_FIXTURES = Path(__file__).parent / "fixtures"
_OCO3_PATH = _FIXTURES / "oco3_sample.nc4"

pytestmark = pytest.mark.skipif(
    not _OCO3_PATH.exists(),
    reason="OCO-3 fixture not found — run tests/create_test_fixtures.py",
)


@pytest.fixture
def domain() -> DomainConfig:
    return DomainConfig()


@pytest.fixture
def grid() -> GridConfig:
    return GridConfig(nx=10, ny=10, nz=5, dx=1000.0, dy=1000.0, dz=500.0)


def test_load_granule_returns_dataset():
    ds = load_granule(_OCO3_PATH)
    assert isinstance(ds, xr.Dataset)


def test_load_granule_has_required_vars():
    ds = load_granule(_OCO3_PATH)
    assert "xco2" in ds
    assert "latitude" in ds
    assert "longitude" in ds


def test_load_granule_sounding_dim():
    ds = load_granule(_OCO3_PATH)
    assert "sounding_id" in ds.dims


def test_load_granule_quality_filtering():
    ds_all = load_granule(_OCO3_PATH, quality_threshold=None)
    ds_filtered = load_granule(_OCO3_PATH, quality_threshold=0)
    # Filtered should have fewer soundings
    assert ds_filtered.sizes["sounding_id"] <= ds_all.sizes["sounding_id"]


def test_load_and_grid_granules_shape(domain, grid):
    ds = load_and_grid_granules([_OCO3_PATH], domain, grid)
    assert isinstance(ds, xr.Dataset)
    assert "xco2_observed" in ds
    assert ds["xco2_observed"].shape == (grid.ny, grid.nx)


def test_load_and_grid_granules_physical_range(domain, grid):
    ds = load_and_grid_granules([_OCO3_PATH], domain, grid)
    xco2 = ds["xco2_observed"].values
    valid = xco2[~np.isnan(xco2)]
    if len(valid) > 0:
        # XCO2 should be in ~380-450 ppm range
        assert np.min(valid) > 380
        assert np.max(valid) < 450


def test_load_and_grid_granules_has_nan_cells(domain, grid):
    """Not all grid cells should have observations."""
    ds = load_and_grid_granules([_OCO3_PATH], domain, grid)
    xco2 = ds["xco2_observed"].values
    assert np.any(np.isnan(xco2))
