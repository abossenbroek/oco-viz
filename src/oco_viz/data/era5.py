"""Download ERA5 wind data from the Copernicus Climate Data Store."""

from __future__ import annotations

import importlib
import math
from typing import TYPE_CHECKING, Any

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


# Secunda approximate location
_SECUNDA_LAT = -26.5
_SECUNDA_LON = 29.2

# Pressure levels covering boundary layer (hPa)
_PRESSURE_LEVELS = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500]


def build_cds_request(
    date: str,
    *,
    lat: float = _SECUNDA_LAT,
    lon: float = _SECUNDA_LON,
    pressure_levels: list[int] | None = None,
) -> dict[str, Any]:
    """Build a CDS API request dict for ERA5 u/v wind components.

    *date* should be ``'YYYY-MM-DD'``.
    """
    levels = pressure_levels or _PRESSURE_LEVELS
    return {
        "product_type": "reanalysis",
        "variable": ["u_component_of_wind", "v_component_of_wind"],
        "pressure_level": [str(p) for p in levels],
        "year": date[:4],
        "month": date[5:7],
        "day": date[8:10],
        "time": [f"{h:02d}:00" for h in range(24)],
        "area": [lat + 0.5, lon - 0.5, lat - 0.5, lon + 0.5],
        "format": "netcdf",
    }


def download_era5(
    request: dict[str, Any],
    dest: Path,
) -> Path:
    """Download ERA5 data via the CDS API (requires ``cdsapi`` installed).

    Returns *dest* on success.
    """
    cdsapi = importlib.import_module("cdsapi")
    client = cdsapi.Client()
    client.retrieve("reanalysis-era5-pressure-levels", request, str(dest))
    return dest


def extract_wind_profile(
    path: Path,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Extract mean wind speed and direction time series from an ERA5 NetCDF.

    Returns ``(speed, direction)`` arrays with shape ``(n_times,)``.
    Speed is in m/s, direction is meteorological degrees (from which wind blows).
    """
    ds: xr.Dataset = xr.open_dataset(str(path))
    # Average over spatial and pressure dimensions
    u = ds["u"].mean(dim=["latitude", "longitude", "pressure_level"]).values
    v = ds["v"].mean(dim=["latitude", "longitude", "pressure_level"]).values

    speed: NDArray[np.float64] = np.sqrt(u**2 + v**2)
    # Meteorological direction: direction wind is coming FROM
    direction: NDArray[np.float64] = np.asarray(
        np.degrees(np.arctan2(-u, -v)) % 360, dtype=np.float64,
    )
    return speed, direction


def wind_components_from_direction(
    speed: float,
    direction_deg: float,
) -> tuple[float, float]:
    """Convert met wind (speed, direction-from) to (u, v) components."""
    rad = math.radians(direction_deg)
    u = -speed * math.sin(rad)
    v = -speed * math.cos(rad)
    return u, v
