"""Data pipeline orchestrator wiring ERA5 winds, satellite overlay, and plume generation."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from oco_viz.data.era5 import load_era5_winds
from oco_viz.data.oco import load_and_grid_granules
from oco_viz.data.zarr_store import write_zarr
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_sequence, generate_timestep
from oco_viz.plume.turbulent import generate_turbulent_sequence

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


def attach_satellite_overlay(
    ds: xr.Dataset,
    granule_paths: list[Path],
    domain: DomainConfig,
    grid: GridConfig,
) -> xr.Dataset:
    """Add xco2_observed variable from OCO-2/3 data to an existing dataset."""
    sat_ds = load_and_grid_granules(granule_paths, domain, grid)
    ds["xco2_observed"] = sat_ds["xco2_observed"]
    return ds


# Keep old name as alias for backward compatibility
attach_oco3_overlay = attach_satellite_overlay


def run_data_pipeline(
    config: AppConfig,
    *,
    mode: str = "gaussian",
    era5_path: Path | None = None,
    oco3_paths: list[Path] | None = None,
    num_timesteps: int = 24,
    output_zarr: Path | None = None,
) -> xr.Dataset:
    """Main data pipeline entry point.

    Modes:
    - ``gaussian``: Gaussian plume only (default).
    - ``turbulent``: Gaussian plume with turbulent noise.
    - ``wind``: ERA5 wind-driven plume (requires *era5_path*).
    - ``advected``: Semi-Lagrangian advection with ERA5 winds (requires *era5_path*).

    If *oco3_paths* is provided, attaches XCO2 observation overlay.
    If *output_zarr* is provided, writes the result to a Zarr store.
    """
    if mode == "turbulent":
        ds = generate_turbulent_sequence(
            config.plume,
            config.grid,
            config.turbulence,
            num_timesteps,
        )
    elif mode == "advected":
        if era5_path is None:
            msg = "mode='advected' requires era5_path"
            raise ValueError(msg)
        wind_ds = load_era5_winds(era5_path, config.data_source.domain, config.grid)
        ds = advect_sequence(
            config.plume,
            config.grid,
            wind_ds,
            config.turbulence,
            num_timesteps,
            adv_cfg=config.advection,
        )
    elif mode == "wind":
        if era5_path is None:
            msg = "mode='wind' requires era5_path"
            raise ValueError(msg)
        ds = build_wind_driven_plume(config, era5_path, num_timesteps)
    else:
        ds = generate_sequence(config.plume, config.grid, num_timesteps)

    if oco3_paths:
        ds = attach_satellite_overlay(ds, oco3_paths, config.data_source.domain, config.grid)

    if output_zarr is not None:
        _write_pipeline_zarr(ds, output_zarr)

    return ds


def _write_pipeline_zarr(ds: xr.Dataset, path: Path) -> None:
    """Write pipeline output to Zarr with two-phase validation.

    Phase 1: write ``concentration`` via :func:`write_zarr`, which validates
    the required variable name, dimensions ``(time, z, y, x)``, and dtype.

    Phase 2: append any auxiliary variables (e.g. ``u_wind``, ``v_wind``,
    ``xco2_observed``) directly via xarray's ``to_zarr`` in append mode,
    bypassing the strict validation since these are supplementary data.
    """
    # write_zarr validates 'concentration' exists — strip auxiliary vars for validation,
    # then write the full dataset
    conc_ds = ds[["concentration"]].copy()

    # Validate via write_zarr (which checks dims/dtype)
    write_zarr(conc_ds, path)

    # Now append auxiliary variables if present
    aux_vars = [v for v in ds.data_vars if v != "concentration"]
    if aux_vars:
        ds[aux_vars].to_zarr(str(path), mode="a")
