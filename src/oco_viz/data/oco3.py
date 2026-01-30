"""Download and filter OCO-3 L2 Lite CO2 data from NASA CMR."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

# Sasol Secunda complex bounding box (lon_min, lat_min, lon_max, lat_max)
_SECUNDA_BBOX = (28.8, -26.7, 29.5, -26.2)

# OCO-3 L2 Lite collection concept ID on CMR
_COLLECTION_ID = "C2237486636-GES_DISC"

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
    """
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)  # noqa: S310
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req) as resp, dest.open("wb") as fout:  # noqa: S310
        while chunk := resp.read(1 << 16):
            fout.write(chunk)
    return dest


def filter_quality(
    xco2: NDArray[np.float64],
    quality_flag: NDArray[np.int8],
) -> NDArray[np.float64]:
    """Return XCO2 values that pass quality filtering (flag == 0)."""
    mask = quality_flag == 0
    return np.asarray(xco2[mask], dtype=np.float64)
