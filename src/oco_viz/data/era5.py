"""Download ERA5 wind data from the Copernicus Climate Data Store."""

from __future__ import annotations

import importlib
import math
from typing import TYPE_CHECKING, Any

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

from oco_viz.data.transform import latlon_to_local_km, local_km_to_latlon, pressure_to_altitude_m

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import DomainConfig, ERA5Config, GridConfig


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
        np.degrees(np.arctan2(-u, -v)) % 360,
        dtype=np.float64,
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


def build_era5_request_for_domain(
    domain: DomainConfig,
    era5_cfg: ERA5Config,
    date: str,
) -> dict[str, Any]:
    """Derive CDS API request from DomainConfig and ERA5Config."""
    # Compute bounding box from domain extents
    half_x = domain.extent_x_km / 2.0
    half_y = domain.extent_y_km / 2.0
    lat_s, lon_w = local_km_to_latlon(
        -half_x, -half_y, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    lat_n, lon_e = local_km_to_latlon(
        half_x, half_y, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    # CDS area format: [N, W, S, E]
    return build_cds_request(
        date,
        lat=domain.origin_lat,
        lon=domain.origin_lon,
        pressure_levels=era5_cfg.pressure_levels,
    ) | {"area": [float(lat_n), float(lon_w), float(lat_s), float(lon_e)]}


def load_era5_winds(
    path: Path,
    domain: DomainConfig,
    grid: GridConfig,
) -> xr.Dataset:
    """Load ERA5 NetCDF winds and regrid to local Cartesian grid.

    Returns xr.Dataset with {u_wind, v_wind} on dims (time, z, y, x), float32.
    """
    ds: xr.Dataset = xr.open_dataset(str(path))

    # Source coordinates
    src_lats = ds["latitude"].values
    src_lons = ds["longitude"].values
    src_pressure = ds["pressure_level"].values
    n_times = ds.sizes["time"]

    # Convert source coords to local km / altitude m
    src_x_km, _ = latlon_to_local_km(
        src_lats[0], src_lons, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    _, src_y_km = latlon_to_local_km(
        src_lats, src_lons[0], origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    src_x_m = np.asarray(src_x_km, dtype=np.float64) * 1000.0
    src_y_m = np.asarray(src_y_km, dtype=np.float64) * 1000.0
    src_z_m = np.asarray(pressure_to_altitude_m(src_pressure), dtype=np.float64)

    # Target grid coordinates in meters
    tgt_x = np.arange(grid.nx, dtype=np.float64) * grid.dx
    tgt_y = np.arange(grid.ny, dtype=np.float64) * grid.dy
    tgt_z = np.arange(grid.nz, dtype=np.float64) * grid.dz

    # Sort source axes (RegularGridInterpolator needs ascending)
    z_order = np.argsort(src_z_m)
    y_order = np.argsort(src_y_m)
    x_order = np.argsort(src_x_m)
    src_z_sorted = src_z_m[z_order]
    src_y_sorted = src_y_m[y_order]
    src_x_sorted = src_x_m[x_order]

    # Build output arrays
    u_out = np.zeros((n_times, grid.nz, grid.ny, grid.nx), dtype=np.float32)
    v_out = np.zeros((n_times, grid.nz, grid.ny, grid.nx), dtype=np.float32)

    # Target meshgrid for interpolation
    tgt_pts = np.stack(
        np.meshgrid(tgt_z, tgt_y, tgt_x, indexing="ij"), axis=-1
    ).reshape(-1, 3)

    for t in range(n_times):
        for var_name, out_arr in [("u", u_out), ("v", v_out)]:
            data_3d = ds[var_name].isel(time=t).values  # (pressure, lat, lon)
            # Reorder to sorted axes
            data_sorted = data_3d[np.ix_(z_order, y_order, x_order)]

            interp = RegularGridInterpolator(
                (src_z_sorted, src_y_sorted, src_x_sorted),
                data_sorted,
                method="linear",
                bounds_error=False,
                fill_value=np.nan,
            )
            out_arr[t] = interp(tgt_pts).reshape(grid.nz, grid.ny, grid.nx).astype(np.float32)

    return xr.Dataset(
        {
            "u_wind": (["time", "z", "y", "x"], u_out),
            "v_wind": (["time", "z", "y", "x"], v_out),
        },
        coords={
            "time": np.arange(n_times),
            "z": tgt_z,
            "y": tgt_y,
            "x": tgt_x,
        },
    )
