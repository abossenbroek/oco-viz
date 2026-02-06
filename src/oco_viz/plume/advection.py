"""Semi-Lagrangian advection for physically-evolving plume transport.

Provides two advection schemes:
- ``semi_lagrangian``: First-order semi-Lagrangian backtracking with trilinear
  interpolation via :class:`scipy.interpolate.RegularGridInterpolator`.
- ``maccormack``: Predictor-corrector extension that reduces numerical diffusion
  while clamping to local bounds to prevent oscillations.

Optional features:
- Briggs buoyancy-driven plume rise (vertical velocity field).
- Turbulent diffusion via curl-noise displacement of departure points.
- Per-step source injection to maintain a continuous emission.
- Mass correction to compensate for interpolation loss.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import maximum_filter, minimum_filter

from oco_viz.config.schema import AdvectionConfig
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.noise import curl_noise_3d

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import (
        GridConfig,
        PlumeConfig,
        TurbulenceConfig,
    )

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #


def _inject_source(
    conc: NDArray[np.float32],
    plume_cfg: PlumeConfig,
    grid: GridConfig,
    sigma: float,
    dt: float,
) -> NDArray[np.float32]:
    """Add source emission as Gaussian kernel at the stack location.

    Parameters
    ----------
    conc:
        Current concentration field (z, y, x).
    plume_cfg:
        Plume configuration with source coordinates and emission rate.
    grid:
        Grid configuration for cell volume.
    sigma:
        Source injection spread in grid cells.
    dt:
        Timestep in seconds (scales injected mass).

    Returns
    -------
    NDArray[np.float32]
        Updated concentration with source contribution added.

    """
    nz, ny, nx = grid.shape
    z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]

    cx = plume_cfg.source_x
    cy = plume_cfg.source_y
    cz = plume_cfg.source_z

    # Gaussian kernel centred on source (in grid-cell coordinates)
    r2 = (x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2
    kernel = np.exp(-r2 / (2.0 * sigma**2)).astype(np.float64)

    # Normalise kernel so its integral = 1
    ksum = kernel.sum()
    if ksum > 0:
        kernel /= ksum

    # Injected mass: emission_rate * dt / cell_volume
    cell_vol = grid.dx * grid.dy * grid.dz
    injected = plume_cfg.emission_rate * dt / cell_vol

    result = conc.astype(np.float64) + kernel * injected
    return cast("NDArray[np.float32]", result.astype(np.float32))


def _briggs_plume_rise(
    plume_cfg: PlumeConfig,
    adv_cfg: AdvectionConfig,
    grid: GridConfig,
    u_wind_mean: float,
) -> NDArray[np.float32]:
    """Compute vertical velocity field from Briggs buoyancy formula.

    Briggs rise: dh = 1.6 * F^(1/3) * x^(2/3) / u
    where F = buoyancy_flux, x = downwind distance, u = wind speed.

    The rise height is converted to a vertical velocity that decays
    with distance from the source.

    Parameters
    ----------
    plume_cfg:
        Plume source configuration.
    adv_cfg:
        Advection configuration (contains buoyancy_flux).
    grid:
        Grid configuration.
    u_wind_mean:
        Mean horizontal wind speed for Briggs formula.

    Returns
    -------
    NDArray[np.float32]
        Vertical velocity field (z, y, x) in grid cells per second.

    """
    nz, ny, nx = grid.shape
    w_wind = np.zeros((nz, ny, nx), dtype=np.float32)

    if adv_cfg.buoyancy_flux <= 0 or u_wind_mean <= 0:
        return w_wind

    f_val = adv_cfg.buoyancy_flux
    z_idx, y_idx, x_idx = np.mgrid[0:nz, 0:ny, 0:nx]

    # Distance from source in grid cells
    dx_src = (x_idx - plume_cfg.source_x).astype(np.float64)
    dy_src = (y_idx - plume_cfg.source_y).astype(np.float64)
    dz_src = (z_idx - plume_cfg.source_z).astype(np.float64)

    # Downwind distance in metres
    horiz_dist = np.sqrt(dx_src**2 + dy_src**2) * grid.dx
    horiz_dist = np.maximum(horiz_dist, grid.dx)  # avoid zero

    # Briggs plume rise (metres)
    dh = 1.6 * f_val ** (1.0 / 3.0) * horiz_dist ** (2.0 / 3.0) / u_wind_mean

    # Convert to vertical velocity (m/s) ~ dh / (x / u)
    travel_time = horiz_dist / u_wind_mean
    w_ms = dh / np.maximum(travel_time, 1.0)  # m/s

    # Decay with vertical distance from source
    vert_decay = np.exp(-0.5 * (dz_src / max(nz * 0.3, 1.0)) ** 2)

    # Decay with horizontal distance
    horiz_decay = np.exp(-horiz_dist / (nx * grid.dx * 0.5))

    # Convert m/s to grid-cells/s (divide by dz)
    w_grid = w_ms * vert_decay * horiz_decay / grid.dz

    return cast("NDArray[np.float32]", w_grid.astype(np.float32))


def _semi_lagrangian_step(
    conc: NDArray[np.float32],
    u_wind: NDArray[np.float32],
    v_wind: NDArray[np.float32],
    w_wind: NDArray[np.float32],
    dt: float,
    grid: GridConfig,
) -> NDArray[np.float32]:
    """First-order semi-Lagrangian advection step.

    For each grid cell, backtrack the departure point using the velocity
    field and interpolate the concentration at that point.

    Parameters
    ----------
    conc:
        Concentration field (z, y, x).
    u_wind:
        X-velocity field (z, y, x) in m/s.
    v_wind:
        Y-velocity field (z, y, x) in m/s.
    w_wind:
        Z-velocity field (z, y, x) in grid cells per second.
    dt:
        Timestep in seconds.
    grid:
        Grid configuration.

    Returns
    -------
    NDArray[np.float32]
        Advected concentration field.

    """
    nz, ny, nx = grid.shape
    z_coords = np.arange(nz, dtype=np.float64)
    y_coords = np.arange(ny, dtype=np.float64)
    x_coords = np.arange(nx, dtype=np.float64)

    interp = RegularGridInterpolator(
        (z_coords, y_coords, x_coords),
        conc.astype(np.float64),
        method="linear",
        bounds_error=False,
        fill_value=0.0,
    )

    z_grid, y_grid, x_grid = np.mgrid[0:nz, 0:ny, 0:nx]
    z_grid = z_grid.astype(np.float64)
    y_grid = y_grid.astype(np.float64)
    x_grid = x_grid.astype(np.float64)

    # Departure points: backtrack by velocity * dt (in grid coordinates)
    dep_x = x_grid - u_wind.astype(np.float64) * dt / grid.dx
    dep_y = y_grid - v_wind.astype(np.float64) * dt / grid.dy
    dep_z = z_grid - w_wind.astype(np.float64) * dt

    points = np.stack([dep_z.ravel(), dep_y.ravel(), dep_x.ravel()], axis=-1)
    result = interp(points).reshape((nz, ny, nx))

    return cast("NDArray[np.float32]", result.astype(np.float32))


def _maccormack_step(
    conc: NDArray[np.float32],
    u_wind: NDArray[np.float32],
    v_wind: NDArray[np.float32],
    w_wind: NDArray[np.float32],
    dt: float,
    grid: GridConfig,
) -> NDArray[np.float32]:
    """MacCormack predictor-corrector advection step.

    1. Forward semi-Lagrangian step (predictor).
    2. Backward semi-Lagrangian step on the predictor result.
    3. Correction: conc + 0.5 * (conc - backward).
    4. Local bounds clamping to prevent oscillations.

    Parameters
    ----------
    conc:
        Concentration field (z, y, x).
    u_wind:
        X-velocity field (z, y, x) in m/s.
    v_wind:
        Y-velocity field (z, y, x) in m/s.
    w_wind:
        Z-velocity field (z, y, x) in grid cells per second.
    dt:
        Timestep in seconds.
    grid:
        Grid configuration.

    Returns
    -------
    NDArray[np.float32]
        Advected concentration field with reduced numerical diffusion.

    """
    # Forward step (predictor)
    forward = _semi_lagrangian_step(conc, u_wind, v_wind, w_wind, dt, grid)

    # Backward step (reverse velocity on forward result)
    neg_u = -u_wind
    neg_v = -v_wind
    neg_w = -w_wind
    backward = _semi_lagrangian_step(forward, neg_u, neg_v, neg_w, dt, grid)

    # Correction
    corrected = forward.astype(np.float64) + 0.5 * (
        conc.astype(np.float64) - backward.astype(np.float64)
    )

    # Local bounds clamping: clip to [local_min, local_max] of neighbours
    local_min = minimum_filter(conc.astype(np.float64), size=3, mode="constant", cval=0.0)
    local_max = maximum_filter(conc.astype(np.float64), size=3, mode="constant", cval=0.0)

    corrected = np.clip(corrected, local_min, local_max)

    return corrected.astype(np.float32)


# ------------------------------------------------------------------ #
# Public API helpers (reduce advect_step complexity)
# ------------------------------------------------------------------ #


def _apply_turbulent_curl(
    u_wind: NDArray[np.float32],
    v_wind: NDArray[np.float32],
    w_wind: NDArray[np.float32],
    turb_cfg: TurbulenceConfig,
    grid: GridConfig,
    t_idx: int,
    dt: float,
) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
    """Add curl-noise turbulent diffusion to the velocity fields."""
    seed_offset = int(t_idx * turb_cfg.temporal_speed * 1000)
    curl_dx, curl_dy, curl_dz = curl_noise_3d(
        grid.shape,
        octaves=min(turb_cfg.octaves, 4),
        lacunarity=turb_cfg.lacunarity,
        gain=turb_cfg.gain,
        seed=turb_cfg.seed + seed_offset,
    )
    curl_scale = turb_cfg.curl_strength * turb_cfg.amplitude
    u_out = u_wind + curl_dx * float(curl_scale * grid.dx / max(dt, 1.0))
    v_out = v_wind + curl_dy * float(curl_scale * grid.dy / max(dt, 1.0))
    w_out = w_wind + curl_dz * float(curl_scale)
    return u_out, v_out, w_out


def _apply_mass_correction(
    result: NDArray[np.float32],
    mass_before: float,
) -> NDArray[np.float32]:
    """Rescale result so total mass matches *mass_before*."""
    mass_after = float(result.sum())
    if mass_after > 0:
        correction = min(max(mass_before / mass_after, 0.5), 2.0)
        return (result.astype(np.float64) * correction).astype(np.float32)
    return result


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #


def advect_step(
    conc: NDArray[np.float32],
    u_wind: NDArray[np.float32],
    v_wind: NDArray[np.float32],
    dt: float,
    grid: GridConfig,
    turb_cfg: TurbulenceConfig,
    t_idx: int,
    *,
    plume_cfg: PlumeConfig | None = None,
    adv_cfg: AdvectionConfig | None = None,
) -> NDArray[np.float32]:
    """Perform a single advection step on the concentration field.

    Steps:
    1. Compute vertical velocity from Briggs buoyancy (if buoyancy_flux > 0).
    2. Apply turbulent diffusion displacement via curl noise on departure points.
    3. Delegate to semi-Lagrangian or MacCormack based on scheme.
    3b. Apply mass correction if enabled (before injection to avoid undoing source).
    4. Inject source emission.
    5. Apply mixing-height lid.
    6. Clamp to >= 0.

    Parameters
    ----------
    conc:
        Concentration field (z, y, x) as float32.
    u_wind:
        X-component wind velocity field (z, y, x) in m/s.
    v_wind:
        Y-component wind velocity field (z, y, x) in m/s.
    dt:
        Timestep in seconds.
    grid:
        Grid configuration.
    turb_cfg:
        Turbulence configuration.
    t_idx:
        Time index (for seeding noise).
    plume_cfg:
        Plume configuration (optional, needed for source injection).
    adv_cfg:
        Advection configuration (optional, uses defaults).

    Returns
    -------
    NDArray[np.float32]
        Updated concentration field.

    """
    if dt <= 0:
        msg = f"Timestep dt must be positive, got {dt}"
        raise ValueError(msg)

    # Use defaults if not provided
    if adv_cfg is None:
        adv_cfg = AdvectionConfig()

    mass_before = float(conc.sum()) if adv_cfg.mass_correction else 0.0

    # 1. Vertical velocity from Briggs buoyancy
    nz, ny, nx = grid.shape
    w_wind = np.zeros((nz, ny, nx), dtype=np.float32)
    if adv_cfg.buoyancy_flux > 0 and plume_cfg is not None:
        u_mean = max(float(np.mean(np.abs(u_wind))), 0.1)
        w_wind = _briggs_plume_rise(plume_cfg, adv_cfg, grid, u_mean)

    # CFL diagnostic
    max_u = float(np.max(np.abs(u_wind)))
    max_v = float(np.max(np.abs(v_wind)))
    cfl = max(max_u * dt / grid.dx, max_v * dt / grid.dy)
    if cfl > 1.0:
        logger.warning(
            "CFL number %.2f > 1.0 at step %d; consider reducing dt or increasing sub_steps",
            cfl,
            t_idx,
        )

    # 2. Turbulent curl-noise
    if turb_cfg.enabled:
        u_wind, v_wind, w_wind = _apply_turbulent_curl(
            u_wind,
            v_wind,
            w_wind,
            turb_cfg,
            grid,
            t_idx,
            dt,
        )

    # 3. Advect
    scheme_fn = _maccormack_step if adv_cfg.scheme == "maccormack" else _semi_lagrangian_step
    result = scheme_fn(conc, u_wind, v_wind, w_wind, dt, grid)

    # 3b. Mass correction (before injection to avoid undoing source emission)
    if adv_cfg.mass_correction and mass_before > 0:
        result = _apply_mass_correction(result, mass_before)

    # 4. Source injection
    if plume_cfg is not None:
        result = _inject_source(result, plume_cfg, grid, adv_cfg.source_injection_sigma, dt)

    # 5. Mixing-height lid
    if plume_cfg is not None and plume_cfg.mixing_height > 0:
        lid_layer = int(plume_cfg.mixing_height / grid.dz)
        if lid_layer < nz:
            result[lid_layer:, :, :] = 0.0

    # 6. Clamp negatives
    np.maximum(result, 0.0, out=result)

    return result


def advect_sequence(
    plume_cfg: PlumeConfig,
    grid: GridConfig,
    wind_ds: xr.Dataset,
    turb_cfg: TurbulenceConfig,
    n_steps: int,
    *,
    adv_cfg: AdvectionConfig | None = None,
) -> xr.Dataset:
    """Generate an advected plume concentration sequence.

    Initialises from :func:`generate_timestep` at ``t=0``, then advects
    forward for ``n_steps`` timesteps.  Each timestep is optionally split
    into ``sub_steps`` for smoother transport.

    Parameters
    ----------
    plume_cfg:
        Plume source configuration.
    grid:
        Grid configuration.
    wind_ds:
        Wind field dataset with ``u_wind`` and ``v_wind`` variables,
        shape ``(time, z, y, x)``.
    turb_cfg:
        Turbulence configuration.
    n_steps:
        Number of major timesteps.
    adv_cfg:
        Advection configuration (optional, uses defaults).

    Returns
    -------
    xr.Dataset
        Dataset with ``concentration`` variable, dims ``(time, z, y, x)``.

    """
    if adv_cfg is None:
        adv_cfg = AdvectionConfig()

    # Initialise from Gaussian plume at t=0
    conc = generate_timestep(plume_cfg, grid, 0)
    nz, ny, nx = grid.shape

    frames: list[NDArray[np.float32]] = [conc.astype(np.float32)]
    sub_steps = adv_cfg.sub_steps
    sub_dt = adv_cfg.dt / sub_steps

    # Extract wind fields; reuse last time slice if wind_ds has fewer time steps
    n_wind_times = wind_ds.sizes.get("time", 1)

    frame_idx = 0
    wind_exhaustion_warned = False
    for step in range(n_steps):
        wind_t = min(step, n_wind_times - 1)
        if step >= n_wind_times and not wind_exhaustion_warned:
            logger.warning(
                "Wind data exhausted at step %d/%d; reusing last time slice for remaining steps",
                step,
                n_wind_times,
            )
            wind_exhaustion_warned = True
        u_wind = wind_ds["u_wind"].values[wind_t].astype(np.float32)
        v_wind = wind_ds["v_wind"].values[wind_t].astype(np.float32)

        for _sub in range(sub_steps):
            conc = advect_step(
                conc,
                u_wind,
                v_wind,
                sub_dt,
                grid,
                turb_cfg,
                frame_idx,
                plume_cfg=plume_cfg,
                adv_cfg=adv_cfg,
            )
            frame_idx += 1
            frames.append(conc.astype(np.float32))

    data = np.stack(frames, axis=0)  # (time, z, y, x)

    return xr.Dataset(
        {"concentration": (["time", "z", "y", "x"], data)},
        coords={
            "time": np.arange(len(frames)),
            "z": np.arange(nz) * grid.dz,
            "y": np.arange(ny) * grid.dy,
            "x": np.arange(nx) * grid.dx,
        },
    )
