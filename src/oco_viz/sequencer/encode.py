"""FFmpeg video encoding from PNG sequences."""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


def encode_video(
    frames_dir: Path,
    output_path: Path,
    *,
    fps: int = 24,
    pattern: str = "frame_%06d.png",
) -> Path:
    """Encode PNG sequence to H.264 MP4 using ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / pattern),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        str(output_path),
    ]

    logger.info("Encoding video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603

    if result.returncode != 0:
        msg = f"ffmpeg failed: {result.stderr}"
        raise RuntimeError(msg)

    logger.info("Video encoded: %s", output_path)
    return output_path
