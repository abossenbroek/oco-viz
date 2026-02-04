"""CAMS high-resolution GHG forecast loader with regridding."""

from __future__ import annotations

import importlib
import zipfile
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

from oco_viz.data.transform import latlon_to_local_km

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import DomainConfig, GridConfig

# Molar masses for unit conversion (kg/kg -> ppm)
_M_AIR = 28.97e-3  # kg/mol
_M_CO2 = 44.01e-3  # kg/mol

# Standard atmosphere constants for hypsometric equation
_R_D = 287.05  # J/(kg·K), specific gas constant for dry air
_G = 9.80665  # m/s²


def _build_cams_request(
    date: str,
    domain: DomainConfig,
) -> dict[str, Any]:
    """Build a CDS API request dict for CAMS high-res GHG forecast."""
    half_x = domain.extent_x_km / 2.0
    half_y = domain.extent_y_km / 2.0
    # Approximate degree offsets
    dlat = half_y / 111.32
    dlon = half_x / (111.32 * np.cos(np.radians(domain.origin_lat)))

    return {
        "variable": ["carbon_dioxide"],
        "model_level": [str(i) for i in range(60, 138)],  # lower atmosphere
        "date": date,
        "leadtime_hour": [str(h) for h in range(0, 25, 3)],
        "area": [
            float(domain.origin_lat + dlat),
            float(domain.origin_lon - dlon),
            float(domain.origin_lat - dlat),
            float(domain.origin_lon + dlon),
        ],
        "data_format": "netcdf_zip",
    }


def download_cams_co2(
    date: str,
    domain: DomainConfig,
    cache_dir: Path,
) -> Path:
    """Download CAMS high-res GHG forecast via ADS API.

    Dataset: ``cams-global-greenhouse-gas-forecasts``.
    Returns path to the extracted NetCDF file.
    """
    cdsapi = importlib.import_module("cdsapi")
    request = _build_cams_request(date, domain)
    zip_dest = cache_dir / f"cams_co2_{date}.netcdf_zip"
    nc_dest = cache_dir / f"cams_co2_{date}.nc"
    cache_dir.mkdir(parents=True, exist_ok=True)

    client = cdsapi.Client(url="https://ads.atmosphere.copernicus.eu/api")
    client.retrieve("cams-global-greenhouse-gas-forecasts", request, str(zip_dest))

    with zipfile.ZipFile(zip_dest) as zf:
        nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
        if not nc_names:
            msg = f"No .nc file found in downloaded archive: {zf.namelist()}"
            raise FileNotFoundError(msg)
        zf.extract(nc_names[0], cache_dir)
        extracted = cache_dir / nc_names[0]
        if extracted != nc_dest:
            extracted.rename(nc_dest)

    zip_dest.unlink()
    return nc_dest


def _kgkg_to_ppm(mass_fraction: NDArray[np.floating[Any]]) -> NDArray[np.float64]:
    """Convert CO2 mass mixing ratio (kg/kg) to ppm (mole fraction)."""
    return np.asarray(mass_fraction, dtype=np.float64) * 1e6 * _M_AIR / _M_CO2


def _hybrid_sigma_to_altitude(
    temperature: NDArray[np.floating[Any]],
    n_levels: int,
) -> NDArray[np.float64]:
    """Approximate altitude from model levels using mean temperature profile.

    Uses hypsometric equation: dz = (R_d * T / g) * d(ln p).
    Returns altitude array (m) for each model level, approximated from
    a linearly-spaced pressure profile.
    """
    # Approximate pressure levels from model level indices
    # CAMS L137: level 60 ~ 100 hPa, level 137 ~ 1013 hPa
    p_top = 100.0  # hPa
    p_bot = 1013.25  # hPa
    pressures = np.linspace(p_bot, p_top, n_levels)  # surface to top

    # Mean temperature per level (average over horizontal dims)
    t_mean: NDArray[np.float64]
    if temperature.ndim >= 3:
        # Average over all dims except the level dim (first)
        axes = tuple(range(1, temperature.ndim))
        t_mean = np.nanmean(temperature, axis=axes).astype(np.float64)
    else:
        t_mean = np.asarray(temperature, dtype=np.float64)

    # Integrate hypsometric equation from surface upward
    altitudes = np.zeros(n_levels, dtype=np.float64)
    for i in range(1, n_levels):
        t_layer = 0.5 * (t_mean[i - 1] + t_mean[i])
        dp = np.log(pressures[i - 1] / pressures[i])
        altitudes[i] = altitudes[i - 1] + (_R_D * t_layer / _G) * dp

    return altitudes


