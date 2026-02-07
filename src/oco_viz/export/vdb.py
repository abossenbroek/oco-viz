"""OpenVDB export for downstream Houdini/GPU rendering pipeline.

Converts numpy concentration arrays to sparse OpenVDB float grids with
proper metadata for the cinematic pipeline.

Grid conventions:
- Name: "density" (standard for volume rendering)
- Type: float32, sparse
- Voxel size: derived from grid config (dx, dy, dz) in meters
- Metadata: emission_rate, stability_class, timestep, source
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import openvdb

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig

logger = logging.getLogger(__name__)


def numpy_to_vdb(
    data: NDArray[np.float32],
    grid_cfg: GridConfig | None = None,
    *,
    grid_name: str = "density",
    metadata: dict[str, str] | None = None,
) -> openvdb.FloatGrid:
    """Convert a 3D numpy array to a sparse OpenVDB FloatGrid.

    Parameters
    ----------
    data:
        Concentration field with shape (nz, ny, nx), float32.
    grid_cfg:
        Grid configuration for voxel size. If None, uses unit voxel size.
    grid_name:
        Name of the VDB grid (default: "density").
    metadata:
        Optional string metadata to embed in the grid.

    Returns
    -------
    openvdb.FloatGrid
        Sparse VDB grid containing only non-zero voxels.

    """
    if data.ndim != 3:
        msg = f"Expected 3D array, got {data.ndim}D"
        raise ValueError(msg)

    grid = openvdb.FloatGrid()
    grid.name = grid_name

    # Set voxel size from grid config
    if grid_cfg is not None:
        voxel_size = float(min(grid_cfg.dx, grid_cfg.dy, grid_cfg.dz))
        grid.transform = openvdb.createLinearTransform(voxelSize=voxel_size)

    # Copy non-zero values to the sparse grid (exact 0.0 stays empty)
    accessor = grid.getAccessor()
    nonzero_mask = data > 0.0
    nonzero_count = int(nonzero_mask.sum())

    indices = np.argwhere(nonzero_mask)
    for idx in indices:
        iz, iy, ix = int(idx[0]), int(idx[1]), int(idx[2])
        accessor.setValueOn((ix, iy, iz), float(data[iz, iy, ix]))

    # Attach metadata
    if metadata:
        for key, value in metadata.items():
            grid[key] = value

    logger.info(
        "VDB grid '%s': %d/%d active voxels (%.1f%% sparse)",
        grid_name,
        nonzero_count,
        data.size,
        (1.0 - nonzero_count / data.size) * 100,
    )

    return grid


def export_vdb_sequence(
    frames: list[NDArray[np.float32]],
    output_dir: Path,
    grid_cfg: GridConfig | None = None,
    *,
    grid_name: str = "density",
    prefix: str = "plume",
    metadata: dict[str, str] | None = None,
) -> list[Path]:
    """Export a sequence of concentration frames as numbered VDB files.

    Parameters
    ----------
    frames:
        List of 3D concentration arrays (nz, ny, nx).
    output_dir:
        Directory for output VDB files.
    grid_cfg:
        Grid configuration for voxel size.
    grid_name:
        Name of the VDB grid.
    prefix:
        Filename prefix (files named {prefix}_{frame:04d}.vdb).
    metadata:
        Optional metadata to embed in each grid.

    Returns
    -------
    list[Path]
        Paths to the written VDB files.

    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for i, frame in enumerate(frames):
        frame_meta = dict(metadata) if metadata else {}
        frame_meta["timestep"] = str(i)

        grid = numpy_to_vdb(
            frame.astype(np.float32),
            grid_cfg,
            grid_name=grid_name,
            metadata=frame_meta,
        )

        path = output_dir / f"{prefix}_{i:04d}.vdb"
        openvdb.write(str(path), grids=[grid])
        paths.append(path)

        logger.info("Wrote VDB frame %d/%d: %s", i + 1, len(frames), path)

    return paths


