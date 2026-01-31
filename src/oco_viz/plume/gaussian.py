"""Gaussian plume model with Pasquill-Gifford dispersion."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from oco_viz.plume.stability import sigma_y, sigma_z

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig, PlumeConfig


def _wind_rotation_matrix(wind_dir_deg: float) -> tuple[float, float]:
    """Return (cos, sin) for rotating coordinates into wind-aligned frame.

    Wind direction is meteorological: degrees from N, clockwise.
    We need the angle from the x-axis to the wind direction.
    """
    rad = np.radians(wind_dir_deg)
    return float(np.cos(rad)), float(np.sin(rad))


def generate_timestep(
    config: PlumeConfig,
    grid: GridConfig,
    time_index: int,
) -> NDArray[np.float32]:
    """Generate concentration field for one timestep.

    Uses Gaussian plume equation with:
    - Wind-rotated coordinates
    - Ground reflection
    - Mixing height cap
    """
    nz, ny, nx = grid.shape
    # Physical coordinates in meters
    x_phys = np.arange(nx, dtype=np.float64) * grid.dx
    y_phys = np.arange(ny, dtype=np.float64) * grid.dy
    z_phys = np.arange(nz, dtype=np.float64) * grid.dz

    xx, yy, zz = np.meshgrid(x_phys, y_phys, z_phys, indexing="ij")

    # Source position in physical coords
    src_x = config.source_x * grid.dx
    src_y = config.source_y * grid.dy
    h_eff = config.stack_height

    # Time variation: oscillate wind direction slightly
    wind_dir = config.wind_direction + 5.0 * np.sin(2 * np.pi * time_index / 48)
    cos_w, sin_w = _wind_rotation_matrix(wind_dir)

    # Translate to source-relative coordinates
    dx = xx - src_x
    dy = yy - src_y

    # Rotate into wind-aligned frame: downwind = along wind direction
    downwind = dx * sin_w + dy * cos_w
    crosswind = -dx * cos_w + dy * sin_w

    # Concentration array
    conc = np.zeros_like(xx, dtype=np.float64)

    # Only compute where downwind > 0
    mask = downwind > grid.dx  # at least one cell downwind
    if not np.any(mask):
        return np.transpose(conc, (2, 1, 0)).astype(np.float32)

    dw = downwind[mask]
    cw = crosswind[mask]
    z_vals = zz[mask]

    # Dispersion coefficients per downwind distance
    sy = np.vectorize(lambda d: sigma_y(float(d), config.stability_class))(dw)
    sz = np.vectorize(lambda d: sigma_z(float(d), config.stability_class))(dw)

    # Clamp sigma to avoid division by zero
    sy = np.maximum(sy, 1.0)
    sz = np.maximum(sz, 1.0)

    # Gaussian plume with ground reflection
    q = config.emission_rate
    u = config.wind_speed

    # Crosswind term
    lateral = np.exp(-0.5 * (cw / sy) ** 2)

    # Vertical term with ground reflection
    z1 = ((z_vals - h_eff) / sz) ** 2
    z2 = ((z_vals + h_eff) / sz) ** 2
    vertical = np.exp(-0.5 * z1) + np.exp(-0.5 * z2)

    # Mixing height reflection
    h_mix = config.mixing_height
    if h_mix > 0:
        z3 = ((z_vals - 2 * h_mix + h_eff) / sz) ** 2
        z4 = ((z_vals + 2 * h_mix - h_eff) / sz) ** 2
        vertical = vertical + np.exp(-0.5 * z3) + np.exp(-0.5 * z4)

    values = (q / (2 * np.pi * u * sy * sz)) * lateral * vertical
    conc[mask] = values

    # Clamp negatives (numerical noise)
    np.maximum(conc, 0.0, out=conc)

    # Transpose from (x, y, z) to (z, y, x) for VTK convention
    result: NDArray[np.float32] = np.transpose(conc, (2, 1, 0)).astype(np.float32)
    return result


def generate_sequence(
    config: PlumeConfig,
    grid: GridConfig,
    num_timesteps: int,
) -> xr.Dataset:
    """Generate a time series of plume concentration as xr.Dataset."""
    nz, ny, nx = grid.shape
    frames = []
    for t in range(num_timesteps):
        frame = generate_timestep(config, grid, t)
        frames.append(frame)

    data = np.stack(frames, axis=0)  # (time, z, y, x)

    return xr.Dataset(
        {"concentration": (["time", "z", "y", "x"], data)},
        coords={
            "time": np.arange(num_timesteps),
            "z": np.arange(nz) * grid.dz,
            "y": np.arange(ny) * grid.dy,
            "x": np.arange(nx) * grid.dx,
        },
    )