def load_cams_co2(  # noqa: C901, PLR0915
    path: Path,
    domain: DomainConfig,
    grid: GridConfig,
) -> NDArray[np.float32]:
    """Load CAMS NetCDF, convert to ppm, regrid to local Cartesian grid.

    Returns a 3D array of shape ``(nz, ny, nx)`` with CO2 concentration in ppm.
    """
    ds: xr.Dataset = xr.open_dataset(str(path))

    # Identify CO2 variable (different CAMS versions use different names)
    co2_var = None
    for candidate in ("co2", "carbon_dioxide", "CO2"):
        if candidate in ds:
            co2_var = candidate
            break
    if co2_var is None:
        msg = f"No CO2 variable found in {path}. Available: {list(ds.data_vars)}"
        raise KeyError(msg)

    co2_raw = ds[co2_var]

    # Select first time step if multiple (handle various CAMS dimension names)
    for time_dim in ("time", "forecast_reference_time", "forecast_period"):
        if time_dim in co2_raw.dims:
            co2_raw = co2_raw.isel({time_dim: 0})

    co2_values = co2_raw.values  # (level, lat, lon) or similar

    # Convert units if needed (check if already in ppm range)
    if float(np.nanmean(co2_values)) < 1.0:
        co2_ppm = _kgkg_to_ppm(co2_values)
    else:
        co2_ppm = np.asarray(co2_values, dtype=np.float64)

    # Get temperature for vertical coordinate conversion
    temp_var = None
    for candidate in ("t", "temperature", "T"):
        if candidate in ds:
            temp_var = candidate
            break

    n_levels = co2_ppm.shape[0]

    if temp_var is not None:
        temp_data = ds[temp_var]
        if "time" in temp_data.dims:
            temp_data = temp_data.isel(time=0)
        src_z = _hybrid_sigma_to_altitude(temp_data.values, n_levels)
    else:
        # Fallback: assume linearly spaced from 0 to extent_z_km
        src_z = np.linspace(0, domain.extent_z_km * 1000.0, n_levels)

    # Source horizontal coordinates
    lat_name = "latitude" if "latitude" in ds.coords else "lat"
    lon_name = "longitude" if "longitude" in ds.coords else "lon"
    src_lats = ds[lat_name].values
    src_lons = ds[lon_name].values

    # Convert to local meters using center latitude for consistent coordinate mapping.
    # Using center latitude avoids skew from Earth's curvature over the domain.
    center_lat = domain.origin_lat
    src_x_km, _ = latlon_to_local_km(
        np.full_like(src_lons, center_lat),
        src_lons,
        origin_lat=domain.origin_lat,
        origin_lon=domain.origin_lon,
    )
    _, src_y_km = latlon_to_local_km(
        src_lats,
        np.full_like(src_lats, domain.origin_lon),
        origin_lat=domain.origin_lat,
        origin_lon=domain.origin_lon,
    )
    src_x_m = np.asarray(src_x_km, dtype=np.float64) * 1000.0
    src_y_m = np.asarray(src_y_km, dtype=np.float64) * 1000.0
    src_z_m = np.asarray(src_z, dtype=np.float64)

    # Target grid (centered around domain origin to match geographic source data)
    half_extent_x = grid.nx * grid.dx / 2.0
    half_extent_y = grid.ny * grid.dy / 2.0
    tgt_x = np.linspace(-half_extent_x + grid.dx / 2, half_extent_x - grid.dx / 2, grid.nx)
    tgt_y = np.linspace(-half_extent_y + grid.dy / 2, half_extent_y - grid.dy / 2, grid.ny)
    tgt_z = np.arange(grid.nz, dtype=np.float64) * grid.dz

    # Sort source axes for RegularGridInterpolator
    z_order = np.argsort(src_z_m)
    y_order = np.argsort(src_y_m)
    x_order = np.argsort(src_x_m)

    co2_sorted = co2_ppm[np.ix_(z_order, y_order, x_order)]

    interp = RegularGridInterpolator(
        (src_z_m[z_order], src_y_m[y_order], src_x_m[x_order]),
        co2_sorted,
        method="linear",
        bounds_error=False,
        fill_value=np.nan,
    )

    tgt_pts = np.stack(
        np.meshgrid(tgt_z, tgt_y, tgt_x, indexing="ij"),
        axis=-1,
    ).reshape(-1, 3)

    result = interp(tgt_pts).reshape(grid.nz, grid.ny, grid.nx)

    # Handle OOB regions: fill NaN with background median
    # NOTE: Edge feathering moved to normalization stage (normalize.py)
    # to avoid corrupting background profile estimation for anomaly mode
    background_ppm = float(np.nanmedian(result))
    result = np.nan_to_num(result, nan=background_ppm)

    return cast("NDArray[np.float32]", result.astype(np.float32))
