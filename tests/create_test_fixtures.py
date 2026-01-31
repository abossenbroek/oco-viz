"""Create synthetic test fixtures for ERA5 and OCO-3 data.

Run this script to generate test fixtures when real data is unavailable.
These fixtures have the same structure as real data but contain synthetic values.

Usage:
    python tests/create_test_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr


def create_era5_fixture(dest: Path) -> None:
    """Create a synthetic ERA5 NetCDF matching real ERA5 structure."""
    n_times = 24
    pressure_levels = [1000, 975, 950, 925, 900, 850, 800, 700, 600, 500]
    n_levels = len(pressure_levels)

    # Small spatial grid around Secunda (-26.5, 29.2)
    lats = np.arange(-27.0, -26.0, 0.25)  # 4 points
    lons = np.arange(28.7, 29.7, 0.25)  # 4 points
    times = np.arange(n_times)

    rng = np.random.default_rng(42)

    # Wind components: u ~ 3-8 m/s, v ~ -3 to 3 m/s (typical boundary layer)
    u_data = rng.uniform(3.0, 8.0, (n_times, n_levels, len(lats), len(lons))).astype(np.float32)
    v_data = rng.uniform(-3.0, 3.0, (n_times, n_levels, len(lats), len(lons))).astype(np.float32)

    ds = xr.Dataset(
        {
            "u": (["time", "pressure_level", "latitude", "longitude"], u_data),
            "v": (["time", "pressure_level", "latitude", "longitude"], v_data),
        },
        coords={
            "time": times,
            "pressure_level": pressure_levels,
            "latitude": lats,
            "longitude": lons,
        },
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(str(dest))
    print(f"Created ERA5 fixture: {dest} ({dest.stat().st_size / 1024:.0f} KB)")


def create_oco3_fixture(dest: Path) -> None:
    """Create a synthetic OCO-3 L2 Lite NetCDF4 matching real structure."""
    n_soundings = 500
    rng = np.random.default_rng(123)

    # Soundings scattered around Secunda region
    lats = rng.uniform(-27.0, -26.0, n_soundings).astype(np.float32)
    lons = rng.uniform(28.5, 30.0, n_soundings).astype(np.float32)

    # XCO2 values in physical range (~405-425 ppm, with plume enhancement)
    xco2 = rng.normal(415.0, 5.0, n_soundings).astype(np.float32)

    # Quality flag: 0 = good, 1 = bad; ~80% good
    quality_flag = rng.choice([0, 1], size=n_soundings, p=[0.8, 0.2]).astype(np.int8)

    # Sounding ID
    sounding_id = np.arange(n_soundings, dtype=np.int64)

    ds = xr.Dataset(
        {
            "xco2": ("sounding_id", xco2),
            "latitude": ("sounding_id", lats),
            "longitude": ("sounding_id", lons),
            "xco2_quality_flag": ("sounding_id", quality_flag),
        },
        coords={"sounding_id": sounding_id},
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(str(dest))
    print(f"Created OCO-3 fixture: {dest} ({dest.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    fixtures_dir = Path(__file__).parent / "fixtures"
    create_era5_fixture(fixtures_dir / "era5_secunda_sample.nc")
    create_oco3_fixture(fixtures_dir / "oco3_sample.nc4")
