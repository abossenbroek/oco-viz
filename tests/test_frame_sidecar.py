"""Tests for YAML sidecar metadata writer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from oco_viz.render.camera import CameraState
from oco_viz.render.frame_sidecar import write_sidecar

if TYPE_CHECKING:
    from pathlib import Path


def test_write_sidecar_creates_yaml(tmp_path: Path) -> None:
    path = tmp_path / "frame_000042.yaml"
    camera = CameraState(
        position=(200.0, 200.0, 100.0),
        focal_point=(50.0, 50.0, 30.0),
    )
    stats = {"min": 0.0, "max": 1.5, "mean": 0.3}
    result = write_sidecar(
        path,
        frame_index=42,
        timestamp=3.5,
        camera_state=camera,
        concentration_stats=stats,
    )

    assert result == path
    assert path.exists()

    with path.open() as f:
        data = yaml.safe_load(f)

    assert data["frame_index"] == 42
    assert data["timestamp"] == 3.5
    assert data["camera"]["position"] == [200.0, 200.0, 100.0]
    assert data["camera"]["focal_point"] == [50.0, 50.0, 30.0]
    assert data["concentration"]["min"] == 0.0
    assert data["concentration"]["max"] == 1.5
    assert data["concentration"]["mean"] == 0.3


def test_write_sidecar_creates_parent_dirs(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "dir" / "frame_000000.yaml"
    camera = CameraState(position=(0.0, 0.0, 0.0), focal_point=(1.0, 1.0, 1.0))
    stats = {"min": 0.0, "max": 0.0, "mean": 0.0}
    write_sidecar(
        path,
        frame_index=0,
        timestamp=0.0,
        camera_state=camera,
        concentration_stats=stats,
    )
    assert path.exists()
