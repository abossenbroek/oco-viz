"""Tests for OCO-3 spatial XCO2 loader (ticket 2-4)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import DomainConfig, GridConfig
from oco_viz.data.oco3 import load_and_grid_granules, load_granule

_FIXTURES = Path(__file__).parent / "fixtures"
_OCO3_PATH = _FIXTURES / "oco3_secunda_2025-10-26.nc4"

pytestmark = pytest.mark.skipif(
    not _OCO3_PATH.exists(),
    reason="OCO-3 fixture not found — run scripts/download_fixtures.py",
)


@pytest.fixture
def domain() -> DomainConfig:
    return DomainConfig()


@pytest.fixture
def grid() -> GridConfig:
    return GridConfig(nx=10, ny=10, nz=5, dx=1000.0, dy=1000.0, dz=500.0)


def test_load_granule_returns_dataset() -> None:
    ds = load_granule(_OCO3_PATH)
    assert isinstance(ds, xr.Dataset)


def test_load_granule_has_required_vars() -> None:
    ds = load_granule(_OCO3_PATH)
    assert "xco2" in ds
    assert "latitude" in ds
    assert "longitude" in ds


def test_load_granule_sounding_dim() -> None:
    ds = load_granule(_OCO3_PATH)
    assert "sounding_id" in ds.dims


def test_load_granule_quality_filtering() -> None:
    ds_all = load_granule(_OCO3_PATH, quality_threshold=None)
    ds_filtered = load_granule(_OCO3_PATH, quality_threshold=0)
    # Filtered should have fewer soundings
    assert ds_filtered.sizes["sounding_id"] <= ds_all.sizes["sounding_id"]


def test_load_and_grid_granules_shape(domain: DomainConfig, grid: GridConfig) -> None:
    ds = load_and_grid_granules([_OCO3_PATH], domain, grid)
    assert isinstance(ds, xr.Dataset)
    assert "xco2_observed" in ds
    assert ds["xco2_observed"].shape == (grid.ny, grid.nx)


# ---------------------------------------------------------------------------
# Secunda fixture tests (oco3_secunda_2025-10-26.nc4)
# ---------------------------------------------------------------------------


@pytest.fixture
def secunda_domain() -> DomainConfig:
    """Domain shifted SW so the good-quality OCO-3 soundings land in the grid.

    The 3 good-quality soundings in oco3_secunda_2025-10-26.nc4 are at
    ~(-80 km, +88 km) relative to Secunda center (-26.52, 29.17).
    Shifting the origin SW captures them in the positive quadrant.
    """
    return DomainConfig(
        origin_lat=-27.5,
        origin_lon=28.2,
        extent_x_km=200.0,
        extent_y_km=200.0,
    )


@pytest.fixture
def secunda_grid() -> GridConfig:
    """Grid covering 200 km with 2 km cells."""
    return GridConfig(nx=100, ny=100, nz=5, dx=2000.0, dy=2000.0, dz=500.0)


def test_secunda_load_granule_returns_dataset() -> None:
    ds = load_granule(_OCO3_PATH)
    assert isinstance(ds, xr.Dataset)


def test_secunda_load_and_grid_has_valid_values(
    secunda_domain: DomainConfig, secunda_grid: GridConfig
) -> None:
    """OCO-3 Secunda fixture should produce non-NaN gridded XCO2."""
    ds = load_and_grid_granules([_OCO3_PATH], secunda_domain, secunda_grid)
    xco2 = ds["xco2_observed"].values
    valid = xco2[~np.isnan(xco2)]
    assert len(valid) > 0, "Expected valid gridded XCO2 values over Secunda"


def test_secunda_load_and_grid_physical_range(
    secunda_domain: DomainConfig, secunda_grid: GridConfig
) -> None:
    """Gridded XCO2 values should be in a physically reasonable range."""
    ds = load_and_grid_granules([_OCO3_PATH], secunda_domain, secunda_grid)
    xco2 = ds["xco2_observed"].values
    valid = xco2[~np.isnan(xco2)]
    assert len(valid) > 0, "Need valid values to check physical range"
    assert np.min(valid) > 380
    assert np.max(valid) < 500
