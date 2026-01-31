"""Data pipeline orchestrator wiring ERA5 winds, OCO-3 overlay, and plume generation."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from oco_viz.data.era5 import load_era5_winds
from oco_viz.data.oco3 import load_and_grid_granules
from oco_viz.data.zarr_store import write_zarr
from oco_viz.plume.gaussian import generate_sequence, generate_timestep

if TYPE_CHECKING:
    from pathlib import Path

    from oco_viz.config.schema import AppConfig, DomainConfig, GridConfig


def build_wind_driven_plume(
    config: AppConfig,
    era5_path: Path,
    num_timesteps: int,
) -> xr.Dataset:
    """Load ERA5 winds and drive Gaussian plume generation with real wind data.

    For each timestep, extracts spatially-averaged wind speed and direction
    from the ERA5 data and generates a plume frame using those parameters.

    Returns xr.Dataset with {concentration, u_wind, v_wind} on dims (time, z, y, x).
    """
    grid = config.grid
    domain = config.data_source.domain

    # Load ERA5 wind fields
    wind_ds = load_era5_winds(era5_path, domain, grid)
    n_era5_times = wind_ds.sizes["time"]

    frames = []
    u_wind_out = []
    v_wind_out = []

    for t in range(num_timesteps):
        # Cycle through ERA5 timesteps if we need more than available
        era5_t = t % n_era5_times
        u_field = wind_ds["u_wind"].isel(time=era5_t).values
        v_field = wind_ds["v_wind"].isel(time=era5_t).values

        # Spatial mean wind for plume driving
        u_mean = float(np.nanmean(u_field))
        v_mean = float(np.nanmean(v_field))
        speed = math.sqrt(u_mean**2 + v_mean**2)
        # Meteorological direction (from which wind blows)
        direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

        # Override plume config with real wind
        plume_cfg = config.plume.model_copy(
            update={"wind_speed": max(speed, 0.1), "wind_direction": direction}
        )

        frame = generate_timestep(plume_cfg, grid, t)
        frames.append(frame)
        u_wind_out.append(u_field)
        v_wind_out.append(v_field)

    conc_data = np.stack(frames, axis=0)
    u_data = np.stack(u_wind_out, axis=0)
    v_data = np.stack(v_wind_out, axis=0)

    nz, ny, nx = grid.shape
    return xr.Dataset(
        {
            "concentration": (["time", "z", "y", "x"], conc_data),
            "u_wind": (["time", "z", "y", "x"], u_data),
            "v_wind": (["time", "z", "y", "x"], v_data),
        },
        coords={
            "time": np.arange(num_timesteps),
            "z": np.arange(nz) * grid.dz,
            "y": np.arange(ny) * grid.dy,
            "x": np.arange(nx) * grid.dx,
        },
    )


def attach_oco3_overlay(
    ds: xr.Dataset,
    oco3_paths: list[Path],
    domain: DomainConfig,
    grid: GridConfig,
) -> xr.Dataset:
    """Add xco2_observed variable from OCO-3 data to an existing dataset."""
    oco3_ds = load_and_grid_granules(oco3_paths, domain, grid)
    ds["xco2_observed"] = oco3_ds["xco2_observed"]
    return ds


def run_data_pipeline(
    config: AppConfig,
    *,
    era5_path: Path | None = None,
    oco3_paths: list[Path] | None = None,
    num_timesteps: int = 24,
    output_zarr: Path | None = None,
) -> xr.Dataset:
    """Main data pipeline entry point.

    If *era5_path* is provided, drives plume with real ERA5 wind data.
    Otherwise, falls back to the existing Gaussian plume generator.
    If *oco3_paths* is provided, attaches XCO2 observation overlay.
    If *output_zarr* is provided, writes the result to a Zarr store.
    """
    if era5_path is not None:
        ds = build_wind_driven_plume(config, era5_path, num_timesteps)
    else:
        ds = generate_sequence(config.plume, config.grid, num_timesteps)

    if oco3_paths:
        ds = attach_oco3_overlay(ds, oco3_paths, config.data_source.domain, config.grid)

    if output_zarr is not None:
        _write_pipeline_zarr(ds, output_zarr)

    return ds


def _write_pipeline_zarr(ds: xr.Dataset, path: Path) -> None:
    """Write pipeline output to Zarr, handling auxiliary variables."""
    # write_zarr validates 'concentration' exists — strip auxiliary vars for validation,
    # then write the full dataset
    conc_ds = ds[["concentration"]].copy()

    # Validate via write_zarr (which checks dims/dtype)
    write_zarr(conc_ds, path)

    # Now append auxiliary variables if present
    aux_vars = [v for v in ds.data_vars if v != "concentration"]
    if aux_vars:
        ds[aux_vars].to_zarr(str(path), mode="a")
