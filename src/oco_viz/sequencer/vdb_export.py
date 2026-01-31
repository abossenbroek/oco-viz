"""Export concentration arrays to OpenVDB sparse volume files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import openvdb

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


_GRID_NAME = "density"
_VOXEL_SIZE = 1000.0  # metres


def export_vdb(
    concentration: NDArray[np.float32],
    output_path: Path,
    *,
    threshold: float = 0.0,
) -> Path:
    """Write a 3-D concentration field as a sparse OpenVDB *density* grid.

    Values at or below *threshold* are treated as background (inactive).
    The grid uses a uniform voxel size of 1 000 m.
    """
    data = np.asarray(concentration, dtype=np.float32)
    if data.ndim != 3:
        msg = f"Expected 3-D array, got {data.ndim}-D"
        raise ValueError(msg)

    # Zero out values <= threshold so they become background (inactive)
    sparse = np.where(data > threshold, data, np.float32(0.0))

    grid = openvdb.FloatGrid()
    grid.copyFromArray(sparse)
    grid.name = _GRID_NAME
    grid.transform = openvdb.createLinearTransform(voxelSize=_VOXEL_SIZE)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    openvdb.write(str(output_path), grids=[grid])
    return output_path


def read_vdb(path: Path) -> tuple[NDArray[np.float32], str]:
    """Read first grid from a VDB file, return (array, grid_name)."""
    grids, _ = openvdb.readAll(str(path))
    if not grids:
        msg = f"No grids found in {path}"
        raise ValueError(msg)
    grid = grids[0]
    bbox = grid.evalActiveVoxelBoundingBox()
    # bbox is ((min_i, min_j, min_k), (max_i, max_j, max_k))  inclusive
    shape = tuple(mx - mn + 1 for mn, mx in zip(bbox[0], bbox[1], strict=True))
    out = np.zeros(shape, dtype=np.float32)
    grid.copyToArray(out, ijk=bbox[0])
    return out, grid.name
