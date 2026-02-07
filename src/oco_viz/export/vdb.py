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
