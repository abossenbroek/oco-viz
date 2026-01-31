"""Coordinate transforms between geographic (lat/lon/pressure) and local Cartesian grid."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig

# Earth radius in km (mean)
_EARTH_RADIUS_KM = 6371.0

# Standard atmosphere constants for barometric formula
_P0 = 1013.25  # sea-level pressure (hPa)
_T0 = 288.15  # sea-level temperature (K)
_L = 0.0065  # temperature lapse rate (K/m)
_G = 9.80665  # gravitational acceleration (m/s²)
_M = 0.0289644  # molar mass of dry air (kg/mol)
_R = 8.31447  # universal gas constant (J/(mol·K))


def latlon_to_local_km(
    lat: float | NDArray[np.floating[Any]],
    lon: float | NDArray[np.floating[Any]],
    *,
    origin_lat: float,
    origin_lon: float,
) -> tuple[NDArray[np.float64] | float, NDArray[np.float64] | float]:
    """Convert lat/lon to local Cartesian coordinates (km) using equirectangular approximation.

    Returns (x_km, y_km) where x is east and y is north.
    """
    dlat = np.asarray(lat, dtype=np.float64) - origin_lat
    dlon = np.asarray(lon, dtype=np.float64) - origin_lon

    y_km = dlat * (np.pi / 180.0) * _EARTH_RADIUS_KM
    x_km = dlon * (np.pi / 180.0) * _EARTH_RADIUS_KM * np.cos(np.radians(origin_lat))

    return x_km, y_km


def local_km_to_latlon(
    x_km: float | NDArray[np.floating[Any]],
    y_km: float | NDArray[np.floating[Any]],
    *,
    origin_lat: float,
    origin_lon: float,
) -> tuple[NDArray[np.float64] | float, NDArray[np.float64] | float]:
    """Convert local Cartesian (km) back to lat/lon (inverse of latlon_to_local_km)."""
    lat = np.asarray(y_km, dtype=np.float64) / (_EARTH_RADIUS_KM * np.pi / 180.0) + origin_lat
    lon = (
        np.asarray(x_km, dtype=np.float64)
        / (_EARTH_RADIUS_KM * np.pi / 180.0 * np.cos(np.radians(origin_lat)))
        + origin_lon
    )
    return lat, lon


def pressure_to_altitude_m(
    pressure_hpa: float | NDArray[np.floating[Any]],
) -> NDArray[np.float64] | float:
    """Convert pressure (hPa) to altitude (m) using the barometric formula.

    Uses the International Standard Atmosphere (ISA) tropospheric model:
    h = (T0/L) * (1 - (P/P0)^(R*L/(g*M)))
    """
    p = np.asarray(pressure_hpa, dtype=np.float64)
    exponent = _R * _L / (_G * _M)
    altitude: NDArray[np.float64] | float = (_T0 / _L) * (1.0 - (p / _P0) ** exponent)
    return altitude


def regrid_to_cartesian(
    data: NDArray[np.float32],
    src_x: NDArray[np.float64],
    src_y: NDArray[np.float64],
    grid: GridConfig,
) -> NDArray[np.float32]:
    """Bin scattered data onto a 2D Cartesian grid by cell averaging.

    Returns a (ny, nx) array with NaN for empty cells.
    """
    # Compute grid cell edges
    x_edges = np.arange(grid.nx + 1) * grid.dx
    y_edges = np.arange(grid.ny + 1) * grid.dy

    # Bin indices for each point
    x_idx = np.digitize(src_x, x_edges) - 1
    y_idx = np.digitize(src_y, y_edges) - 1

    # Initialize output
    result = np.full((grid.ny, grid.nx), np.nan, dtype=np.float32)
    counts = np.zeros((grid.ny, grid.nx), dtype=np.int32)
    sums = np.zeros((grid.ny, grid.nx), dtype=np.float64)

    # Accumulate
    valid = (x_idx >= 0) & (x_idx < grid.nx) & (y_idx >= 0) & (y_idx < grid.ny)
    for i in range(len(data)):
        if valid[i]:
            yi, xi = y_idx[i], x_idx[i]
            sums[yi, xi] += data[i]
            counts[yi, xi] += 1

    # Average where we have data
    has_data = counts > 0
    result[has_data] = (sums[has_data] / counts[has_data]).astype(np.float32)

    return result
