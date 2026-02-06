"""Round-trip tests for OpenVDB export module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import openvdb
import pytest

from oco_viz.config.schema import GridConfig
from oco_viz.export.vdb import export_vdb_sequence, numpy_to_vdb

if TYPE_CHECKING:
    from pathlib import Path


def test_numpy_to_vdb_round_trip() -> None:
    """Numpy → VDB → read back should preserve non-zero values."""
    data = np.zeros((8, 10, 12), dtype=np.float32)
    # Set some known values
    data[2, 3, 4] = 1.5
    data[5, 7, 9] = 0.75
    data[0, 0, 0] = 0.001

    grid = numpy_to_vdb(data, grid_name="density")

    # Read back values via accessor
    accessor = grid.getAccessor()
    assert abs(accessor.getValue((4, 3, 2)) - 1.5) < 1e-6
    assert abs(accessor.getValue((9, 7, 5)) - 0.75) < 1e-6
    assert abs(accessor.getValue((0, 0, 0)) - 0.001) < 1e-6

    # Zero values should not be active
    assert accessor.getValue((0, 0, 1)) == 0.0


def test_numpy_to_vdb_sparsity() -> None:
    """VDB grid should be sparse — only non-zero voxels active."""
    data = np.zeros((16, 16, 16), dtype=np.float32)
    data[8, 8, 8] = 1.0  # Single active voxel

    grid = numpy_to_vdb(data)
    assert grid.activeVoxelCount() == 1


def test_numpy_to_vdb_with_grid_config() -> None:
    """Grid config should set voxel size on the VDB transform."""
    data = np.zeros((8, 10, 12), dtype=np.float32)
    data[4, 5, 6] = 1.0

    grid_cfg = GridConfig(nx=12, ny=10, nz=8, dx=100.0, dy=100.0, dz=50.0)
    grid = numpy_to_vdb(data, grid_cfg)

    # Voxel size should be min(dx, dy, dz) = 50.0
    voxel_size = grid.transform.voxelSize()
    assert abs(voxel_size[0] - 50.0) < 1e-6


def test_numpy_to_vdb_metadata() -> None:
    """Metadata should be attached to the VDB grid."""
    data = np.zeros((4, 4, 4), dtype=np.float32)
    data[2, 2, 2] = 1.0

    metadata = {"source": "oco-viz", "stability_class": "D"}
    grid = numpy_to_vdb(data, metadata=metadata)

    assert grid["source"] == "oco-viz"
    assert grid["stability_class"] == "D"


def test_numpy_to_vdb_grid_name() -> None:
    """Grid name should be set correctly."""
    data = np.zeros((4, 4, 4), dtype=np.float32)
    data[2, 2, 2] = 1.0

    grid = numpy_to_vdb(data, grid_name="temperature")
    assert grid.name == "temperature"


def test_numpy_to_vdb_rejects_non_3d() -> None:
    """Non-3D input should raise ValueError."""
    data_2d = np.zeros((4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="3D"):
        numpy_to_vdb(data_2d)


def test_export_vdb_sequence_creates_files(tmp_path: Path) -> None:
    """Sequence export should create numbered VDB files."""
    frames = [np.random.default_rng(i).random((4, 6, 8)).astype(np.float32) for i in range(3)]

    paths = export_vdb_sequence(frames, tmp_path, prefix="test")

    assert len(paths) == 3
    for i, path in enumerate(paths):
        assert path.exists()
        assert path.name == f"test_{i:04d}.vdb"


def test_export_vdb_sequence_round_trip(tmp_path: Path) -> None:
    """Sequence export should preserve data through file I/O."""
    data = np.zeros((8, 10, 12), dtype=np.float32)
    data[4, 5, 6] = 2.5
    data[2, 3, 4] = 0.8

    paths = export_vdb_sequence([data], tmp_path, prefix="roundtrip")
    assert len(paths) == 1

    # Read back — readAll returns (grids_list, file_metadata)
    grids, _ = openvdb.readAll(str(paths[0]))
    assert len(grids) == 1
    read_grid = grids[0]

    accessor = read_grid.getAccessor()
    assert abs(accessor.getValue((6, 5, 4)) - 2.5) < 1e-6
    assert abs(accessor.getValue((4, 3, 2)) - 0.8) < 1e-6


def test_export_vdb_sequence_metadata(tmp_path: Path) -> None:
    """Metadata should be preserved through file I/O."""
    data = np.zeros((4, 4, 4), dtype=np.float32)
    data[2, 2, 2] = 1.0

    metadata = {"source": "oco-viz", "tier": "exhibition"}
    export_vdb_sequence([data], tmp_path, metadata=metadata, prefix="meta")

    grids, _ = openvdb.readAll(str(tmp_path / "meta_0000.vdb"))
    grid = grids[0]
    assert grid["source"] == "oco-viz"
    assert grid["tier"] == "exhibition"
    assert grid["timestep"] == "0"  # Added by export_vdb_sequence
