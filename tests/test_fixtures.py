"""Smoke-tests verifying real test fixtures have expected structure."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

_FIXTURES = Path(__file__).parent / "fixtures"
_ERA5_PATH = _FIXTURES / "era5_secunda_2025-10-13.nc"
_OCO3_PATH = _FIXTURES / "oco3_secunda_2025-10-26.nc4"

# ---------------------------------------------------------------------------
# ERA5 fixture
# ---------------------------------------------------------------------------

_skip_era5 = pytest.mark.skipif(
    not _ERA5_PATH.exists(),
    reason="ERA5 fixture not found — run scripts/download_fixtures.py",
)


@_skip_era5
def test_era5_fixture_has_expected_dims() -> None:
    ds = xr.open_dataset(str(_ERA5_PATH))
    # ERA5 uses 'valid_time' (newer CDS) or 'time' (older CDS)
    assert "valid_time" in ds.dims or "time" in ds.dims
    assert "pressure_level" in ds.dims
    assert "latitude" in ds.dims
    assert "longitude" in ds.dims
    ds.close()


@_skip_era5
def test_era5_fixture_has_wind_vars() -> None:
    ds = xr.open_dataset(str(_ERA5_PATH))
    assert "u" in ds.data_vars
    assert "v" in ds.data_vars
    assert ds["u"].dtype == np.float32
    assert ds["v"].dtype == np.float32
    ds.close()


@_skip_era5
def test_era5_fixture_has_expected_shape() -> None:
    ds = xr.open_dataset(str(_ERA5_PATH))
    time_dim = "valid_time" if "valid_time" in ds.dims else "time"
    assert ds.sizes[time_dim] == 24
    assert ds.sizes["pressure_level"] == 10
    assert ds.sizes["latitude"] >= 4
    assert ds.sizes["longitude"] >= 4
    ds.close()


# ---------------------------------------------------------------------------
# OCO-3 fixture
# ---------------------------------------------------------------------------

_skip_oco3 = pytest.mark.skipif(
    not _OCO3_PATH.exists(),
    reason="OCO-3 fixture not found — run scripts/download_fixtures.py",
)


@_skip_oco3
def test_oco3_fixture_has_expected_dims() -> None:
    ds = xr.open_dataset(str(_OCO3_PATH))
    assert "sounding_id" in ds.dims
    assert ds.sizes["sounding_id"] > 1000
    ds.close()


@_skip_oco3
def test_oco3_fixture_has_required_vars() -> None:
    ds = xr.open_dataset(str(_OCO3_PATH))
    for var in ("xco2", "latitude", "longitude", "xco2_quality_flag"):
        assert var in ds, f"Missing required variable: {var}"
    ds.close()


@_skip_oco3
def test_oco3_fixture_xco2_physical_range() -> None:
    ds = xr.open_dataset(str(_OCO3_PATH))
    xco2 = ds["xco2"].values
    valid = xco2[~np.isnan(xco2)]
    assert len(valid) > 0, "No valid XCO2 values"
    assert np.all(valid >= 350), f"XCO2 below 350 ppm: min={valid.min()}"
    assert np.all(valid <= 500), f"XCO2 above 500 ppm: max={valid.max()}"
    ds.close()


@_skip_oco3
def test_oco3_fixture_quality_flag_values() -> None:
    ds = xr.open_dataset(str(_OCO3_PATH))
    qf = ds["xco2_quality_flag"].values
    valid = qf[~np.isnan(qf)]
    unique = set(np.unique(valid).astype(int))
    assert unique <= {0, 1}, f"Unexpected quality flag values: {unique}"
    ds.close()
