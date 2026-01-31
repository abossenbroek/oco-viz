"""Download test fixtures for Wave 2 data pipeline tests.

Requires:
- CDS API credentials (~/.cdsapirc) for ERA5 download
- NASA Earthdata token (EARTHDATA_TOKEN env var) for OCO-3 download

Usage:
    python scripts/download_fixtures.py [--era5-only | --oco3-only]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add src to path so we can import oco_viz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def download_era5_fixture(dest: Path) -> None:
    """Download ERA5 sample: 1 day over Sasol Secunda bbox."""
    from oco_viz.data.era5 import build_cds_request, download_era5

    print(f"Downloading ERA5 fixture to {dest}")
    request = build_cds_request(
        "2024-01-15",
        lat=-26.5,
        lon=29.2,
        pressure_levels=[1000, 975, 950, 925, 900, 850, 800, 700, 600, 500],
    )
    download_era5(request, dest)
    print(f"ERA5 fixture saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def download_oco3_fixture(dest: Path) -> None:
    """Download OCO-3 L2 Lite granule covering Secunda."""
    from oco_viz.data.oco3 import download_granule, granule_download_urls, search_granules

    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        print("ERROR: Set EARTHDATA_TOKEN environment variable")
        sys.exit(1)

    print("Searching for OCO-3 granules over Secunda...")
    entries = search_granules("2025-10-01", "2025-12-31")
    if not entries:
        print("ERROR: No granules found")
        sys.exit(1)

    urls = granule_download_urls(entries)
    if not urls:
        print("ERROR: No download URLs found")
        sys.exit(1)

    print(f"Found {len(urls)} granules, downloading first: {urls[0]}")
    download_granule(urls[0], dest, token=token)
    print(f"OCO-3 fixture saved: {dest} ({dest.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download test fixtures for Wave 2")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--era5-only", action="store_true", help="Download ERA5 only")
    group.add_argument("--oco3-only", action="store_true", help="Download OCO-3 only")
    args = parser.parse_args()

    fixtures_dir = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    fixtures_dir.mkdir(parents=True, exist_ok=True)

    if not args.oco3_only:
        download_era5_fixture(fixtures_dir / "era5_secunda_sample.nc")

    if not args.era5_only:
        download_oco3_fixture(fixtures_dir / "oco3_sample.nc4")

    print("Done!")


if __name__ == "__main__":
    main()
