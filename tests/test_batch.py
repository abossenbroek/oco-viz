"""Tests for batch render manager with progress tracking and recovery."""

from __future__ import annotations

import gc
import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import attrs
import numpy as np
import pytest
import xarray as xr

from oco_viz.sequencer.batch import (
    BatchRenderManager,
    BatchResult,
    ProgressState,
    _format_eta,
    format_progress_bar,
    write_progress,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_render() -> tuple[MagicMock, MagicMock]:
    """Mock render_sequence and read_zarr via patch."""
    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((10, 4, 4, 4), dtype=np.float32))},
    )

    mock_read = MagicMock(return_value=ds)
    mock_render_seq = MagicMock(return_value=[])

    with (
        patch("oco_viz.data.zarr_store.read_zarr", mock_read),
        patch("oco_viz.sequencer.controller.render_sequence", mock_render_seq),
    ):
        yield mock_read, mock_render_seq


@pytest.fixture
def config() -> MagicMock:
    """Minimal mock config with model_copy support."""
    output = MagicMock()
    output.frames_dir = "output/frames"
    output.model_copy = MagicMock(return_value=output)

    cfg = MagicMock()
    cfg.output = output
    cfg.model_copy = MagicMock(return_value=cfg)
    return cfg


# ---------------------------------------------------------------------------
# format_progress_bar tests
# ---------------------------------------------------------------------------


def test_progress_bar_zero_completed() -> None:
    bar = format_progress_bar(0, 100, 0.0)
    assert "0.0%" in bar
    assert "0/100" in bar


def test_progress_bar_halfway() -> None:
    bar = format_progress_bar(50, 100, 100.0)
    assert "50.0%" in bar
    assert "50/100" in bar


def test_progress_bar_complete() -> None:
    bar = format_progress_bar(100, 100, 200.0)
    assert "100.0%" in bar
    assert "100/100" in bar


# ---------------------------------------------------------------------------
# _format_eta tests
# ---------------------------------------------------------------------------


def test_format_eta_zero() -> None:
    assert _format_eta(0.0) == "0s"


def test_format_eta_seconds_only() -> None:
    assert _format_eta(45.0) == "45s"


def test_format_eta_minutes_seconds() -> None:
    result = _format_eta(125.0)
    assert "2m" in result
    assert "5s" in result


def test_format_eta_hours_minutes() -> None:
    result = _format_eta(3725.0)
    assert "1h" in result
    assert "2m" in result


# ---------------------------------------------------------------------------
# write_progress tests
# ---------------------------------------------------------------------------


def test_write_progress_creates_file(tmp_path: Path) -> None:
    state = ProgressState(
        total_frames=100,
        completed=50,
        elapsed_seconds=100.0,
        avg_seconds_per_frame=2.0,
        estimated_remaining_seconds=100.0,
        last_frame=49,
        status="running",
    )
    path = write_progress(tmp_path, state)
    assert path.exists()
    assert path.name == "progress.json"

    data = json.loads(path.read_text())
    assert data["total_frames"] == 100
    assert data["completed"] == 50
    assert data["status"] == "running"


def test_write_progress_valid_json(tmp_path: Path) -> None:
    state = ProgressState(
        total_frames=10,
        completed=5,
        elapsed_seconds=50.0,
        avg_seconds_per_frame=10.0,
        estimated_remaining_seconds=50.0,
        last_frame=4,
        status="running",
    )
    path = write_progress(tmp_path, state)
    data = json.loads(path.read_text())
    assert set(data.keys()) == {
        "total_frames",
        "completed",
        "elapsed_seconds",
        "avg_seconds_per_frame",
        "estimated_remaining_seconds",
        "last_frame",
        "status",
        "error",
    }


def test_write_progress_overwrites(tmp_path: Path) -> None:
    state1 = ProgressState(
        total_frames=100,
        completed=10,
        elapsed_seconds=10.0,
        avg_seconds_per_frame=1.0,
        estimated_remaining_seconds=90.0,
        last_frame=9,
        status="running",
    )
    write_progress(tmp_path, state1)

    state2 = ProgressState(
        total_frames=100,
        completed=50,
        elapsed_seconds=50.0,
        avg_seconds_per_frame=1.0,
        estimated_remaining_seconds=50.0,
        last_frame=49,
        status="running",
    )
    path = write_progress(tmp_path, state2)
    data = json.loads(path.read_text())
    assert data["completed"] == 50


# ---------------------------------------------------------------------------
# BatchResult / ProgressState attrs tests
# ---------------------------------------------------------------------------


def test_batch_result_frozen() -> None:
    result = BatchResult(
        total_frames=100,
        completed_frames=100,
        elapsed_seconds=200.0,
        avg_seconds_per_frame=2.0,
        status="completed",
    )
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        result.status = "failed"  # type: ignore[misc]


