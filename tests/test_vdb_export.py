"""Round-trip tests for OpenVDB export module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import openvdb
import pytest

from oco_viz.config.schema import GridConfig
from oco_viz.export.vdb import (
    compute_dissolution_mask,
    compute_temperature_field,
    export_multi_grid_vdb,
    export_vdb_sequence,
    numpy_to_vdb,
    numpy_to_vec3f_grid,
)

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


# ------------------------------------------------------------------ #
# Multi-grid VDB export tests
# ------------------------------------------------------------------ #


def _make_concentration(shape: tuple[int, int, int] = (10, 10, 10)) -> np.ndarray:
    """Create a Gaussian concentration blob for testing."""
    nz, ny, nx = shape
    z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
    cx, cy, cz = nx / 2.0, ny / 2.0, nz / 2.0
    conc = np.exp(-((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) / (2 * 2.0**2))
    return conc.astype(np.float32)


def test_numpy_to_vec3f_grid_creates_vec3s() -> None:
    """Vec3SGrid is created with correct name and active voxels."""
    shape = (8, 8, 8)
    rng = np.random.default_rng(42)
    u = rng.standard_normal(shape).astype(np.float32)
    v = rng.standard_normal(shape).astype(np.float32)
    w = rng.standard_normal(shape).astype(np.float32)

    grid_cfg = GridConfig(nx=8, ny=8, nz=8, dx=100.0, dy=100.0, dz=50.0)
    grid = numpy_to_vec3f_grid(u, v, w, grid_cfg, grid_name="vel")

    assert grid.name == "vel"
    assert isinstance(grid, openvdb.Vec3SGrid)
    assert grid.activeVoxelCount() > 0


def test_numpy_to_vec3f_grid_shape_mismatch() -> None:
    """Mismatched shapes raise ValueError."""
    u = np.zeros((8, 8, 8), dtype=np.float32)
    v = np.zeros((8, 8, 4), dtype=np.float32)
    w = np.zeros((8, 8, 8), dtype=np.float32)

    with pytest.raises(ValueError, match="Shape mismatch"):
        numpy_to_vec3f_grid(u, v, w)


def test_compute_temperature_range() -> None:
    """Temperature field stays within [t_ambient, t_source]."""
    conc = _make_concentration()
    grid_cfg = GridConfig(nx=10, ny=10, nz=10, dx=100.0, dy=100.0, dz=50.0)

    temp = compute_temperature_field(conc, grid_cfg, t_ambient=293.0, t_source=423.0)

    assert temp.shape == conc.shape
    assert temp.min() >= 293.0 - 1e-5
    assert temp.max() <= 423.0 + 1e-5
    assert temp.max() > 293.0


def test_compute_temperature_zero_concentration() -> None:
    """Zero concentration produces uniform ambient temperature."""
    conc = np.zeros((8, 8, 8), dtype=np.float32)
    grid_cfg = GridConfig(nx=8, ny=8, nz=8, dx=100.0, dy=100.0, dz=50.0)

    temp = compute_temperature_field(conc, grid_cfg, t_ambient=293.0, t_source=423.0)

    assert np.allclose(temp, 293.0)


def test_compute_dissolution_mask_range() -> None:
    """Dissolution mask stays within [0, 1]."""
    conc = _make_concentration()

    mask = compute_dissolution_mask(conc, low=0.05, high=0.30)

    assert mask.shape == conc.shape
    assert mask.min() >= 0.0
    assert mask.max() <= 1.0
    # Core (high concentration) should be near 0
    peak_idx = np.unravel_index(conc.argmax(), conc.shape)
    assert mask[peak_idx] < 0.5


def test_compute_dissolution_mask_zero_concentration() -> None:
    """Zero concentration produces all-ones mask."""
    conc = np.zeros((8, 8, 8), dtype=np.float32)

    mask = compute_dissolution_mask(conc)

    assert np.allclose(mask, 1.0)


def test_export_multi_grid_vdb_roundtrip(tmp_path: Path) -> None:
    """Multi-grid VDB roundtrips through write/read."""
    path = tmp_path / "test_multi.vdb"
    grid_cfg = GridConfig(nx=10, ny=10, nz=10, dx=100.0, dy=100.0, dz=50.0)
    conc = _make_concentration()

    rng = np.random.default_rng(42)
    u = rng.standard_normal(conc.shape).astype(np.float32)
    v = rng.standard_normal(conc.shape).astype(np.float32)
    w = rng.standard_normal(conc.shape).astype(np.float32)

    temp = compute_temperature_field(conc, grid_cfg)
    diss = compute_dissolution_mask(conc)

    result_path = export_multi_grid_vdb(
        conc,
        velocity=(u, v, w),
        temperature=temp,
        dissolution=diss,
        path=path,
        grid_cfg=grid_cfg,
        metadata={"frame": "0"},
    )

    assert result_path == path
    assert path.exists()

    grids, _ = openvdb.readAll(str(path))
    grid_names = {g.name for g in grids}
    assert "density" in grid_names
    assert "vel" in grid_names
    assert "temperature" in grid_names
    assert "dissolution_mask" in grid_names


def test_export_multi_grid_vdb_density_only(tmp_path: Path) -> None:
    """Export with only density (no velocity/temp/dissolution)."""
    path = tmp_path / "density_only.vdb"
    grid_cfg = GridConfig(nx=10, ny=10, nz=10, dx=100.0, dy=100.0, dz=50.0)
    conc = _make_concentration()

    result_path = export_multi_grid_vdb(
        conc,
        velocity=None,
        temperature=None,
        dissolution=None,
        path=path,
        grid_cfg=grid_cfg,
    )

    assert result_path.exists()
    grids, _ = openvdb.readAll(str(path))
    assert len(grids) == 1
    assert grids[0].name == "density"


def test_sparse_design_zeros_small_values(tmp_path: Path) -> None:
    """Values below 1e-6 are zeroed before VDB export."""
    path = tmp_path / "sparse_test.vdb"
    grid_cfg = GridConfig(nx=10, ny=10, nz=10, dx=100.0, dy=100.0, dz=50.0)

    conc = np.full((10, 10, 10), 1e-8, dtype=np.float32)
    conc[5, 5, 5] = 1.0

    export_multi_grid_vdb(
        conc,
        velocity=None,
        temperature=None,
        dissolution=None,
        path=path,
        grid_cfg=grid_cfg,
    )

    grids, _ = openvdb.readAll(str(path))
    density = grids[0]
    assert density.activeVoxelCount() == 1


def test_export_multi_grid_metadata(tmp_path: Path) -> None:
    """Metadata is attached to all grids."""
    path = tmp_path / "meta_test.vdb"
    grid_cfg = GridConfig(nx=10, ny=10, nz=10, dx=100.0, dy=100.0, dz=50.0)
    conc = _make_concentration()

    export_multi_grid_vdb(
        conc,
        velocity=None,
        temperature=None,
        dissolution=None,
        path=path,
        grid_cfg=grid_cfg,
        metadata={"render_tier": "exhibition"},
    )

    grids, _ = openvdb.readAll(str(path))
    density = grids[0]
    assert density["creator"] == "oco-viz"
    assert density["file_grid_class"] == "fog volume"
    assert density["render_tier"] == "exhibition"
