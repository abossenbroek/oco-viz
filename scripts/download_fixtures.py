"""Download test fixtures for data pipeline tests.

Requires:
- CDS API credentials (~/.cdsapirc) for ERA5 downloads
- NASA Earthdata token (EARTHDATA_TOKEN env var) for OCO-2/OCO-3 download

Usage:
    python scripts/download_fixtures.py [--era5-only | --oco3-only | --oco2-only]
    python scripts/download_fixtures.py --date 2025-10-13  # single-date override

The OCO-2 and OCO-3 downloaders use ``find_nearest_passes`` to pick the
granule closest to a reference date (default 2025-10-15) so that both
satellites cover the same period.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add src to path so we can import oco_viz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Reference date: both OCO-2 V11.2r and OCO-3 V11r have Secunda data here
_REFERENCE_DATE = "2025-10-15"
_SECUNDA_LAT = -26.52
_SECUNDA_LON = 29.17

# Actual OCO pass dates over Secunda
_OCO2_DATE = "2025-10-13"
_OCO3_DATE = "2025-10-26"
_PASS_DATES = [_OCO2_DATE, _OCO3_DATE]


def download_era5_fixture(dest: Path, date: str) -> None:
    """Download ERA5 sample: 1 day over Sasol Secunda bbox."""
    from oco_viz.data.era5 import build_cds_request, download_era5  # noqa: PLC0415

    print(f"Downloading ERA5 fixture for {date} to {dest}")
    request = build_cds_request(
        date,
        lat=-26.5,
        lon=29.2,
        pressure_levels=[1000, 975, 950, 925, 900, 850, 800, 700, 600, 500],
    )
    download_era5(request, dest)
    print(f"ERA5 fixture saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def _download_satellite_fixture(
    satellite: str,
    dest: Path,
    *,
    reference_date: str = _REFERENCE_DATE,
) -> None:
    """Download the nearest granule for *satellite* ('oco2' or 'oco3')."""
    from oco_viz.data.oco import (  # noqa: PLC0415
        SATELLITE_COLLECTION_IDS,
        download_granule,
        find_nearest_passes,
        granule_download_urls,
        search_granules,
    )

    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        print("ERROR: Set EARTHDATA_TOKEN environment variable")
        sys.exit(1)

    label = satellite.upper()
    print(f"Finding nearest {label} pass to {reference_date} over Secunda...")
    passes = find_nearest_passes(
        _SECUNDA_LAT,
        _SECUNDA_LON,
        reference_date,
        radius_km=50.0,
        search_window_days=30,
        satellites=(satellite,),
    )
    if not passes:
        print(f"ERROR: No {label} passes found")
        sys.exit(1)

    best = passes[0]
    print(f"Closest pass: {best['date']} ({best['days_from_target']:+d} days) — {best['title']}")

    # Search for that specific date to get the download URL
    entries = search_granules(
        best["date"],
        best["date"],
        collection_id=SATELLITE_COLLECTION_IDS[satellite],
    )
    urls = granule_download_urls(entries)
    if not urls:
        print(f"ERROR: No download URLs found for {label} on {best['date']}")
        sys.exit(1)

    print(f"Downloading: {urls[0]}")
    download_granule(urls[0], dest, token=token)
    print(f"{label} fixture saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def download_oco2_fixture(dest: Path) -> None:
    """Download the nearest OCO-2 L2 Lite granule for Secunda."""
    _download_satellite_fixture("oco2", dest)


def download_oco3_fixture(dest: Path) -> None:
    """Download the nearest OCO-3 L2 Lite granule for Secunda."""
    _download_satellite_fixture("oco3", dest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download test fixtures")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--era5-only", action="store_true", help="Download ERA5 only")
    group.add_argument("--oco3-only", action="store_true", help="Download OCO-3 only")
    group.add_argument("--oco2-only", action="store_true", help="Download OCO-2 only")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Single date override (YYYY-MM-DD); default downloads both pass dates",
    )
    args = parser.parse_args()

    fixtures_dir = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    dates = [args.date] if args.date else _PASS_DATES

    if args.era5_only:
        for d in dates:
            download_era5_fixture(fixtures_dir / f"era5_secunda_{d}.nc", d)
    elif args.oco3_only:
        download_oco3_fixture(fixtures_dir / "oco3_secunda_2025-10-26.nc4")
    elif args.oco2_only:
        download_oco2_fixture(fixtures_dir / "oco2_secunda_2025-10-13.nc4")
    else:
        # Download everything: ERA5 for both dates, OCO-2 + OCO-3
        for d in dates:
            download_era5_fixture(fixtures_dir / f"era5_secunda_{d}.nc", d)
        download_oco3_fixture(fixtures_dir / "oco3_secunda_2025-10-26.nc4")
        download_oco2_fixture(fixtures_dir / "oco2_secunda_2025-10-13.nc4")

    print("Done!")


if __name__ == "__main__":
    main()
