"""Download and filter OCO-3 L2 Lite CO2 data from NASA CMR."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import xarray as xr

from oco_viz.data.transform import latlon_to_local_km, local_km_to_latlon, regrid_to_cartesian

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import DomainConfig, GridConfig, OCO3Config

# Sasol Secunda complex bounding box (lon_min, lat_min, lon_max, lat_max)
_SECUNDA_BBOX = (28.8, -26.7, 29.5, -26.2)

# OCO-3 L2 Lite collection concept ID on CMR
_COLLECTION_ID = "C2910086168-GES_DISC"

_CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"


def search_granules(
    start_date: str,
    end_date: str,
    *,
    bbox: tuple[float, float, float, float] = _SECUNDA_BBOX,
    collection_id: str = _COLLECTION_ID,
    page_size: int = 200,
) -> list[dict[str, Any]]:
    """Search NASA CMR for OCO-3 granules overlapping *bbox* in the date range.

    Returns a list of granule metadata dicts with keys 'title', 'id', and 'links'.
    """
    params = {
        "collection_concept_id": collection_id,
        "temporal": f"{start_date},{end_date}",
        "bounding_box": ",".join(str(v) for v in bbox),
        "page_size": str(page_size),
        "sort_key": "-start_date",
    }
    query = urllib.parse.urlencode(params)
    url = f"{_CMR_SEARCH_URL}?{query}"

    req = urllib.request.Request(url, headers={"Accept": "application/json"})  # noqa: S310
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        data = json.loads(resp.read().decode())

    entries: list[dict[str, Any]] = data.get("feed", {}).get("entry", [])
    return entries


def granule_download_urls(entries: list[dict[str, Any]]) -> list[str]:
    """Extract HTTPS download URLs from CMR granule entries."""
    urls: list[str] = []
    for entry in entries:
        for link in entry.get("links", []):
            href = link.get("href", "")
            if href.endswith(".nc4") and "opendap" not in href.lower():
                urls.append(href)
                break
    return urls


def download_granule(url: str, dest: Path, *, token: str | None = None) -> Path:
    """Download a single granule file.

    If *token* is provided it is sent as a Bearer Authorization header
    (required for Earthdata Login protected data).

    Uses *requests* when available (handles Earthdata OAuth redirects),
    falls back to *urllib* for simple servers.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        import requests as _requests  # noqa: PLC0415

        session = _requests.Session()
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        resp = session.get(url, stream=True, allow_redirects=True, timeout=120)
        resp.raise_for_status()
        with dest.open("wb") as fout:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fout.write(chunk)
    except ModuleNotFoundError:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)  # noqa: S310
        with urllib.request.urlopen(req) as resp_u, dest.open("wb") as fout:  # noqa: S310
            while chunk_b := resp_u.read(1 << 16):
                fout.write(chunk_b)

    return dest


def filter_quality(
    xco2: NDArray[np.float64],
    quality_flag: NDArray[np.floating[Any] | np.integer[Any]],
) -> NDArray[np.float64]:
    """Return XCO2 values that pass quality filtering (flag == 0)."""
    mask = quality_flag == 0
    return np.asarray(xco2[mask], dtype=np.float64)


def load_granule(
    path: Path,
    *,
    quality_threshold: int | None = 0,
) -> xr.Dataset:
    """Load an OCO-3 L2 Lite NetCDF4 file and optionally apply quality filtering.

    Returns xr.Dataset with dims (sounding_id,) containing xco2, latitude, longitude.
    If *quality_threshold* is None, no filtering is applied.
    """
    ds: xr.Dataset = xr.open_dataset(str(path))

    if quality_threshold is not None and "xco2_quality_flag" in ds:
        mask = ds["xco2_quality_flag"] <= quality_threshold
        ds = ds.where(mask, drop=True)

    return ds


def load_and_grid_granules(
    paths: list[Path],
    domain: DomainConfig,
    grid: GridConfig,
) -> xr.Dataset:
    """Load, concatenate, and grid OCO-3 granules onto a 2D Cartesian grid.

    Returns xr.Dataset with {xco2_observed} on dims (y, x), float32.
    Empty cells are NaN.
    """
    # Load and concatenate all granules
    datasets = [load_granule(p) for p in paths]
    combined = xr.concat(datasets, dim="sounding_id")

    # Filter to domain bounding box
    lats = combined["latitude"].values
    lons = combined["longitude"].values
    xco2 = combined["xco2"].values

    # Convert to local km
    x_km, y_km = latlon_to_local_km(
        lats, lons, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    x_m = np.asarray(x_km, dtype=np.float64) * 1000.0
    y_m = np.asarray(y_km, dtype=np.float64) * 1000.0

    # Filter to grid extent
    x_max = grid.nx * grid.dx
    y_max = grid.ny * grid.dy
    in_domain = (x_m >= 0) & (x_m < x_max) & (y_m >= 0) & (y_m < y_max)

    gridded = regrid_to_cartesian(
        xco2[in_domain].astype(np.float32),
        x_m[in_domain],
        y_m[in_domain],
        grid,
    )

    tgt_y = np.arange(grid.ny, dtype=np.float64) * grid.dy
    tgt_x = np.arange(grid.nx, dtype=np.float64) * grid.dx

    return xr.Dataset(
        {"xco2_observed": (["y", "x"], gridded)},
        coords={"y": tgt_y, "x": tgt_x},
    )


def search_and_download(
    domain: DomainConfig,
    oco3_cfg: OCO3Config,
    start_date: str,
    end_date: str,
    dest_dir: Path,
    *,
    token: str | None = None,
) -> list[Path]:
    """Search for OCO-3 granules and download them to dest_dir.

    Returns list of downloaded file paths.
    """
    half_x = domain.extent_x_km / 2.0
    half_y = domain.extent_y_km / 2.0
    lat_s, lon_w = local_km_to_latlon(
        -half_x, -half_y, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    lat_n, lon_e = local_km_to_latlon(
        half_x, half_y, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
    )
    bbox = (float(lon_w), float(lat_s), float(lon_e), float(lat_n))

    entries = search_granules(
        start_date, end_date,
        bbox=bbox,
        collection_id=oco3_cfg.collection_id,
    )
    urls = granule_download_urls(entries)

    downloaded: list[Path] = []
    for url in urls:
        filename = url.rsplit("/", 1)[-1]
        dest = Path(dest_dir) / filename
        download_granule(url, dest, token=token)
        downloaded.append(dest)

    return downloaded
