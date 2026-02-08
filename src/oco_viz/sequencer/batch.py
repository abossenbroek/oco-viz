"""Batch render manager with progress tracking and crash recovery."""

from __future__ import annotations

import gc
import json
import logging
import sys
import time
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from pathlib import Path

    from oco_viz.config.schema import AppConfig

logger = logging.getLogger(__name__)


@attrs.frozen
class BatchResult:
    """Immutable result of a batch render run."""

    total_frames: int
    completed_frames: int
    elapsed_seconds: float
    avg_seconds_per_frame: float
    status: str  # "completed" | "failed" | "partial"
    error: str | None = None


@attrs.frozen
class ProgressState:
    """Immutable snapshot of batch render progress."""

    total_frames: int
    completed: int
    elapsed_seconds: float
    avg_seconds_per_frame: float
    estimated_remaining_seconds: float
    last_frame: int
    status: str  # "running" | "completed" | "failed"
    error: str | None = None


def write_progress(output_dir: Path, state: ProgressState) -> Path:
    """Serialize ProgressState to JSON atomically.

    Writes to a temporary file then atomically replaces to prevent corruption.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / "progress.json"
    tmp_path = output_dir / "progress.json.tmp"

    data = attrs.asdict(state)
    tmp_path.write_text(json.dumps(data, indent=2))
    tmp_path.replace(progress_path)

    return progress_path


def _format_eta(seconds: float) -> str:
    """Format seconds into human-readable ETA string."""
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    if total < 3600:
        m, s = divmod(total, 60)
        return f"{m}m {s}s"
    h, remainder = divmod(total, 3600)
    m = remainder // 60
    return f"{h}h {m}m"


def format_progress_bar(completed: int, total: int, elapsed: float) -> str:
    """Format a progress bar string for terminal display.

    Example: ``Frame 450/2160 [========>               ] 20.8% | 8.0s/f | ETA 3h48m``
    """
    pct = (completed / total * 100.0) if total > 0 else 0.0
    bar_width = 24
    filled = int(bar_width * completed / total) if total > 0 else 0
    bar = "=" * filled
    if filled < bar_width:
        bar += ">"
    bar = bar.ljust(bar_width)

    avg = elapsed / completed if completed > 0 else 0.0
    remaining = avg * (total - completed) if completed > 0 else 0.0
    eta = _format_eta(remaining)

    return f"Frame {completed}/{total} [{bar}] {pct:.1f}% | {avg:.1f}s/f | ETA {eta}"


class BatchRenderManager:
    """Manages chunked batch rendering with progress tracking and crash recovery."""

    def __init__(
        self,
        zarr_path: Path,
        output_dir: Path,
        config: AppConfig,
        chunk_size: int = 100,
    ) -> None:
        self._zarr_path = zarr_path
        self._output_dir = output_dir
        self._config = config
        self._chunk_size = chunk_size

    def run(self) -> BatchResult:
        """Render from scratch (start_frame=0)."""
        return self._execute(start_from=0)

    def resume(self) -> BatchResult:
        """Scan existing frames in output_dir, continue from first missing."""
        self._output_dir.mkdir(parents=True, exist_ok=True)
        existing = sorted(self._output_dir.glob("frame_*.png"))
        start_from = len(existing)
        logger.info("Resume: found %d existing frames, starting from %d", start_from, start_from)
        return self._execute(start_from=start_from)

    def _execute(self, *, start_from: int = 0) -> BatchResult:
        """Core chunked render loop with progress tracking."""
        from oco_viz.data.zarr_store import read_zarr  # noqa: PLC0415
        from oco_viz.sequencer.controller import render_sequence  # noqa: PLC0415

        ds = read_zarr(self._zarr_path)
        total = ds.sizes["time"]

        # Build config with output_dir
        updated_output = self._config.output.model_copy(
            update={"frames_dir": str(self._output_dir)}
        )
        updated_config = self._config.model_copy(update={"output": updated_output})

        completed = start_from
        t_start = time.monotonic()

        try:
            chunk_start = start_from
            while chunk_start < total:
                chunk_end = min(chunk_start + self._chunk_size, total)

                render_sequence(
                    updated_config,
                    self._zarr_path,
                    num_frames=total,
                    start_frame=chunk_start,
                    end_frame=chunk_end,
                )

                completed = chunk_end
                elapsed = time.monotonic() - t_start
                rendered = completed - start_from
                avg = elapsed / rendered if rendered > 0 else 0.0
                remaining = avg * (total - completed)

                state = ProgressState(
                    total_frames=total,
                    completed=completed,
                    elapsed_seconds=elapsed,
                    avg_seconds_per_frame=avg,
                    estimated_remaining_seconds=remaining,
                    last_frame=chunk_end - 1,
                    status="running" if completed < total else "completed",
                )
                write_progress(self._output_dir, state)

                bar = format_progress_bar(completed, total, elapsed)
                print(f"\r{bar}", end="", file=sys.stderr, flush=True)

                gc.collect()
                chunk_start = chunk_end

        except Exception as exc:  # noqa: BLE001
            elapsed = time.monotonic() - t_start
            rendered = completed - start_from
            avg = elapsed / rendered if rendered > 0 else 0.0
            error_msg = f"{type(exc).__name__}: {exc}"

            error_state = ProgressState(
                total_frames=total,
                completed=completed,
                elapsed_seconds=elapsed,
                avg_seconds_per_frame=avg,
                estimated_remaining_seconds=0.0,
                last_frame=max(completed - 1, 0),
                status="failed",
                error=error_msg,
            )
            write_progress(self._output_dir, error_state)

            return BatchResult(
                total_frames=total,
                completed_frames=completed,
                elapsed_seconds=elapsed,
                avg_seconds_per_frame=avg,
                status="failed",
                error=error_msg,
            )

        elapsed = time.monotonic() - t_start
        rendered = completed - start_from
        avg = elapsed / rendered if rendered > 0 else 0.0

        # Write final completed state
        final_state = ProgressState(
            total_frames=total,
            completed=completed,
            elapsed_seconds=elapsed,
            avg_seconds_per_frame=avg,
            estimated_remaining_seconds=0.0,
            last_frame=max(completed - 1, 0),
            status="completed",
        )
        write_progress(self._output_dir, final_state)

        return BatchResult(
            total_frames=total,
            completed_frames=completed,
            elapsed_seconds=elapsed,
            avg_seconds_per_frame=avg,
            status="completed",
        )