def numpy_to_vec3f_grid(
    u: NDArray[np.float32],
    v: NDArray[np.float32],
    w: NDArray[np.float32],
    grid_cfg: GridConfig | None = None,
    *,
    grid_name: str = "vel",
) -> openvdb.Vec3SGrid:
    """Convert three velocity component arrays to a sparse OpenVDB Vec3SGrid.

    Parameters
    ----------
    u:
        X-component velocity field (z, y, x).
    v:
        Y-component velocity field (z, y, x).
    w:
        Z-component velocity field (z, y, x).
    grid_cfg:
        Grid configuration for voxel size. If None, uses unit voxel size.
    grid_name:
        Name of the VDB grid (default: "vel").

    Returns
    -------
    openvdb.Vec3SGrid
        Sparse VDB grid containing only non-zero velocity voxels.

    """
    if u.shape != v.shape or u.shape != w.shape:
        msg = f"Shape mismatch: u={u.shape}, v={v.shape}, w={w.shape}"
        raise ValueError(msg)
    if u.ndim != 3:
        msg = f"Expected 3D arrays, got {u.ndim}D"
        raise ValueError(msg)

    grid = openvdb.Vec3SGrid()
    grid.name = grid_name

    if grid_cfg is not None:
        voxel_size = float(min(grid_cfg.dx, grid_cfg.dy, grid_cfg.dz))
        grid.transform = openvdb.createLinearTransform(voxelSize=voxel_size)

    # Find voxels where any component exceeds threshold
    threshold = 1e-6
    active_mask = (np.abs(u) > threshold) | (np.abs(v) > threshold) | (np.abs(w) > threshold)
    indices = np.argwhere(active_mask)

    accessor = grid.getAccessor()
    for idx in indices:
        iz, iy, ix = int(idx[0]), int(idx[1]), int(idx[2])
        accessor.setValueOn(
            (ix, iy, iz),
            (float(u[iz, iy, ix]), float(v[iz, iy, ix]), float(w[iz, iy, ix])),
        )

    nonzero_count = int(active_mask.sum())
    logger.info(
        "VDB Vec3SGrid '%s': %d/%d active voxels (%.1f%% sparse)",
        grid_name,
        nonzero_count,
        u.size,
        (1.0 - nonzero_count / u.size) * 100,
    )

    return grid


def compute_temperature_field(
    concentration: NDArray[np.float32],
    grid_cfg: GridConfig,
    *,
    t_ambient: float = 293.0,
    t_source: float = 423.0,
    decay_cells: float = 50.0,
) -> NDArray[np.float32]:
    """Compute temperature field from concentration for emission shading.

    Temperature scales linearly with normalized concentration:
    T = t_ambient + (t_source - t_ambient) * concentration_normalized

    The concentration is first normalized to [0, 1] by dividing by its max.
    Areas with zero concentration get t_ambient (effectively background).

    Parameters
    ----------
    concentration:
        3D concentration field (z, y, x).
    grid_cfg:
        Grid configuration (unused currently, reserved for future decay logic).
    t_ambient:
        Ambient temperature in Kelvin.
    t_source:
        Source temperature in Kelvin.
    decay_cells:
        Temperature decay distance in grid cells (reserved for future use).

    Returns
    -------
    NDArray[np.float32]
        Temperature field in Kelvin with shape matching concentration.

    """
    _ = grid_cfg  # reserved for future spatial decay
    _ = decay_cells  # reserved for future spatial decay
    c_max = float(concentration.max())
    if c_max <= 0:
        return np.full_like(concentration, t_ambient, dtype=np.float32)

    c_norm = concentration.astype(np.float64) / c_max
    temp = t_ambient + (t_source - t_ambient) * c_norm
    return temp.astype(np.float32)


