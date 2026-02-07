from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

from oco_viz.config.schema import DomainConfig, GridConfig
from oco_viz.data.era5 import (
    build_cds_request,
    load_era5_winds,
    wind_components_from_direction,
)


def test_build_cds_request_date_parsing() -> None:
    req = build_cds_request("2024-03-15")
    assert req["year"] == "2024"
    assert req["month"] == "03"
    assert req["day"] == "15"
    assert "u_component_of_wind" in req["variable"]
    assert "v_component_of_wind" in req["variable"]
    assert len(req["time"]) == 24


def test_build_cds_request_pressure_levels() -> None:
    req = build_cds_request("2024-01-01", pressure_levels=[850, 500])
    assert req["pressure_level"] == ["850", "500"]


def test_wind_components_north_wind() -> None:
    # Wind from the north (0 deg) blowing southward -> u=0, v<0
    u, v = wind_components_from_direction(10.0, 0.0)
    assert abs(u) < 1e-10
    assert v < 0
    assert abs(v - (-10.0)) < 1e-10


def test_wind_components_west_wind() -> None:
    # Wind from the west (270 deg) blowing eastward -> u>0, v~0
    u, v = wind_components_from_direction(10.0, 270.0)
    assert u > 0
    assert abs(u - 10.0) < 1e-6
    assert abs(v) < 1e-6


def test_wind_components_round_trip() -> None:
    speed = 8.5
    direction = 135.0
    u, v = wind_components_from_direction(speed, direction)
    recovered_speed = math.sqrt(u**2 + v**2)
    np.testing.assert_allclose(recovered_speed, speed, atol=1e-10)


def test_nan_threshold_warning(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """ERA5 regridding should warn when NaN fraction exceeds 10%."""
    # Create a minimal ERA5-like dataset where regridding will produce many NaNs.
    # Use a tiny source grid that doesn't cover the target domain, causing extrapolation NaNs.
    n_times, n_levels = 1, 3
    lats = np.array([-26.5, -26.4])  # Very small spatial extent
    lons = np.array([29.1, 29.2])
    pressures = np.array([1000.0, 850.0, 700.0])
    u_data = np.ones((n_times, n_levels, len(lats), len(lons)), dtype=np.float64)
    v_data = np.ones((n_times, n_levels, len(lats), len(lons)), dtype=np.float64)

    ds = xr.Dataset(
        {
            "u": (["time", "pressure_level", "latitude", "longitude"], u_data),
            "v": (["time", "pressure_level", "latitude", "longitude"], v_data),
        },
        coords={
            "time": np.arange(n_times),
            "pressure_level": pressures,
            "latitude": lats,
            "longitude": lons,
        },
    )
    path = tmp_path / "era5_nan_test.nc"
    ds.to_netcdf(str(path))

    domain = DomainConfig(
        origin_lat=-26.52, origin_lon=29.17, extent_x_km=200.0, extent_y_km=200.0
    )
    grid = GridConfig(nx=10, ny=10, nz=10, dx=1000.0, dy=1000.0, dz=500.0)

    with caplog.at_level(logging.WARNING):
        load_era5_winds(path, domain, grid)

    nan_warnings = [r for r in caplog.records if "nan" in r.message.lower()]
    assert len(nan_warnings) > 0, "Expected NaN-related warnings for out-of-coverage regridding"
    threshold_warnings = [r for r in caplog.records if "threshold" in r.message.lower()]
    assert len(threshold_warnings) > 0, "Expected NaN fraction threshold warning"
