import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from oco_viz.sequencer.encode import encode_video


def _create_test_frames(frames_dir: Path, n: int = 5, size: int = 64) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        arr = np.random.default_rng(i).integers(0, 255, (size, size, 3), dtype=np.uint8)
        Image.fromarray(arr).save(frames_dir / f"frame_{i:06d}.png")


def test_encode_video(tmp_path):
    frames_dir = tmp_path / "frames"
    _create_test_frames(frames_dir, n=5)

    output = tmp_path / "video" / "test.mp4"
    result = encode_video(frames_dir, output, fps=24)
    assert result.exists()
    assert result.stat().st_size > 0


def test_ffprobe_h264(tmp_path):
    frames_dir = tmp_path / "frames"
    _create_test_frames(frames_dir, n=5)

    output = tmp_path / "test.mp4"
    encode_video(frames_dir, output, fps=24)

    # Check with ffprobe
    probe = subprocess.run(  # noqa: S603
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    info = json.loads(probe.stdout)
    stream = info["streams"][0]
    assert stream["codec_name"] == "h264"
    assert int(stream["width"]) == 64
    assert int(stream["height"]) == 64
