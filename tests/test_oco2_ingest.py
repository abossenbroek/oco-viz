"""Tests for OCO-2 spatial XCO2 loader."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import DomainConfig, GridConfig
from oco_viz.data.oco import load_and_grid_granules, load_granule

_FIXTURES = Path(__file__).parent / "fixtures"
_OCO2_PATH = _FIXTURES / "oco2_secunda_2025-10-13.nc4"

pytestmark = pytest.mark.skipif(
    not _OCO2_PATH.exists(),
    reason="OCO-2 Secunda fixture not found — run scripts/find_secunda_granule.py",
)


@pytest.fixture
def secunda_domain() -> DomainConfig:
    """Domain centered on Secunda (default DomainConfig)."""
    return DomainConfig()


@pytest.fixture
def grid() -> GridConfig:
    """Coarse grid covering the Secunda domain."""
    return GridConfig(nx=100, ny=100, nz=5, dx=1000.0, dy=1000.0, dz=500.0)


def test_load_granule_returns_dataset() -> None:
    ds = load_granule(_OCO2_PATH)
    assert isinstance(ds, xr.Dataset)


def test_load_granule_has_required_vars() -> None:
    ds = load_granule(_OCO2_PATH)
    assert "xco2" in ds
    assert "latitude" in ds
    assert "longitude" in ds


def test_load_granule_sounding_dim() -> None:
    ds = load_granule(_OCO2_PATH)
    assert "sounding_id" in ds.dims


def test_load_granule_quality_filtering() -> None:
    ds_all = load_granule(_OCO2_PATH, quality_threshold=None)
    ds_filtered = load_granule(_OCO2_PATH, quality_threshold=0)
    assert ds_filtered.sizes["sounding_id"] <= ds_all.sizes["sounding_id"]


def test_load_and_grid_secunda_has_valid_values(
    secunda_domain: DomainConfig, grid: GridConfig
) -> None:
    """OCO-2 Secunda fixture should produce non-NaN gridded XCO2."""
    ds = load_and_grid_granules([_OCO2_PATH], secunda_domain, grid)
    xco2 = ds["xco2_observed"].values
    valid = xco2[~np.isnan(xco2)]
    assert len(valid) > 0, "Expected valid gridded XCO2 values over Secunda"


def test_load_and_grid_secunda_physical_range(
    secunda_domain: DomainConfig, grid: GridConfig
) -> None:
    """Gridded XCO2 values should be in a physically reasonable range."""
    ds = load_and_grid_granules([_OCO2_PATH], secunda_domain, grid)
    xco2 = ds["xco2_observed"].values
    valid = xco2[~np.isnan(xco2)]
    assert len(valid) > 0, "Need valid values to check physical range"
    assert np.min(valid) > 380
    assert np.max(valid) < 500
