"""NASA Earthdata ECD (Enhanced Column Density) loader with turbulence coupling."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from oco_viz.data.transform import latlon_to_local_km

if TYPE_CHECKING:
    import types
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import DomainConfig, ECDConfig, GridConfig

logger = logging.getLogger(__name__)


def _import_earthaccess() -> types.ModuleType | None:
    """Lazy-import earthaccess; return None if unavailable."""
    try:
        return importlib.import_module("earthaccess")
    except ImportError:
        logger.warning(
            "earthaccess not installed — ECD data ingestion disabled. "
            "Install with: pixi add earthaccess"
        )
        return None


def search_ecd_granules(
    ecd_cfg: ECDConfig,
    domain: DomainConfig,
) -> list[str]:
    """Search NASA CMR for ECD granules matching config.

    Returns list of granule URLs, or empty list if earthaccess is unavailable.
    """
    ea = _import_earthaccess()
    if ea is None:
        return []

    bbox = domain.bbox()
    start_date, end_date = ecd_cfg.date_range

    results = ea.search_data(
        short_name="OCO3_L2_Lite_FP",
        temporal=(start_date, end_date),
        bounding_box=(bbox[0], bbox[1], bbox[2], bbox[3]),
    )

    urls: list[str] = []
    for granule in results:
        links = ea.get_https_links(granule)
        urls.extend(links)

    logger.info("Found %d ECD granule URLs for %s to %s", len(urls), start_date, end_date)
    return urls


def download_ecd_granules(
    urls: list[str],
    cache_dir: Path,
) -> list[Path]:
    """Download ECD granules to cache directory.

    Returns list of local file paths. Falls back gracefully if earthaccess
    is unavailable.
    """
    ea = _import_earthaccess()
    if ea is None:
        return []

    cache_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = ea.download(urls, str(cache_dir))
    logger.info("Downloaded %d ECD files to %s", len(downloaded), cache_dir)
    return downloaded


def load_ecd_data(path: Path) -> xr.Dataset:
    """Load a single ECD NetCDF/HDF5 file into an xr.Dataset.

    Expects variables: xco2, latitude, longitude.
    Returns dataset with ecd_xco2 on (sounding,) dimension.
    """
    ds: xr.Dataset = xr.open_dataset(str(path))

    # Normalize variable names (OCO-3 L2 Lite uses 'xco2')
    rename_map: dict[str, str] = {}
    if "xco2" in ds and "ecd_xco2" not in ds:
        rename_map["xco2"] = "ecd_xco2"
    if rename_map:
        ds = ds.rename(rename_map)

    return ds


def compute_ecd_anomaly(
    ecd_ds: xr.Dataset,
    background_ppm: float = 415.0,
) -> NDArray[np.float32]:
    """Compute ECD anomaly (delta from background).

    Returns 1D array of anomaly values (positive = enhancement above background).
    """
    xco2 = ecd_ds["ecd_xco2"].values.astype(np.float64)
    delta = np.maximum(xco2 - background_ppm, 0.0)
    return delta.astype(np.float32)


def regrid_ecd_to_domain(
    ecd_ds: xr.Dataset,
    anomaly: NDArray[np.float32],
    domain: DomainConfig,
    grid: GridConfig,
) -> NDArray[np.float32]:
    """Regrid sparse ECD anomaly observations onto the 2D domain grid.

    Returns 2D array of shape (ny, nx) with ECD anomaly values,
    using nearest-neighbor interpolation for sparse satellite data.
    """
    lats = ecd_ds["latitude"].values
    lons = ecd_ds["longitude"].values

    x_km_raw, y_km_raw = latlon_to_local_km(
        lats,
        lons,
        origin_lat=domain.origin_lat,
        origin_lon=domain.origin_lon,
    )
    x_km = np.atleast_1d(np.asarray(x_km_raw, dtype=np.float64))
    y_km = np.atleast_1d(np.asarray(y_km_raw, dtype=np.float64))

    # Target grid edges
    half_x = grid.nx * grid.dx / 2000.0  # km
    half_y = grid.ny * grid.dy / 2000.0  # km

    # Bin observations into grid cells
    result = np.zeros((grid.ny, grid.nx), dtype=np.float64)
    counts = np.zeros((grid.ny, grid.nx), dtype=np.int64)

    for i in range(len(x_km)):
        ix = int((x_km[i] + half_x) / (grid.dx / 1000.0))
        iy = int((y_km[i] + half_y) / (grid.dy / 1000.0))
        if 0 <= ix < grid.nx and 0 <= iy < grid.ny:
            result[iy, ix] += anomaly[i]
            counts[iy, ix] += 1

    # Average where we have observations
    valid = counts > 0
    result[valid] /= counts[valid]

    return result.astype(np.float32)


def attach_ecd_anomaly(
    ds: xr.Dataset,
    ecd_paths: list[Path],
    domain: DomainConfig,
    grid: GridConfig,
    *,
    anomaly_scale: float = 1.0,
    background_ppm: float = 415.0,
) -> xr.Dataset:
    """Add ecd_delta variable to an existing dataset.

    Follows the pattern of ``attach_satellite_overlay()`` in ``data/pipeline.py``.
    The ecd_delta field is a 2D (y, x) grid of scaled anomaly values suitable
    for computing turbulence amplitude modulation.

    Parameters
    ----------
    ds
        Existing dataset to augment.
    ecd_paths
        Paths to ECD data files.
    domain
        Geographic domain configuration.
    grid
        Spatial grid configuration.
    anomaly_scale
        Scaling factor applied to anomaly values.
    background_ppm
        Background CO2 level for anomaly computation.

    """
    if not ecd_paths:
        logger.info("No ECD paths provided — skipping ECD attachment")
        return ds

    # Load and combine all ECD files
    ecd_datasets = [load_ecd_data(p) for p in ecd_paths]
    combined = xr.concat(ecd_datasets, dim="sounding")

    anomaly = compute_ecd_anomaly(combined, background_ppm=background_ppm)
    gridded = regrid_ecd_to_domain(combined, anomaly, domain, grid)

    # Scale the anomaly
    gridded *= anomaly_scale

    ds["ecd_delta"] = (["y", "x"], gridded)
    return ds


def compute_amplitude_modulator(
    ecd_delta: NDArray[np.float32],
    anomaly_scale: float = 1.0,
) -> float:
    """Compute turbulence amplitude modulator from ECD anomaly delta.

    Formula: amplitude_modulator = 1.0 + anomaly_scale * mean(normalized_ecd_delta)

    A modulator of 1.0 means no change (default). Values > 1.0 increase turbulence
    in regions with higher ECD anomaly.
    """
    if ecd_delta.size == 0 or float(ecd_delta.max()) < 1e-8:
        return 1.0

    # Normalize to [0, 1] based on max
    normalized = ecd_delta / max(float(ecd_delta.max()), 1e-8)
    mean_delta = float(np.mean(normalized[normalized > 0])) if np.any(normalized > 0) else 0.0

    return 1.0 + anomaly_scale * mean_delta
