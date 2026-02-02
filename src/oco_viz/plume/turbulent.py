"""Turbulent plume compositor: Gaussian base + fractal noise displacement."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr
from scipy.ndimage import map_coordinates

from oco_viz.plume.gaussian import generate_timestep as gaussian_timestep
from oco_viz.plume.noise import curl_noise_3d, fbm_3d

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig, PlumeConfig, TurbulenceConfig


def apply_turbulence(
    base_conc: NDArray[np.float32],
    turb_cfg: TurbulenceConfig,
    grid_cfg: GridConfig,
    time_index: int,
) -> NDArray[np.float32]:
    """Apply turbulence displacement and density modulation to a base concentration field.

    Steps:
    1. Generate curl noise displacement field for divergence-free advection.
    2. Displace coordinates using map_coordinates with curl_strength scaling.
    3. Modulate density with fBm noise (amplitude-controlled).
    4. Apply distance-from-center falloff for wispy edges.
    5. Clamp to >= 0.

    """
    shape = grid_cfg.shape
    seed_offset = int(time_index * turb_cfg.temporal_speed * 1000)

    # Step 1: curl noise displacement field
    curl_dx, curl_dy, curl_dz = curl_noise_3d(
        shape,
        octaves=min(turb_cfg.octaves, 4),
        lacunarity=turb_cfg.lacunarity,
        gain=turb_cfg.gain,
        seed=turb_cfg.seed + seed_offset,
    )

    # Step 2: build displaced coordinate arrays
    nz, ny, nx = shape
    coords_z, coords_y, coords_x = np.mgrid[0:nz, 0:ny, 0:nx]
    coords_z = coords_z.astype(np.float64)
    coords_y = coords_y.astype(np.float64)
    coords_x = coords_x.astype(np.float64)

    # Scale curl displacement by strength and a fraction of the grid size
    disp_scale = turb_cfg.curl_strength * min(nz, ny, nx) * 0.5
    coords_z += curl_dz.astype(np.float64) * disp_scale
    coords_y += curl_dy.astype(np.float64) * disp_scale
    coords_x += curl_dx.astype(np.float64) * disp_scale

    # Step 2b: warp the base concentration field
    warped = map_coordinates(
        base_conc.astype(np.float64),
        [coords_z, coords_y, coords_x],
        order=1,
        mode="constant",
        cval=0.0,
    )

    # Step 3: density modulation via fBm noise
    noise = fbm_3d(
        shape,
        octaves=turb_cfg.octaves,
        lacunarity=turb_cfg.lacunarity,
        gain=turb_cfg.gain,
        seed=turb_cfg.seed + seed_offset + 100,
    )
    # Modulate around 1.0: (noise * amplitude) + (1 - amplitude/2)
    modulation = noise.astype(np.float64) * turb_cfg.amplitude + (1.0 - turb_cfg.amplitude / 2.0)
    warped *= modulation

    # Step 4: distance-from-center falloff (core dense, edges wispy)
    cz, cy, cx = nz / 2.0, ny / 2.0, nx / 2.0
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]
    dist = np.sqrt(
        ((zz - cz) / cz) ** 2 + ((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2,
    )
    # Smooth falloff: 1.0 at center, ~0 at corners
    falloff = np.clip(1.0 - dist * 0.5, 0.0, 1.0)
    warped *= falloff

    # Step 5: clamp negatives
    np.maximum(warped, 0.0, out=warped)

    return warped.astype(np.float32)


def generate_turbulent_timestep(
    plume_cfg: PlumeConfig,
    grid_cfg: GridConfig,
    turb_cfg: TurbulenceConfig,
    time_index: int,
) -> NDArray[np.float32]:
    """Generate a single turbulent plume timestep.

    Combines Gaussian base with fractal turbulence displacement.
    """
    base = gaussian_timestep(plume_cfg, grid_cfg, time_index)
    if not turb_cfg.enabled:
        return base
    return apply_turbulence(base, turb_cfg, grid_cfg, time_index)


def generate_turbulent_sequence(
    plume_cfg: PlumeConfig,
    grid_cfg: GridConfig,
    turb_cfg: TurbulenceConfig,
    num_timesteps: int,
) -> xr.Dataset:
    """Generate a time series of turbulent plume concentrations as xr.Dataset."""
    nz, ny, nx = grid_cfg.shape
    frames = []
    for t in range(num_timesteps):
        frame = generate_turbulent_timestep(plume_cfg, grid_cfg, turb_cfg, t)
        frames.append(frame)

    data = np.stack(frames, axis=0)  # (time, z, y, x)

    return xr.Dataset(
        {"concentration": (["time", "z", "y", "x"], data)},
        coords={
            "time": np.arange(num_timesteps),
            "z": np.arange(nz) * grid_cfg.dz,
            "y": np.arange(ny) * grid_cfg.dy,
            "x": np.arange(nx) * grid_cfg.dx,
        },
    )
