"""OCO-3 L2 Lite CO2 data — thin wrapper over shared ``oco`` module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oco_viz.data.oco import (
    SATELLITE_COLLECTION_IDS,
    download_granule,
    filter_quality,
    granule_download_urls,
    load_and_grid_granules,
    load_granule,
)
from oco_viz.data.oco import (
    search_and_download as _search_and_download,
)
from oco_viz.data.oco import (
    search_granules as _search_granules,
)

if TYPE_CHECKING:
    from pathlib import Path

    from oco_viz.config.schema import DomainConfig, OCO3Config

# Sasol Secunda complex bounding box (lon_min, lat_min, lon_max, lat_max)
_SECUNDA_BBOX = (28.8, -26.7, 29.5, -26.2)

_COLLECTION_ID = SATELLITE_COLLECTION_IDS["oco3"]


def search_granules(
    start_date: str,
    end_date: str,
    *,
    bbox: tuple[float, float, float, float] = _SECUNDA_BBOX,
    collection_id: str = _COLLECTION_ID,
    page_size: int = 200,
) -> list[dict[str, Any]]:
    """Search NASA CMR for OCO-3 granules overlapping *bbox* in the date range."""
    return _search_granules(
        start_date, end_date, bbox=bbox, collection_id=collection_id, page_size=page_size
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
    """Search for OCO-3 granules and download them to dest_dir."""
    return _search_and_download(
        domain,
        oco3_cfg.collection_id,
        start_date,
        end_date,
        dest_dir,
        token=token,
    )


# Re-export shared functions so existing imports continue to work
__all__ = [
    "download_granule",
    "filter_quality",
    "granule_download_urls",
    "load_and_grid_granules",
    "load_granule",
    "search_and_download",
    "search_granules",
]