def test_batch_result_default_error() -> None:
    result = BatchResult(
        total_frames=100,
        completed_frames=100,
        elapsed_seconds=200.0,
        avg_seconds_per_frame=2.0,
        status="completed",
    )
    assert result.error is None


def test_progress_state_frozen() -> None:
    state = ProgressState(
        total_frames=100,
        completed=50,
        elapsed_seconds=100.0,
        avg_seconds_per_frame=2.0,
        estimated_remaining_seconds=100.0,
        last_frame=49,
        status="running",
    )
    with pytest.raises(attrs.exceptions.FrozenInstanceError):
        state.status = "failed"  # type: ignore[misc]


def test_progress_state_default_error() -> None:
    state = ProgressState(
        total_frames=100,
        completed=50,
        elapsed_seconds=100.0,
        avg_seconds_per_frame=2.0,
        estimated_remaining_seconds=100.0,
        last_frame=49,
        status="running",
    )
    assert state.error is None


# ---------------------------------------------------------------------------
# BatchRenderManager tests
# ---------------------------------------------------------------------------


def test_batch_renders_correct_chunks(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """250 frames / 100 chunk_size = 3 calls (100+100+50)."""
    mock_read, mock_render_seq = mock_render

    # 250-frame dataset
    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((250, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=tmp_path / "frames",
        config=config,
        chunk_size=100,
    )
    result = manager.run()

    assert mock_render_seq.call_count == 3
    assert result.status == "completed"
    assert result.total_frames == 250
    assert result.completed_frames == 250


def test_batch_correct_start_end_per_chunk(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """Each call should have correct start_frame and end_frame."""
    mock_read, mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((250, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=tmp_path / "frames",
        config=config,
        chunk_size=100,
    )
    manager.run()

    calls = mock_render_seq.call_args_list
    # Chunk 0: start=0, end=100
    assert calls[0].kwargs["start_frame"] == 0
    assert calls[0].kwargs["end_frame"] == 100
    # Chunk 1: start=100, end=200
    assert calls[1].kwargs["start_frame"] == 100
    assert calls[1].kwargs["end_frame"] == 200
    # Chunk 2: start=200, end=250
    assert calls[2].kwargs["start_frame"] == 200
    assert calls[2].kwargs["end_frame"] == 250


def test_batch_resume_skips_existing(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """Resume mode should start from first missing frame."""
    mock_read, mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((10, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    # Create 5 existing frames
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir(parents=True)
    for i in range(5):
        (frames_dir / f"frame_{i:06d}.png").touch()

    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=frames_dir,
        config=config,
        chunk_size=100,
    )
    result = manager.resume()

    # Should call render_sequence starting from frame 5
    assert mock_render_seq.call_count == 1
    assert mock_render_seq.call_args.kwargs["start_frame"] == 5
    assert result.status == "completed"


def test_batch_writes_progress_each_chunk(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """progress.json should be written after each chunk."""
    mock_read, _mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((250, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    frames_dir = tmp_path / "frames"
    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=frames_dir,
        config=config,
        chunk_size=100,
    )
    manager.run()

    progress_path = frames_dir / "progress.json"
    assert progress_path.exists()
    data = json.loads(progress_path.read_text())
    assert data["status"] == "completed"
    assert data["completed"] == 250


def test_batch_error_saves_failed_state(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """On exception, should return failed result with error message."""
    mock_read, mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((10, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds
    mock_render_seq.side_effect = RuntimeError("VTK crashed")

    frames_dir = tmp_path / "frames"
    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=frames_dir,
        config=config,
        chunk_size=100,
    )
    result = manager.run()

    assert result.status == "failed"
    assert result.error is not None
    assert "VTK crashed" in result.error

    progress_path = frames_dir / "progress.json"
    assert progress_path.exists()
    data = json.loads(progress_path.read_text())
    assert data["status"] == "failed"


def test_batch_gc_collect_called(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    """gc.collect should be called after each chunk."""
    mock_read, _mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((250, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=tmp_path / "frames",
        config=config,
        chunk_size=100,
    )

    with patch.object(gc, "collect", wraps=gc.collect) as mock_gc:
        manager.run()
        assert mock_gc.call_count >= 3


def test_batch_completed_status_on_success(
    tmp_path: Path, mock_render: tuple[MagicMock, MagicMock], config: MagicMock
) -> None:
    mock_read, _mock_render_seq = mock_render

    ds = xr.Dataset(
        {"concentration": (("time", "z", "y", "x"), np.zeros((10, 4, 4, 4), dtype=np.float32))},
    )
    mock_read.return_value = ds

    manager = BatchRenderManager(
        zarr_path=tmp_path / "plume.zarr",
        output_dir=tmp_path / "frames",
        config=config,
        chunk_size=100,
    )
    result = manager.run()

    assert result.status == "completed"
    assert result.completed_frames == 10
    assert result.elapsed_seconds >= 0
    assert result.avg_seconds_per_frame >= 0
