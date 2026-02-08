"""Validate VDB output conforms to Houdini pipeline conventions."""

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
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_vdb(tmp_path: Path) -> Path:
    """Create a sample multi-grid VDB for convention tests."""
    grid_cfg = GridConfig(nx=20, ny=20, nz=10, dx=100.0, dy=100.0, dz=50.0)
    rng = np.random.default_rng(42)
    concentration = rng.random((10, 20, 20), dtype=np.float32) * 0.8
    velocity = (
        rng.random((10, 20, 20), dtype=np.float32) * 5.0,
        rng.random((10, 20, 20), dtype=np.float32) * 3.0,
        rng.random((10, 20, 20), dtype=np.float32) * 1.0,
    )
    temperature = compute_temperature_field(concentration, grid_cfg)
    dissolution = compute_dissolution_mask(concentration)
    path = tmp_path / "test_conventions.vdb"
    export_multi_grid_vdb(
        concentration,
        velocity,
        temperature,
        dissolution,
        path,
        grid_cfg,
        metadata={"creator": "oco-viz", "file_grid_class": "fog volume"},
    )
    return path


def test_grid_names(sample_vdb: Path) -> None:
    """VDB must contain exactly the 4 expected grid names."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    names = {g.name for g in grids}
    assert names == {"density", "vel", "temperature", "dissolution_mask"}


def test_grid_types(sample_vdb: Path) -> None:
    """density/temperature/dissolution are FloatGrid, vel is Vec3SGrid."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    type_map = {g.name: type(g).__name__ for g in grids}
    for name in ("density", "temperature", "dissolution_mask"):
        assert type_map[name] == "FloatGrid", f"{name} should be FloatGrid, got {type_map[name]}"
    assert type_map["vel"] == "Vec3SGrid", f"vel should be Vec3SGrid, got {type_map['vel']}"


def test_density_range(sample_vdb: Path) -> None:
    """Density values must be in [0, 1]."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    density = next(g for g in grids if g.name == "density")
    # Read all active values via bounding box iteration
    bbox_min, bbox_max = density.evalActiveVoxelBoundingBox()
    accessor = density.getAccessor()
    for iz in range(bbox_min[2], bbox_max[2] + 1):
        for iy in range(bbox_min[1], bbox_max[1] + 1):
            for ix in range(bbox_min[0], bbox_max[0] + 1):
                val = accessor.getValue((ix, iy, iz))
                if val != 0.0:
                    assert 0.0 <= val <= 1.0, f"Density {val} outside [0, 1]"


def test_temperature_range(sample_vdb: Path) -> None:
    """Temperature must be in [293, 423] K."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    temp = next(g for g in grids if g.name == "temperature")
    bbox_min, bbox_max = temp.evalActiveVoxelBoundingBox()
    accessor = temp.getAccessor()
    for iz in range(bbox_min[2], bbox_max[2] + 1):
        for iy in range(bbox_min[1], bbox_max[1] + 1):
            for ix in range(bbox_min[0], bbox_max[0] + 1):
                val = accessor.getValue((ix, iy, iz))
                if val != 0.0:
                    assert 293.0 - 0.1 <= val <= 423.0 + 0.1, (
                        f"Temperature {val} outside [293, 423]K"
                    )


def test_dissolution_range(sample_vdb: Path) -> None:
    """Dissolution mask must be in [0, 1]."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    diss = next(g for g in grids if g.name == "dissolution_mask")
    bbox_min, bbox_max = diss.evalActiveVoxelBoundingBox()
    accessor = diss.getAccessor()
    for iz in range(bbox_min[2], bbox_max[2] + 1):
        for iy in range(bbox_min[1], bbox_max[1] + 1):
            for ix in range(bbox_min[0], bbox_max[0] + 1):
                val = accessor.getValue((ix, iy, iz))
                if val != 0.0:
                    assert 0.0 <= val <= 1.0, f"Dissolution {val} outside [0, 1]"


def test_no_nan_inf(sample_vdb: Path) -> None:
    """No grid may contain NaN or Inf values."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    for g in grids:
        bbox_min, bbox_max = g.evalActiveVoxelBoundingBox()
        accessor = g.getAccessor()
        for iz in range(bbox_min[2], bbox_max[2] + 1):
            for iy in range(bbox_min[1], bbox_max[1] + 1):
                for ix in range(bbox_min[0], bbox_max[0] + 1):
                    val = accessor.getValue((ix, iy, iz))
                    if isinstance(val, (int, float)):
                        assert np.isfinite(val), (
                            f"Grid {g.name} has non-finite value at ({ix},{iy},{iz})"
                        )
                    elif hasattr(val, "__len__"):
                        for component in val:
                            assert np.isfinite(component), (
                                f"Grid {g.name} has non-finite vector component"
                            )


def test_metadata_present(sample_vdb: Path) -> None:
    """Required metadata fields must be present."""
    grids, _ = openvdb.readAll(str(sample_vdb))
    density = next(g for g in grids if g.name == "density")
    assert density["creator"] == "oco-viz"
    assert density["file_grid_class"] == "fog volume"
