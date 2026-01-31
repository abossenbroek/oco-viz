"""Diagnostic inspector for OCO-3 L2 Lite NetCDF4 files."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr

_DEFAULT_PATH = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "oco3_sample.nc4"

# Secunda facility coordinates
_SECUNDA_LAT = -26.52
_SECUNDA_LON = 29.17
_DEFAULT_RADIUS_DEG = 2.0


def _section_metadata(ds: xr.Dataset, path: Path) -> None:
    """Section 1: File metadata."""
    print("=" * 60)
    print("1. FILE METADATA")
    print("=" * 60)
    print(f"  Path:       {path}")
    print(f"  Size:       {path.stat().st_size / 1024 / 1024:.2f} MB")
    attrs = ds.attrs
    for key in ("title", "Sensor", "Platform", "creation_date", "L2FullPhysicsExeVersion"):
        print(f"  {key}: {attrs.get(key, 'N/A')}")
    print()


def _section_dims(ds: xr.Dataset) -> None:
    """Section 2: Dimensions."""
    print("=" * 60)
    print("2. DIMENSIONS")
    print("=" * 60)
    for name, size in ds.sizes.items():
        print(f"  {name:30s} {size}")
    print()


def _section_temporal(ds: xr.Dataset) -> None:
    """Section 3: Temporal coverage."""
    print("=" * 60)
    print("3. TEMPORAL COVERAGE")
    print("=" * 60)
    if "time" in ds:
        t = ds["time"].values
        print(f"  Min time:       {np.nanmin(t)}")
        print(f"  Max time:       {np.nanmax(t)}")
    if "date" in ds:
        dates = ds["date"].values
        unique_count = len(np.unique(dates[~np.isnan(dates)])) if np.issubdtype(
            dates.dtype, np.floating
        ) else len(np.unique(dates))
        print(f"  Unique dates:   {unique_count}")
    print()


def _section_spatial(ds: xr.Dataset) -> None:
    """Section 4: Spatial coverage."""
    print("=" * 60)
    print("4. SPATIAL COVERAGE")
    print("=" * 60)
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    print(f"  Latitude:   [{lat.min():.4f}, {lat.max():.4f}]")
    print(f"  Longitude:  [{lon.min():.4f}, {lon.max():.4f}]")
    print(f"  Soundings:  {len(lat)}")
    print()
    print("  Latitude-band histogram (10-deg bins):")
    edges = np.arange(-90, 100, 10)
    counts, _ = np.histogram(lat, bins=edges)
    for i, count in enumerate(counts):
        if count > 0:
            print(f"    [{edges[i]:+6.0f}, {edges[i + 1]:+6.0f}): {count:>6d}")
    print()


def _section_secunda(ds: xr.Dataset, radius_deg: float) -> None:
    """Section 5: Secunda focus."""
    print("=" * 60)
    print(f"5. SECUNDA FOCUS (radius={radius_deg} deg)")
    print("=" * 60)
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    mask = (np.abs(lat - _SECUNDA_LAT) < radius_deg) & (
        np.abs(lon - _SECUNDA_LON) < radius_deg
    )
    n = mask.sum()
    print(f"  Soundings within radius: {n}")
    if n > 0:
        sub_lat = lat[mask]
        sub_lon = lon[mask]
        sub_xco2 = ds["xco2"].values[mask]
        print(f"  Latitude:  [{sub_lat.min():.4f}, {sub_lat.max():.4f}]")
        print(f"  Longitude: [{sub_lon.min():.4f}, {sub_lon.max():.4f}]")
        print(f"  XCO2:      min={sub_xco2.min():.2f} max={sub_xco2.max():.2f} "
              f"mean={sub_xco2.mean():.2f}")
    else:
        print("  No soundings in this region.")
    print()


def _section_xco2(ds: xr.Dataset) -> None:
    """Section 6: XCO2 statistics."""
    print("=" * 60)
    print("6. XCO2 STATISTICS")
    print("=" * 60)
    xco2 = ds["xco2"].values
    valid = xco2[~np.isnan(xco2)]
    print(f"  All soundings (n={len(valid)}):")
    print(f"    min={valid.min():.2f}  max={valid.max():.2f}  "
          f"mean={valid.mean():.2f}  std={valid.std():.2f}")
    pcts = np.percentile(valid, [5, 25, 50, 75, 95])
    print(f"    P5={pcts[0]:.2f}  P25={pcts[1]:.2f}  P50={pcts[2]:.2f}  "
          f"P75={pcts[3]:.2f}  P95={pcts[4]:.2f}")

    if "xco2_quality_flag" in ds:
        qf = ds["xco2_quality_flag"].values
        good_mask = qf == 0
        good_xco2 = xco2[good_mask & ~np.isnan(xco2)]
        if len(good_xco2) > 0:
            print(f"  Quality-filtered (n={len(good_xco2)}):")
            print(f"    min={good_xco2.min():.2f}  max={good_xco2.max():.2f}  "
                  f"mean={good_xco2.mean():.2f}  std={good_xco2.std():.2f}")
            pcts2 = np.percentile(good_xco2, [5, 25, 50, 75, 95])
            print(f"    P5={pcts2[0]:.2f}  P25={pcts2[1]:.2f}  P50={pcts2[2]:.2f}  "
                  f"P75={pcts2[3]:.2f}  P95={pcts2[4]:.2f}")
    print()


def _section_quality_flags(ds: xr.Dataset) -> None:
    """Section 7: Quality flags."""
    print("=" * 60)
    print("7. QUALITY FLAGS")
    print("=" * 60)
    if "xco2_quality_flag" not in ds:
        print("  xco2_quality_flag not found.")
        print()
        return
    qf = ds["xco2_quality_flag"].values
    unique, counts = np.unique(qf[~np.isnan(qf)], return_counts=True)
    total = counts.sum()
    for val, cnt in zip(unique, counts):
        print(f"  flag={val:.0f}: {cnt:>6d} ({100 * cnt / total:.1f}%)")
    good = counts[unique == 0].sum() if 0 in unique else 0
    print(f"  Good (flag==0): {good}/{total} = {100 * good / total:.1f}%")
    print()


def _section_all_vars(ds: xr.Dataset) -> None:
    """Section 8: All variables."""
    print("=" * 60)
    print("8. ALL VARIABLES")
    print("=" * 60)
    for name in sorted(str(v) for v in ds.data_vars):
        var = ds[name]
        info = f"  {name:35s} shape={str(var.shape):25s} dtype={var.dtype}"
        if np.issubdtype(var.dtype, np.number):
            vals = var.values
            valid = vals[~np.isnan(vals)] if np.issubdtype(var.dtype, np.floating) else vals
            if len(valid) > 0:
                info += f"  min={np.min(valid):.4g}  max={np.max(valid):.4g}  mean={np.mean(valid):.4g}"
        else:
            flat = var.values.flat
            sample = flat[0] if len(flat) > 0 else "N/A"
            info += f"  sample={sample}"
        print(info)
    print()


def _section_coords(ds: xr.Dataset) -> None:
    """Section 9: Coordinates."""
    print("=" * 60)
    print("9. COORDINATES")
    print("=" * 60)
    for name in sorted(str(c) for c in ds.coords):
        co = ds.coords[name]
        print(f"  {name:30s} shape={str(co.shape):15s} dtype={co.dtype}")
        if co.size <= 20:
            print(f"    values: {co.values}")
        else:
            print(f"    range: [{co.values.min()} .. {co.values.max()}]")
    print()


def main() -> None:
    """Run the OCO-3 file inspector."""
    parser = argparse.ArgumentParser(description="Inspect OCO-3 L2 Lite NetCDF4 files")
    parser.add_argument(
        "path",
        nargs="?",
        default=str(_DEFAULT_PATH),
        help="Path to the .nc4 file (default: tests/fixtures/oco3_sample.nc4)",
    )
    parser.add_argument(
        "--secunda",
        action="store_true",
        help="Show Secunda-region detail (section 5)",
    )
    parser.add_argument(
        "--secunda-radius",
        type=float,
        default=_DEFAULT_RADIUS_DEG,
        help="Radius in degrees for Secunda search (default: 2.0)",
    )
    parser.add_argument(
        "--all-vars",
        action="store_true",
        help="Show all variables and coordinates (sections 8-9)",
    )
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        raise SystemExit(1)

    ds: xr.Dataset = xr.open_dataset(str(path))

    # Default sections: 1-4, 6-7
    _section_metadata(ds, path)
    _section_dims(ds)
    _section_temporal(ds)
    _section_spatial(ds)
    _section_xco2(ds)
    _section_quality_flags(ds)

    if args.secunda:
        _section_secunda(ds, args.secunda_radius)

    if args.all_vars:
        _section_all_vars(ds)
        _section_coords(ds)

    ds.close()


if __name__ == "__main__":
    main()
