"""Tests for coordinate transforms between geographic and local Cartesian grid."""

from __future__ import annotations

import numpy as np
import pytest

from oco_viz.config.schema import GridConfig
from oco_viz.data.transform import (
    latlon_to_local_km,
    local_km_to_latlon,
    pressure_to_altitude_m,
    regrid_to_cartesian,
)


# --- latlon_to_local_km / local_km_to_latlon round-trip ---


def test_latlon_to_local_km_origin_is_zero():
    x, y = latlon_to_local_km(-26.52, 29.17, origin_lat=-26.52, origin_lon=29.17)
    assert abs(x) < 1e-10
    assert abs(y) < 1e-10


def test_latlon_to_local_km_one_degree_lat():
    """One degree latitude ~ 111 km."""
    _, y = latlon_to_local_km(-25.52, 29.17, origin_lat=-26.52, origin_lon=29.17)
    assert 109 < y < 113


def test_latlon_to_local_km_one_degree_lon():
    """One degree longitude at -26.5 lat ~ 99 km (cos correction)."""
    x, _ = latlon_to_local_km(-26.52, 30.17, origin_lat=-26.52, origin_lon=29.17)
    assert 95 < x < 103


def test_round_trip_latlon():
    """latlon -> local -> latlon should recover original coords."""
    lat, lon = -26.3, 29.5
    origin_lat, origin_lon = -26.52, 29.17
    x, y = latlon_to_local_km(lat, lon, origin_lat=origin_lat, origin_lon=origin_lon)
    lat2, lon2 = local_km_to_latlon(x, y, origin_lat=origin_lat, origin_lon=origin_lon)
    np.testing.assert_allclose(lat2, lat, atol=0.01)
    np.testing.assert_allclose(lon2, lon, atol=0.01)


def test_latlon_to_local_km_arrays():
    """Should work with numpy arrays."""
    lats = np.array([-26.52, -25.52])
    lons = np.array([29.17, 30.17])
    x, y = latlon_to_local_km(lats, lons, origin_lat=-26.52, origin_lon=29.17)
    assert x.shape == (2,)
    assert y.shape == (2,)


# --- pressure_to_altitude_m ---


def test_pressure_1013_is_zero():
    """Standard sea-level pressure should give ~0 m altitude."""
    alt = pressure_to_altitude_m(1013.25)
    assert abs(alt) < 50  # within 50 m of sea level


def test_pressure_500_is_high():
    """500 hPa ~ 5500 m in standard atmosphere."""
    alt = pressure_to_altitude_m(500.0)
    assert 5000 < alt < 6000


def test_pressure_monotonic():
    """Lower pressure = higher altitude."""
    pressures = [1000, 850, 700, 500, 300]
    altitudes = [pressure_to_altitude_m(p) for p in pressures]
    for i in range(len(altitudes) - 1):
        assert altitudes[i] < altitudes[i + 1]


def test_pressure_array():
    """Should work with numpy arrays."""
    p = np.array([1000.0, 500.0])
    alt = pressure_to_altitude_m(p)
    assert alt.shape == (2,)
    assert alt[0] < alt[1]


# --- regrid_to_cartesian ---


def test_regrid_to_cartesian_shape():
    """Output shape should match grid config."""
    grid = GridConfig(nx=10, ny=10, nz=5, dx=1000.0, dy=1000.0, dz=500.0)
    n_points = 50
    rng = np.random.default_rng(42)
    data = rng.uniform(0, 1, n_points).astype(np.float32)
    src_x = rng.uniform(0, 10000, n_points)
    src_y = rng.uniform(0, 10000, n_points)
    result = regrid_to_cartesian(data, src_x, src_y, grid)
    assert result.shape == (grid.ny, grid.nx)


def test_regrid_to_cartesian_nan_fill():
    """Cells with no data should be NaN."""
    grid = GridConfig(nx=10, ny=10, nz=5, dx=1000.0, dy=1000.0, dz=500.0)
    # Place all data in one corner
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    src_x = np.array([500.0, 500.0, 1500.0])
    src_y = np.array([500.0, 1500.0, 500.0])
    result = regrid_to_cartesian(data, src_x, src_y, grid)
    # Far corner should be NaN
    assert np.isnan(result[9, 9])


def test_regrid_to_cartesian_correct_binning():
    """Points in same cell should be averaged."""
    grid = GridConfig(nx=5, ny=5, nz=1, dx=1000.0, dy=1000.0, dz=500.0)
    # Two points in cell (0, 0)
    data = np.array([10.0, 20.0], dtype=np.float32)
    src_x = np.array([100.0, 200.0])  # both in x-cell 0
    src_y = np.array([100.0, 200.0])  # both in y-cell 0
    result = regrid_to_cartesian(data, src_x, src_y, grid)
    np.testing.assert_allclose(result[0, 0], 15.0, atol=0.01)
