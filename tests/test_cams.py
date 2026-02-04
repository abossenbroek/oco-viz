"""Tests for CAMS high-res GHG forecast loader."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import DomainConfig, GridConfig
from oco_viz.data.cams import (
    _build_cams_request,
    _hybrid_sigma_to_altitude,
    _kgkg_to_ppm,
    download_cams_co2,
    load_cams_co2,
)


def _make_cams_fixture(tmp_path: Path, *, units: str = "kgkg") -> Path:
    """Create a synthetic CAMS NetCDF file for testing."""
    n_lev, n_lat, n_lon = 10, 8, 8
    lats = np.linspace(-27.0, -26.0, n_lat)
    lons = np.linspace(28.7, 29.7, n_lon)

    # Background ~420 ppm in kgkg: 420e-6 * M_co2 / M_air
    co2_val = 420e-6 * 44.01e-3 / 28.97e-3 if units == "kgkg" else 420.0

    co2 = np.full((n_lev, n_lat, n_lon), co2_val, dtype=np.float64)
    # Add a slight vertical gradient (decreasing above PBL)
    for k in range(n_lev):
        co2[k] *= 1.0 - 0.005 * k

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
    path = tmp_path / "cams_test.nc"
    ds.to_netcdf(str(path))
    return path


@pytest.fixture
def domain() -> DomainConfig:
    return DomainConfig(
        origin_lat=-26.52,
        origin_lon=29.17,
        extent_x_km=100.0,
        extent_y_km=100.0,
        extent_z_km=15.0,
    )


@pytest.fixture
def small_grid() -> GridConfig:
    return GridConfig(nx=10, ny=10, nz=8, dx=1000.0, dy=1000.0, dz=500.0)


def test_kgkg_to_ppm() -> None:
    """CO2 mass mixing ratio -> ppm conversion."""
    # ~420 ppm in kg/kg
    kgkg = 420e-6 * 44.01e-3 / 28.97e-3
    ppm = _kgkg_to_ppm(np.array([kgkg]))
    assert 415.0 < ppm[0] < 425.0


def test_hybrid_sigma_to_altitude() -> None:
    """Altitude profile should be monotonically increasing."""
    temp = np.full((10, 5, 5), 270.0, dtype=np.float64)
    altitudes = _hybrid_sigma_to_altitude(temp, 10)
    assert altitudes[0] == 0.0
    assert np.all(np.diff(altitudes) > 0)


def test_load_cams_co2_shape(
    tmp_path: Path,
    domain: DomainConfig,
    small_grid: GridConfig,
) -> None:
    """Loaded array matches target grid shape."""
    fixture = _make_cams_fixture(tmp_path)
    result = load_cams_co2(fixture, domain, small_grid)
    assert result.shape == (small_grid.nz, small_grid.ny, small_grid.nx)
    assert result.dtype == np.float32


def test_load_cams_co2_ppm_range(
    tmp_path: Path,
    domain: DomainConfig,
    small_grid: GridConfig,
) -> None:
    """CO2 concentration should be in a plausible ppm range."""
    fixture = _make_cams_fixture(tmp_path)
    result = load_cams_co2(fixture, domain, small_grid)
    assert float(np.nanmin(result)) > 390.0
    assert float(np.nanmax(result)) < 460.0


def test_load_cams_co2_ppm_direct(
    tmp_path: Path,
    domain: DomainConfig,
    small_grid: GridConfig,
) -> None:
    """File already in ppm units should not be double-converted."""
    fixture = _make_cams_fixture(tmp_path, units="ppm")
    result = load_cams_co2(fixture, domain, small_grid)
    assert float(np.nanmin(result)) > 390.0
    assert float(np.nanmax(result)) < 460.0


def test_load_cams_co2_vertical_profile(
    tmp_path: Path,
    domain: DomainConfig,
    small_grid: GridConfig,
) -> None:
    """Vertical profile should show decreasing CO2 above boundary layer."""
    fixture = _make_cams_fixture(tmp_path)
    result = load_cams_co2(fixture, domain, small_grid)
    # Column mean at surface vs top
    surface_mean = float(np.nanmean(result[0, :, :]))
    top_mean = float(np.nanmean(result[-1, :, :]))
    assert surface_mean > top_mean


def test_build_cams_request(domain: DomainConfig) -> None:
    """Request dict has required keys."""
    req = _build_cams_request("2024-01-15", domain)
    assert req["date"] == "2024-01-15"
    assert "area" in req
    assert len(req["area"]) == 4


def test_download_cams_co2_mock(
    tmp_path: Path,
    domain: DomainConfig,
) -> None:
    """download_cams_co2 calls cdsapi.Client().retrieve and unzips result."""
    mock_cdsapi = MagicMock()
    mock_client = MagicMock()
    mock_cdsapi.Client.return_value = mock_client

    def _fake_retrieve(_dataset: str, _request: dict[str, object], dest_path: str) -> None:
        with zipfile.ZipFile(dest_path, "w") as zf:
            zf.writestr("data.nc", b"fake-netcdf-content")

    mock_client.retrieve.side_effect = _fake_retrieve

    with patch.dict("sys.modules", {"cdsapi": mock_cdsapi}):
        dest = download_cams_co2("2024-01-15", domain, tmp_path / "cache")
        mock_client.retrieve.assert_called_once()
        assert str(dest).endswith(".nc")
        assert dest.exists()


def test_load_missing_co2_variable(
    tmp_path: Path,
    domain: DomainConfig,
    small_grid: GridConfig,
) -> None:
    """Raise KeyError when no CO2 variable found."""
    ds = xr.Dataset(
        {"dummy": (["level", "latitude", "longitude"], np.zeros((5, 4, 4)))},
        coords={
            "level": np.arange(5),
            "latitude": np.linspace(-27, -26, 4),
            "longitude": np.linspace(28.7, 29.7, 4),
        },
    )
    path = tmp_path / "no_co2.nc"
    ds.to_netcdf(str(path))
    with pytest.raises(KeyError, match="No CO2 variable"):
        load_cams_co2(path, domain, small_grid)


def _make_cams_fixture_with_gradient(tmp_path: Path) -> Path:
    """Create CAMS fixture with spatial gradient to test interpolation coverage."""
    n_lev, n_lat, n_lon = 10, 8, 8
    lats = np.linspace(-27.0, -26.0, n_lat)
    lons = np.linspace(28.7, 29.7, n_lon)

    co2 = np.full((n_lev, n_lat, n_lon), 420.0, dtype=np.float64)
    # Add spatial gradient (lat/lon dependent) to detect fill artifacts
    for j in range(n_lat):
        for i in range(n_lon):
            co2[:, j, i] += 0.5 * j + 0.3 * i

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
    path = tmp_path / "cams_gradient_test.nc"
    ds.to_netcdf(str(path))
    return path


def test_cams_no_rectangular_artifacts(
    tmp_path: Path,
    domain: DomainConfig,
) -> None:
    """CAMS regridding produces smooth field without rectangular gaps.

    Regression test for coordinate transform bug that caused fill_value artifacts.
    The bug used misaligned 1D coordinate slices, causing RegularGridInterpolator
    to fill large regions with the mean value instead of interpolating.
    """
    # Use gallery-sized grid to expose any regrid artifacts
    gallery_grid = GridConfig(nx=48, ny=48, nz=32, dx=1000.0, dy=1000.0, dz=500.0)
    fixture = _make_cams_fixture_with_gradient(tmp_path)
    result = load_cams_co2(fixture, domain, gallery_grid)

    # Check no large uniform rectangular regions (artifact signature).
    # A healthy interpolation should produce varied values across the grid.
    center_slice = result[result.shape[0] // 2, :, :]
    unique_values = len(np.unique(center_slice.round(1)))
    assert unique_values > 10, "Too few unique values suggests fill_value artifact"


def test_cams_no_edge_discontinuities(
    tmp_path: Path,
    domain: DomainConfig,
) -> None:
    """Interpolation should produce smooth gradients (no step functions).

    This test verifies the second derivative (rate of gradient change) is smooth,
    detecting step discontinuities from interpolation artifacts.

    Note: Edge feathering has been moved to the normalization stage to avoid
    corrupting background profile estimation for anomaly mode rendering.
    """
    gallery_grid = GridConfig(nx=48, ny=48, nz=32, dx=1000.0, dy=1000.0, dz=500.0)
    fixture = _make_cams_fixture_with_gradient(tmp_path)
    result = load_cams_co2(fixture, domain, gallery_grid)

    # Check for step discontinuities via second derivative (Laplacian-like)
    # A smooth interpolation has bounded second derivatives; step functions have spikes
    mid_z = result.shape[0] // 2
    slice_2d = result[mid_z, :, :]

    # Compute second derivative along each axis
    d2y = np.diff(slice_2d, n=2, axis=0)
    d2x = np.diff(slice_2d, n=2, axis=1)

    # Second derivatives should be bounded (no spike from step discontinuity)
    max_d2 = max(np.max(np.abs(d2y)), np.max(np.abs(d2x)))
    data_range = float(np.max(slice_2d) - np.min(slice_2d))

    # Second derivative magnitude shouldn't exceed data range (step would be ~data_range)
    assert max_d2 < data_range, f"Step discontinuity detected: max d2={max_d2}, range={data_range}"


def test_cams_no_fill_artifacts(
    tmp_path: Path,
    domain: DomainConfig,
) -> None:
    """NaN fill should produce valid output without artifacts.

    Verifies:
    1. No NaN or inf values remain in output
    2. No single value dominates (fill artifact signature)
    3. Values are positive (physically valid CO2 concentrations)

    Note: Edge feathering has been moved to the normalization stage.
    Raw CAMS values should remain in physically plausible ppm range.
    """
    gallery_grid = GridConfig(nx=48, ny=48, nz=32, dx=1000.0, dy=1000.0, dz=500.0)
    fixture = _make_cams_fixture_with_gradient(tmp_path)
    result = load_cams_co2(fixture, domain, gallery_grid)

    # No NaN/inf values should remain after fill
    assert np.all(np.isfinite(result)), "NaN or inf values remain after fill"

    # Values should be positive (valid CO2 concentrations)
    assert np.all(result > 0), "Non-positive CO2 concentration values"

    # No single value should dominate (fill artifact = many identical values)
    values = result.flatten()
    unique_values = np.unique(values.round(2))
    most_common_count = int(np.max([np.sum(values.round(2) == v) for v in unique_values[:10]]))
    total_count = len(values)
    # A fill artifact would have >20% of values identical
    assert most_common_count / total_count < 0.2, "Single value dominates - possible fill artifact"
