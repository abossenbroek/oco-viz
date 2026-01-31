"""Find and download OCO-2/OCO-3 granules with actual soundings over Secunda.

CMR spatial search matches every daily L2 Lite file because the granule-level
bounding box covers the entire globe.  This script downloads candidates one at
a time, checks whether any soundings fall within *radius_deg* of Secunda, and
keeps the first match.

Requires:
    EARTHDATA_TOKEN environment variable (Bearer token for NASA Earthdata).

Usage:
    pixi run find-secunda-granule --satellite oco3
    pixi run find-secunda-granule --satellite oco2
    pixi run find-secunda-granule --satellite oco3 --start 2025-09-01 --end 2025-10-31
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import xarray as xr

# Add src to path so we can import oco_viz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

SECUNDA_LAT = -26.52
SECUNDA_LON = 29.17


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find OCO-2/OCO-3 granule with soundings over Secunda",
    )
    parser.add_argument(
        "--satellite",
        choices=["oco2", "oco3"],
        default="oco3",
        help="Satellite to search (default: oco3)",
    )
    parser.add_argument("--start", default="2025-09-15", help="Search start date")
    parser.add_argument("--end", default="2025-10-31", help="Search end date")
    parser.add_argument(
        "--radius-deg",
        type=float,
        default=1.0,
        help="Max distance in degrees from Secunda (default: 1.0 ~ 110 km)",
    )
    parser.add_argument(
        "--dest-dir",
        type=str,
        default="tests/fixtures",
        help="Directory to save the matching granule",
    )
    parser.add_argument(
        "--max-tries",
        type=int,
        default=30,
        help="Max granules to download before giving up",
    )
    parser.add_argument(
        "--require-good-quality",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Require xco2_quality_flag == 0 for near-Secunda soundings (default: True)",
    )
    parser.add_argument(
        "--min-good",
        type=int,
        default=1,
        help="Minimum good-quality soundings near Secunda to accept (default: 1)",
    )
    args = parser.parse_args()

    from oco_viz.data.oco import (  # noqa: PLC0415
        SATELLITE_COLLECTION_IDS,
        download_granule,
        granule_download_urls,
        search_granules,
    )

    token = os.environ.get("EARTHDATA_TOKEN")
    if not token:
        print("ERROR: Set EARTHDATA_TOKEN environment variable")
        sys.exit(1)

    label = args.satellite.upper()
    collection_id = SATELLITE_COLLECTION_IDS[args.satellite]

    print(f"Searching CMR for {label} granules ({args.start} to {args.end})...")
    entries = search_granules(
        args.start,
        args.end,
        collection_id=collection_id,
        page_size=args.max_tries,
    )
    urls = granule_download_urls(entries)
    print(f"Found {len(urls)} candidate granules")

    if not urls:
        print("No granules found in date range.")
        sys.exit(1)

    dest_dir = Path(args.dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = dest_dir / f".{args.satellite}_candidate.nc4"

    for i, url in enumerate(urls[: args.max_tries]):
        date = entries[i].get("time_start", "?")[:10]
        print(f"\n[{i + 1}/{min(len(urls), args.max_tries)}] {date}: downloading...", end=" ")

        download_granule(url, tmp_path, token=token)
        size_mb = tmp_path.stat().st_size / 1e6

        ds = xr.open_dataset(str(tmp_path))
        lats = ds["latitude"].values
        lons = ds["longitude"].values

        near = (
            (np.abs(lats - SECUNDA_LAT) < args.radius_deg)
            & (np.abs(lons - SECUNDA_LON) < args.radius_deg)
        )
        n_near = int(np.sum(near))

        n_good = n_near
        if args.require_good_quality and "xco2_quality_flag" in ds:
            qf = ds["xco2_quality_flag"].values
            good = near & (qf == 0)
            n_good = int(np.sum(good))

        ds.close()

        quality_info = f", {n_good} good quality" if args.require_good_quality else ""
        print(f"{size_mb:.1f} MB, {len(lats)} soundings, {n_near} near Secunda{quality_info}")

        if n_good >= args.min_good:
            final_name = f"{args.satellite}_secunda_{date}.nc4"
            final_path = dest_dir / final_name
            tmp_path.rename(final_path)
            print(f"\nFound {n_near} soundings near Secunda ({n_good} good quality) on {date}")
            print(f"Saved: {final_path}")
            sys.exit(0)

        tmp_path.unlink()

    print(f"\nNo granules with Secunda soundings found in {args.max_tries} tries.")
    print("Try a wider date range or larger --radius-deg.")
    sys.exit(1)


if __name__ == "__main__":
    main()
