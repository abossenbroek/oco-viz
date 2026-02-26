"""Progress tracking for gallery rendering."""

from __future__ import annotations

import sys
import time


def _format_eta(seconds: float) -> str:
    """Format seconds into human-readable ETA string.

    Examples: ``12s``, ``3m 45s``, ``1h 12m``.
    """
    total = int(seconds)
    if total < 60:
        return f"{total}s"
    if total < 3600:
        m, s = divmod(total, 60)
        return f"{m}m {s}s"
    h, remainder = divmod(total, 3600)
    m = remainder // 60
    return f"{h}h {m}m"


class GalleryProgress:
    """Track rendering progress across waves and images.

    Parameters
    ----------
    total_images
        Total number of images to render across all waves.
    """

    def __init__(self, total_images: int) -> None:
        self.total_images = total_images
        self.completed: int = 0
        self.failed: int = 0
        self._start_time = time.monotonic()
        self._wave_starts: dict[str, float] = {}
        self._current_wave: str | None = None

    def begin_wave(self, wave_name: str) -> None:
        """Mark the start of a new wave."""
        self._current_wave = wave_name
        self._wave_starts[wave_name] = time.monotonic()

    def image_done(self, image_name: str, *, success: bool = True) -> None:
        """Record completion of a single image render."""
        if success:
            self.completed += 1
        else:
            self.failed += 1
        self._print_progress(image_name)

    @property
    def elapsed(self) -> float:
        """Total elapsed seconds since construction."""
        return time.monotonic() - self._start_time

    def _print_progress(self, image_name: str) -> None:
        """Print a carriage-return progress line to stderr."""
        done = self.completed + self.failed
        pct = (done / self.total_images * 100.0) if self.total_images > 0 else 0.0
        avg = self.elapsed / done if done > 0 else 0.0
        remaining = avg * (self.total_images - done) if done > 0 else 0.0
        eta = _format_eta(remaining)
        bar_width = 24
        filled = int(bar_width * done / self.total_images) if self.total_images > 0 else 0
        bar = "=" * filled
        if filled < bar_width:
            bar += ">"
        bar = bar.ljust(bar_width)
        line = (
            f"\r  [{bar}] {done}/{self.total_images} ({pct:.0f}%)"
            f" | {avg:.1f}s/img | ETA {eta} | {image_name}"
        )
        sys.stderr.write(line)
        sys.stderr.flush()
        if done == self.total_images:
            sys.stderr.write("\n")

    def summary(self) -> dict[str, object]:
        """Return a summary dict for logging."""
        return {
            "total": self.total_images,
            "completed": self.completed,
            "failed": self.failed,
            "elapsed": round(self.elapsed, 1),
        }


class DryRunProgress:
    """Collect image names without rendering (for --dry-run mode)."""

    def __init__(self) -> None:
        self.images: list[str] = []
        self._current_wave: str | None = None

    def begin_wave(self, wave_name: str) -> None:
        """Record the current wave."""
        self._current_wave = wave_name

    def image_done(self, image_name: str, *, success: bool = True) -> None:  # noqa: ARG002
        """Record the image name (no rendering occurs)."""
        prefix = f"{self._current_wave}/" if self._current_wave else ""
        self.images.append(f"{prefix}{image_name}")

    @property
    def total_images(self) -> int:
        """Number of images collected."""
        return len(self.images)
