"""OCO-2 L2 Lite CO2 data — thin wrapper over shared ``oco`` module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oco_viz.data.oco import (
    SATELLITE_COLLECTION_IDS,
)
from oco_viz.data.oco import (
    load_granule as _load_granule,
)
from oco_viz.data.oco import (
    search_and_download as _search_and_download,
)
from oco_viz.data.oco import (
    search_granules as _search_granules,
)

if TYPE_CHECKING:
    from pathlib import Path

    import xarray as xr

    from oco_viz.config.schema import DomainConfig

# Default Secunda bounding box (lon_min, lat_min, lon_max, lat_max)
# Kept as fallback default; prefer DomainConfig.bbox() for new code.
_DEFAULT_BBOX = (28.8, -26.7, 29.5, -26.2)

# OCO-2 L2 Lite v11.1r collection concept ID on CMR
_COLLECTION_ID = SATELLITE_COLLECTION_IDS["oco2"]


def search_granules(
    start_date: str,
    end_date: str,
    *,
    bbox: tuple[float, float, float, float] = _DEFAULT_BBOX,
    collection_id: str = _COLLECTION_ID,
    page_size: int = 200,
) -> list[dict[str, Any]]:
    """Search NASA CMR for OCO-2 granules overlapping *bbox* in the date range."""
    return _search_granules(
        start_date, end_date, bbox=bbox, collection_id=collection_id, page_size=page_size
    )


def search_and_download(
    domain: DomainConfig,
    collection_id: str,
    start_date: str,
    end_date: str,
    dest_dir: Path,
    *,
    token: str | None = None,
) -> list[Path]:
    """Search for OCO-2 granules and download them to dest_dir."""
    return _search_and_download(
        domain,
        collection_id if collection_id else _COLLECTION_ID,
        start_date,
        end_date,
        dest_dir,
        token=token,
    )


def load_granule(
    path: Path,
    *,
    quality_threshold: int | None = 0,
) -> xr.Dataset:
    """Load an OCO-2 L2 Lite NetCDF4 file and optionally apply quality filtering."""
    return _load_granule(path, quality_threshold=quality_threshold)
