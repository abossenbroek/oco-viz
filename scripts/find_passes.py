"""Find nearest OCO-2/OCO-3 overpasses for a given location and date.

Usage:
    pixi run python scripts/find_passes.py [--lat LAT] [--lon LON] [--date DATE] \
        [--radius-km 50] [--window-days 90] [--satellites oco2,oco3]
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

# Add src to path so we can import oco_viz
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find nearest OCO-2/OCO-3 satellite overpasses",
    )
    parser.add_argument("--lat", type=float, default=-26.52, help="Latitude (default: Secunda)")
    parser.add_argument("--lon", type=float, default=29.17, help="Longitude (default: Secunda)")
    parser.add_argument(
        "--date",
        type=str,
        default=dt.datetime.now(tz=dt.UTC).date().isoformat(),
        help="Target date YYYY-MM-DD (default: today)",
    )
    parser.add_argument("--radius-km", type=float, default=50.0, help="Search radius in km")
    parser.add_argument("--window-days", type=int, default=90, help="Search window in days")
    parser.add_argument(
        "--satellites",
        type=str,
        default="oco2,oco3",
        help="Comma-separated satellite list (default: oco2,oco3)",
    )
    args = parser.parse_args()

    satellites = tuple(s.strip() for s in args.satellites.split(","))

    from oco_viz.data.oco import find_nearest_passes  # noqa: PLC0415

    print(
        f"Searching for passes near ({args.lat}, {args.lon}) "
        f"within {args.window_days} days of {args.date}..."
    )
    print(f"Satellites: {', '.join(satellites)}")
    print(f"Search radius: {args.radius_km} km")
    print()

    passes = find_nearest_passes(
        args.lat,
        args.lon,
        args.date,
        radius_km=args.radius_km,
        search_window_days=args.window_days,
        satellites=satellites,
    )

    if not passes:
        print("No passes found.")
        sys.exit(1)

    # Print table
    print(f"{'Satellite':<10} {'Date':<12} {'Days from target':>16}  {'Title'}")
    print("-" * 72)
    for p in passes:
        sign = "+" if p["days_from_target"] >= 0 else ""
        print(
            f"{p['satellite']:<10} {p['date']:<12} {sign}{p['days_from_target']:>15}  {p['title']}"
        )

    # Summary
    print()
    print(f"Total passes found: {len(passes)}")
    for sat in satellites:
        count = sum(1 for p in passes if p["satellite"] == sat)
        if count:
            print(f"  {sat}: {count}")


if __name__ == "__main__":
    main()
