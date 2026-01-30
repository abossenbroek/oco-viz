"""Run HYSPLIT dispersion model or fall back to Gaussian + ERA5 winds."""

from __future__ import annotations

import importlib
import shutil
import subprocess
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    from pathlib import Path

    from oco_viz.config.schema import AppConfig


# Sasol Secunda source coordinates
_SOURCE_LAT = -26.52
_SOURCE_LON = 29.17
_SOURCE_ALT_M = 200.0  # stack height


def generate_control_file(
    output_path: Path,
    *,
    start_year: int,
    start_month: int,
    start_day: int,
    start_hour: int = 0,
    run_hours: int = 48,
    source_lat: float = _SOURCE_LAT,
    source_lon: float = _SOURCE_LON,
    source_alt: float = _SOURCE_ALT_M,
) -> Path:
    """Generate a HYSPLIT CONTROL file for forward dispersion from Secunda."""
    lines = [
        f"{start_year:02d} {start_month:02d} {start_day:02d} {start_hour:02d}",
        "1",  # number of source locations
        f"{source_lat:.4f} {source_lon:.4f} {source_alt:.1f}",
        str(run_hours),
        "0",  # vertical motion method (data)
        "10000.0",  # top of model domain (m)
        "1",  # number of met data files
        "./",  # met data directory
        "gdas1.jan20.w1",  # placeholder met file
        "1",  # number of pollutant species
        "CO2",
        "1000.0",  # emission rate (arbitrary units)
        "24.0",  # emission duration (hours)
        "00 00 00 00 00",  # release start
        "1",  # number of grids
        "0.0 0.0",  # center of grid (relative)
        "0.05 0.05",  # grid spacing (degrees)
        "100.0 100.0",  # grid span
        "./",  # output directory
        "cdump",  # output filename
        "1",  # number of vertical levels
        "10000",  # top of output grid
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n")
    return output_path


def run_hysplit(control_path: Path, *, hycs_std: str = "hycs_std") -> Path:
    """Run HYSPLIT using the given CONTROL file.

    Returns path to the cdump output file.
    """
    if not shutil.which(hycs_std):
        msg = f"HYSPLIT executable '{hycs_std}' not found on PATH"
        raise FileNotFoundError(msg)

    work_dir = control_path.parent
    subprocess.run(  # noqa: S603
        [hycs_std],
        cwd=str(work_dir),
        check=True,
        capture_output=True,
    )
    cdump = work_dir / "cdump"
    if not cdump.exists():
        msg = f"HYSPLIT did not produce output: {cdump}"
        raise FileNotFoundError(msg)
    return cdump


def parse_cdump_to_dataset(
    cdump_path: Path,
    grid_shape: tuple[int, int, int],
) -> xr.Dataset:
    """Parse HYSPLIT cdump binary output to xr.Dataset matching Zarr contract.

    This is a simplified parser — real cdump parsing depends on the
    HYSPLIT binary format. For production use, consider ``pysplit`` or
    HYSPLIT's own conversion utilities.
    """
    # Placeholder: read raw binary as flat float32 and reshape
    raw = np.fromfile(str(cdump_path), dtype=np.float32)
    nz, ny, nx = grid_shape
    n_timesteps = max(1, raw.size // (nz * ny * nx))
    expected = n_timesteps * nz * ny * nx
    if raw.size < expected:
        padded = np.zeros(expected, dtype=np.float32)
        padded[: raw.size] = raw
        raw = padded
    else:
        raw = raw[:expected]

    data = raw.reshape(n_timesteps, nz, ny, nx)

    return xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), data)},
        coords={
            "time": np.arange(n_timesteps),
            "z": np.arange(nz),
            "y": np.arange(ny),
            "x": np.arange(nx),
        },
    )


def hysplit_or_gaussian(
    config: AppConfig,
    num_timesteps: int,
    *,
    control_path: Path | None = None,
) -> xr.Dataset:
    """Try HYSPLIT; fall back to Gaussian plume with ERA5 winds if unavailable."""
    if control_path and shutil.which("hycs_std"):
        cdump = run_hysplit(control_path)
        return parse_cdump_to_dataset(cdump, config.grid.shape)

    # Fallback: Gaussian plume generator
    gaussian = importlib.import_module("oco_viz.plume.gaussian")
    result: xr.Dataset = gaussian.generate_sequence(
        config.plume, config.grid, num_timesteps=num_timesteps,
    )
    return result
