"""Tests for TouchDesigner VDB + point cloud export."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import numpy as np
import pytest

import oco_viz.sequencer.td_export as td_mod
from oco_viz.sequencer.td_export import (
    _create_vdb_transform,
    _position_to_rotation,
    _tf_to_color_ramp,
    _tf_to_opacity_ramp,
    export_point_cloud,
    export_td_camera_chop,
    export_td_manifest,
    export_td_vdb_frame,
    export_td_vdb_sequence,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _noop_grid(*_args: object, **_kwargs: object) -> MagicMock:
    return MagicMock()


def _zero_field(*_args: object, **_kwargs: object) -> np.ndarray:
    return np.zeros((4, 4, 4), dtype=np.float32)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_openvdb(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Provide a mock openvdb module so tests run without the real C extension."""
    mock_vdb = MagicMock()
    mock_grid = MagicMock()
    mock_vdb.FloatGrid.return_value = mock_grid
    mock_vdb.Vec3SGrid.return_value = MagicMock()
    mock_vdb.createLinearTransform.return_value = MagicMock()
    monkeypatch.setitem(sys.modules, "openvdb", mock_vdb)
    monkeypatch.setattr(td_mod, "openvdb", mock_vdb)
    return mock_vdb


@pytest.fixture
def _mock_export_vdb(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock oco_viz.export.vdb functions used by td_export."""
    monkeypatch.setattr(td_mod, "numpy_to_vec3f_grid", _noop_grid)
    monkeypatch.setattr(td_mod, "compute_temperature_field", _zero_field)
    monkeypatch.setattr(td_mod, "compute_dissolution_mask", _zero_field)
    monkeypatch.setattr(td_mod, "numpy_to_vdb", _noop_grid)


@pytest.fixture
def grid_cfg() -> MagicMock:
    """Minimal GridConfig stand-in."""
    cfg = MagicMock()
    cfg.dx = 100.0
    cfg.dy = 100.0
    cfg.dz = 50.0
    cfg.nx = 10
    cfg.ny = 10
    cfg.nz = 8
    return cfg


@pytest.fixture
def app_config(grid_cfg: MagicMock) -> MagicMock:
    """Minimal AppConfig stand-in."""
    cfg = MagicMock()
    cfg.grid = grid_cfg
    cfg.output.fps = 24
    cfg.data_source.domain.origin_lat = -26.52
    cfg.data_source.domain.origin_lon = 29.17
    return cfg


@pytest.fixture
def sample_concentration() -> np.ndarray:
    """Small 3-D test concentration field."""
    rng = np.random.default_rng(42)
    data = rng.random((8, 10, 10), dtype=np.float32)
    data[data < 0.3] = 0.0
    return data


@pytest.fixture
def sample_tf() -> MagicMock:
    """Minimal TransferFunction stand-in with attrs-like fields."""
    cp1 = MagicMock()
    cp1.scalar = 0.0
    cp1.r = 0.0
    cp1.g = 0.0
    cp1.b = 0.0
    cp1.opacity = 0.0

    cp2 = MagicMock()
    cp2.scalar = 0.5
    cp2.r = 1.0
    cp2.g = 0.5
    cp2.b = 0.2
    cp2.opacity = 0.3

    cp3 = MagicMock()
    cp3.scalar = 1.0
    cp3.r = 1.0
    cp3.g = 1.0
    cp3.b = 1.0
    cp3.opacity = 0.5

    tf = MagicMock()
    tf.color_points = [cp3, cp1, cp2]  # deliberately unsorted
    tf.opacity_points = [cp2, cp3, cp1]  # deliberately unsorted
    return tf


@pytest.fixture
def camera_path_mock() -> MagicMock:
    """Mock CameraPath that returns predictable states."""
    path = MagicMock()

    def _evaluate(t: float) -> MagicMock:
        state = MagicMock()
        state.position = (100.0 * t, 200.0 * t, 300.0)
        state.focal_point = (50.0, 50.0, 30.0)
        return state

    path.evaluate = _evaluate
    return path


# ---------------------------------------------------------------------------
# _position_to_rotation tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb")
def test_position_to_rotation_above() -> None:
    """Camera directly above focal point looking down -> pitch = -90."""
    rx, _ry, rz = _position_to_rotation(
        position=(50.0, 50.0, 100.0),
        focal_point=(50.0, 50.0, 0.0),
    )
    assert rz == 0.0
    assert rx == pytest.approx(-90.0, abs=0.1)


@pytest.mark.usefixtures("mock_openvdb")
def test_position_to_rotation_same_height() -> None:
    """Camera at same height -> pitch ~0."""
    rx, _ry, rz = _position_to_rotation(
        position=(100.0, 50.0, 30.0),
        focal_point=(50.0, 50.0, 30.0),
    )
    assert rz == 0.0
    assert rx == pytest.approx(0.0, abs=0.1)


@pytest.mark.usefixtures("mock_openvdb")
def test_position_to_rotation_coincident() -> None:
    """Coincident position and focal point -> all zeros."""
    rx, ry, rz = _position_to_rotation(
        position=(50.0, 50.0, 30.0),
        focal_point=(50.0, 50.0, 30.0),
    )
    assert (rx, ry, rz) == (0.0, 0.0, 0.0)


@pytest.mark.usefixtures("mock_openvdb")
def test_position_to_rotation_returns_degrees() -> None:
    """Rotation values should be in degrees, not radians."""
    rx, ry, rz = _position_to_rotation(
        position=(50.0, 150.0, 130.0),
        focal_point=(50.0, 50.0, 30.0),
    )
    assert abs(rx) < 360
    assert abs(ry) < 360
    assert rz == 0.0


# ---------------------------------------------------------------------------
# _tf_to_color_ramp / _tf_to_opacity_ramp tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb")
def test_tf_to_color_ramp_sorted(sample_tf: MagicMock) -> None:
    """Color ramp entries must be sorted by pos."""
    ramp = _tf_to_color_ramp(sample_tf)
    positions = [entry["pos"] for entry in ramp]
    assert positions == sorted(positions)


@pytest.mark.usefixtures("mock_openvdb")
def test_tf_to_color_ramp_keys(sample_tf: MagicMock) -> None:
    """Each color ramp entry must have pos, r, g, b."""
    ramp = _tf_to_color_ramp(sample_tf)
    for entry in ramp:
        assert set(entry.keys()) == {"pos", "r", "g", "b"}


@pytest.mark.usefixtures("mock_openvdb")
def test_tf_to_opacity_ramp_sorted(sample_tf: MagicMock) -> None:
    """Opacity ramp entries must be sorted by pos."""
    ramp = _tf_to_opacity_ramp(sample_tf)
    positions = [entry["pos"] for entry in ramp]
    assert positions == sorted(positions)


@pytest.mark.usefixtures("mock_openvdb")
def test_tf_to_opacity_ramp_keys(sample_tf: MagicMock) -> None:
    """Each opacity ramp entry must have pos and opacity."""
    ramp = _tf_to_opacity_ramp(sample_tf)
    for entry in ramp:
        assert set(entry.keys()) == {"pos", "opacity"}


# ---------------------------------------------------------------------------
# Camera CHOP export tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb")
def test_camera_chop_file_created(
    camera_path_mock: MagicMock,
    tmp_path: Path,
) -> None:
    """CHOP file must be created."""
    path = export_td_camera_chop(camera_path_mock, tmp_path, n_frames=10)
    assert path.exists()
    assert path.suffix == ".tsv"


@pytest.mark.usefixtures("mock_openvdb")
def test_camera_chop_header(
    camera_path_mock: MagicMock,
    tmp_path: Path,
) -> None:
    """CHOP file header must include coordinate_system comment."""
    path = export_td_camera_chop(camera_path_mock, tmp_path, n_frames=5)
    text = path.read_text()
    assert "coordinate_system" in text
    assert "z_up" in text


@pytest.mark.usefixtures("mock_openvdb")
def test_camera_chop_row_count(
    camera_path_mock: MagicMock,
    tmp_path: Path,
) -> None:
    """CHOP file must have correct number of data rows."""
    n_frames = 12
    path = export_td_camera_chop(
        camera_path_mock,
        tmp_path,
        n_frames=n_frames,
    )
    lines = path.read_text().strip().splitlines()
    data_lines = [ln for ln in lines if not ln.startswith("#") and not ln.startswith("frame")]
    assert len(data_lines) == n_frames


@pytest.mark.usefixtures("mock_openvdb")
def test_camera_chop_values_parseable(
    camera_path_mock: MagicMock,
    tmp_path: Path,
) -> None:
    """All data values must be parseable as floats."""
    path = export_td_camera_chop(camera_path_mock, tmp_path, n_frames=5)
    lines = path.read_text().strip().splitlines()
    data_lines = [ln for ln in lines if not ln.startswith("#") and not ln.startswith("frame")]
    for line in data_lines:
        parts = line.split("\t")
        assert len(parts) == 7
        for p in parts:
            float(p)


# ---------------------------------------------------------------------------
# Manifest export tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb")
def test_manifest_required_keys(
    app_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Manifest must contain all required keys."""
    path = export_td_manifest(app_config, tmp_path, frame_count=100)
    data = json.loads(path.read_text())
    required = {
        "frame_count",
        "fps",
        "vdb_pattern",
        "coordinate_system",
        "creator",
        "grid_names",
    }
    assert required.issubset(set(data.keys()))


@pytest.mark.usefixtures("mock_openvdb")
def test_manifest_frame_count(
    app_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Manifest frame_count must match input."""
    path = export_td_manifest(app_config, tmp_path, frame_count=42)
    data = json.loads(path.read_text())
    assert data["frame_count"] == 42


@pytest.mark.usefixtures("mock_openvdb")
def test_manifest_includes_tf(
    app_config: MagicMock,
    sample_tf: MagicMock,
    tmp_path: Path,
) -> None:
    """Manifest includes color_ramp and opacity_ramp when TF is provided."""
    path = export_td_manifest(
        app_config,
        tmp_path,
        frame_count=10,
        transfer_function=sample_tf,
    )
    data = json.loads(path.read_text())
    assert "color_ramp" in data
    assert "opacity_ramp" in data
    assert len(data["color_ramp"]) == 3
    assert len(data["opacity_ramp"]) == 3


@pytest.mark.usefixtures("mock_openvdb")
def test_manifest_includes_camera(
    app_config: MagicMock,
    camera_path_mock: MagicMock,
    tmp_path: Path,
) -> None:
    """Manifest includes camera_keyframes when camera_path is provided."""
    path = export_td_manifest(
        app_config,
        tmp_path,
        frame_count=5,
        camera_path=camera_path_mock,
    )
    data = json.loads(path.read_text())
    assert "camera_keyframes" in data
    assert len(data["camera_keyframes"]) == 5


# ---------------------------------------------------------------------------
# Point cloud export tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb")
def test_point_cloud_header(
    grid_cfg: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """Point cloud CSV must have correct header."""
    path = export_point_cloud(
        sample_concentration,
        grid_cfg,
        tmp_path / "pts.csv",
    )
    first_line = path.read_text().splitlines()[0]
    assert first_line == "x,y,z,density"


@pytest.mark.usefixtures("mock_openvdb")
def test_point_cloud_threshold_filtering(tmp_path: Path) -> None:
    """Only voxels above threshold should appear in point cloud."""
    data = np.array([[[0.001, 0.5], [0.0, 0.9]]], dtype=np.float32)
    cfg = MagicMock()
    cfg.dx = 10.0
    cfg.dy = 10.0
    cfg.dz = 5.0
    path = export_point_cloud(data, cfg, tmp_path / "pts.csv", threshold=0.01)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 3


@pytest.mark.usefixtures("mock_openvdb")
def test_point_cloud_world_coords(tmp_path: Path) -> None:
    """World coordinates = index * spacing."""
    data = np.zeros((2, 2, 2), dtype=np.float32)
    data[1, 1, 1] = 1.0

    cfg = MagicMock()
    cfg.dx = 100.0
    cfg.dy = 200.0
    cfg.dz = 50.0

    path = export_point_cloud(data, cfg, tmp_path / "pts.csv", threshold=0.5)
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 2
    parts = lines[1].split(",")
    x, y, z, density = (
        float(parts[0]),
        float(parts[1]),
        float(parts[2]),
        float(parts[3]),
    )
    assert x == pytest.approx(100.0)
    assert y == pytest.approx(200.0)
    assert z == pytest.approx(50.0)
    assert density == pytest.approx(1.0)


@pytest.mark.usefixtures("mock_openvdb")
def test_point_cloud_empty(
    grid_cfg: MagicMock,
    tmp_path: Path,
) -> None:
    """When all values are below threshold, CSV has only a header."""
    data = np.full((4, 4, 4), 0.001, dtype=np.float32)
    path = export_point_cloud(
        data,
        grid_cfg,
        tmp_path / "pts.csv",
        threshold=0.01,
    )
    lines = path.read_text().strip().splitlines()
    assert len(lines) == 1


# ---------------------------------------------------------------------------
# VDB frame export tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_mock_export_vdb")
def test_vdb_frame_copy_from_array(
    mock_openvdb: MagicMock,
    app_config: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """grid.copyFromArray must be called (not per-voxel iteration)."""
    export_td_vdb_frame(
        sample_concentration,
        None,
        tmp_path,
        frame=0,
        config=app_config,
    )
    mock_grid = mock_openvdb.FloatGrid.return_value
    mock_grid.copyFromArray.assert_called_once()


@pytest.mark.usefixtures("_mock_export_vdb")
def test_vdb_frame_non_uniform_transform(
    mock_openvdb: MagicMock,
    app_config: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """Non-uniform voxels (dx != dz) must use matrix transform."""
    export_td_vdb_frame(
        sample_concentration,
        None,
        tmp_path,
        frame=0,
        config=app_config,
    )
    call_args = mock_openvdb.createLinearTransform.call_args
    assert call_args is not None
    assert "matrix" in call_args.kwargs


@pytest.mark.usefixtures("_mock_export_vdb")
def test_vdb_frame_naming(
    mock_openvdb: MagicMock,
    app_config: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """VDB frame file naming must be plume_{frame:06d}.vdb."""
    _ = mock_openvdb  # activates fixture; inspected indirectly via openvdb.write
    path = export_td_vdb_frame(
        sample_concentration,
        None,
        tmp_path,
        frame=42,
        config=app_config,
    )
    assert path.name == "plume_000042.vdb"


@pytest.mark.usefixtures("_mock_export_vdb")
def test_vdb_frame_metadata(
    mock_openvdb: MagicMock,
    app_config: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """VDB grids must have metadata attached."""
    export_td_vdb_frame(
        sample_concentration,
        None,
        tmp_path,
        frame=7,
        config=app_config,
        metadata={"custom_key": "custom_value"},
    )
    mock_grid = mock_openvdb.FloatGrid.return_value
    mock_grid.__setitem__.assert_called()


@pytest.mark.usefixtures("_mock_export_vdb")
def test_vdb_frame_grid_name(
    mock_openvdb: MagicMock,
    app_config: MagicMock,
    sample_concentration: np.ndarray,
    tmp_path: Path,
) -> None:
    """Density grid must be named 'density'."""
    export_td_vdb_frame(
        sample_concentration,
        None,
        tmp_path,
        frame=0,
        config=app_config,
    )
    mock_grid = mock_openvdb.FloatGrid.return_value
    assert mock_grid.name == "density"


# ---------------------------------------------------------------------------
# VDB sequence export tests
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_openvdb", "_mock_export_vdb")
def test_vdb_sequence_file_count(
    app_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Sequence must produce one VDB per frame."""
    frames = [np.random.default_rng(i).random((4, 4, 4)).astype(np.float32) for i in range(5)]
    paths = export_td_vdb_sequence(frames, None, app_config, tmp_path)
    assert len(paths) == 5


@pytest.mark.usefixtures("mock_openvdb", "_mock_export_vdb")
def test_vdb_sequence_ordering(
    app_config: MagicMock,
    tmp_path: Path,
) -> None:
    """Sequence files must be numbered in order."""
    frames = [np.random.default_rng(i).random((4, 4, 4)).astype(np.float32) for i in range(3)]
    paths = export_td_vdb_sequence(frames, None, app_config, tmp_path)
    names = [p.name for p in paths]
    assert names == [
        "plume_000000.vdb",
        "plume_000001.vdb",
        "plume_000002.vdb",
    ]


# ---------------------------------------------------------------------------
# _create_vdb_transform tests
# ---------------------------------------------------------------------------


def test_create_vdb_transform_uniform(mock_openvdb: MagicMock) -> None:
    """Uniform voxels should use voxelSize parameter."""
    cfg = MagicMock()
    cfg.dx = 100.0
    cfg.dy = 100.0
    cfg.dz = 100.0

    _create_vdb_transform(cfg)
    call_args = mock_openvdb.createLinearTransform.call_args
    assert "voxelSize" in call_args.kwargs


def test_create_vdb_transform_non_uniform(mock_openvdb: MagicMock) -> None:
    """Non-uniform voxels should use matrix parameter."""
    cfg = MagicMock()
    cfg.dx = 100.0
    cfg.dy = 100.0
    cfg.dz = 50.0

    _create_vdb_transform(cfg)
    call_args = mock_openvdb.createLinearTransform.call_args
    assert "matrix" in call_args.kwargs