def compute_dissolution_mask(
    concentration: NDArray[np.float32],
    *,
    low: float = 0.05,
    high: float = 0.30,
) -> NDArray[np.float32]:
    """Compute edge dissolution mask from concentration field.

    Returns a mask in [0, 1] where:
    - 0.0 = solid core (concentration > high * max)
    - 1.0 = fully dissolved edge (concentration < low * max)
    - Linear interpolation between low and high thresholds

    Parameters
    ----------
    concentration:
        3D concentration field (z, y, x).
    low:
        Low threshold fraction (below this = fully dissolved).
    high:
        High threshold fraction (above this = solid core).

    Returns
    -------
    NDArray[np.float32]
        Dissolution mask in [0, 1].

    """
    c_max = float(concentration.max())
    if c_max <= 0:
        return np.ones_like(concentration, dtype=np.float32)

    low_val = low * c_max
    high_val = high * c_max

    conc_f64 = concentration.astype(np.float64)

    # Linear interpolation: 1.0 at low_val, 0.0 at high_val
    if high_val > low_val:
        mask = 1.0 - (conc_f64 - low_val) / (high_val - low_val)
    else:
        mask = np.where(conc_f64 > low_val, 0.0, 1.0)

    return np.clip(mask, 0.0, 1.0).astype(np.float32)


def export_multi_grid_vdb(
    concentration: NDArray[np.float32],
    velocity: tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]] | None,
    temperature: NDArray[np.float32] | None,
    dissolution: NDArray[np.float32] | None,
    path: Path,
    grid_cfg: GridConfig | None = None,
    *,
    metadata: dict[str, str] | None = None,
) -> Path:
    """Export multi-grid VDB file with density, velocity, temperature, and dissolution.

    All grids share the same voxel transform from grid_cfg.
    Voxels with values < 1e-6 are stored as exactly 0.0 (sparse design).

    Parameters
    ----------
    concentration:
        3D concentration field (z, y, x).
    velocity:
        Optional tuple of (u, v, w) velocity component arrays.
    temperature:
        Optional temperature field in Kelvin.
    dissolution:
        Optional dissolution mask field in [0, 1].
    path:
        Output VDB file path.
    grid_cfg:
        Grid configuration for voxel size.
    metadata:
        Optional string metadata to embed in all grids.

    Returns
    -------
    Path
        Path to the written VDB file.

    """
    threshold = 1e-6

    # Zero out small values for sparse design
    conc_sparse = concentration.copy()
    conc_sparse[np.abs(conc_sparse) < threshold] = 0.0

    # Build density grid
    meta = dict(metadata) if metadata else {}
    meta.setdefault("creator", "oco-viz")
    meta.setdefault("file_grid_class", "fog volume")

    density_grid = numpy_to_vdb(
        conc_sparse.astype(np.float32),
        grid_cfg,
        grid_name="density",
        metadata=meta,
    )

    grids: list[openvdb.FloatGrid | openvdb.Vec3SGrid] = [density_grid]

    # Velocity grid
    if velocity is not None:
        u, v, w = velocity
        # Zero out small values
        u_sparse = u.copy()
        v_sparse = v.copy()
        w_sparse = w.copy()
        u_sparse[np.abs(u_sparse) < threshold] = 0.0
        v_sparse[np.abs(v_sparse) < threshold] = 0.0
        w_sparse[np.abs(w_sparse) < threshold] = 0.0

        vel_grid = numpy_to_vec3f_grid(
            u_sparse.astype(np.float32),
            v_sparse.astype(np.float32),
            w_sparse.astype(np.float32),
            grid_cfg,
            grid_name="vel",
        )
        for key, value in meta.items():
            vel_grid[key] = value
        grids.append(vel_grid)

    # Temperature grid
    if temperature is not None:
        temp_sparse = temperature.copy()
        temp_sparse[np.abs(temp_sparse) < threshold] = 0.0
        temp_grid = numpy_to_vdb(
            temp_sparse.astype(np.float32),
            grid_cfg,
            grid_name="temperature",
            metadata=meta,
        )
        grids.append(temp_grid)

    # Dissolution grid
    if dissolution is not None:
        diss_sparse = dissolution.copy()
        diss_sparse[np.abs(diss_sparse) < threshold] = 0.0
        diss_grid = numpy_to_vdb(
            diss_sparse.astype(np.float32),
            grid_cfg,
            grid_name="dissolution_mask",
            metadata=meta,
        )
        grids.append(diss_grid)

    path.parent.mkdir(parents=True, exist_ok=True)
    openvdb.write(str(path), grids=grids)

    logger.info("Wrote multi-grid VDB: %s (%d grids)", path, len(grids))

    return path
