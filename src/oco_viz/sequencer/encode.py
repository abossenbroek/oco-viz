"""FFmpeg video encoding from PNG sequences with multi-codec support."""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import AppConfig, EncodingConfig

logger = logging.getLogger(__name__)

# (ffmpeg_args, extension, supports_crf)
CODEC_PRESETS: dict[str, tuple[list[str], str, bool]] = {
    "h264": (["-c:v", "libx264", "-pix_fmt", "yuv420p"], ".mp4", True),
    "h265": (["-c:v", "libx265"], ".mp4", True),
    "prores4444": (
        ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"],
        ".mov",
        False,
    ),
    "dnxhr_hqx": (
        ["-c:v", "dnxhd", "-profile:v", "dnxhr_hqx", "-pix_fmt", "yuv422p10le"],
        ".mxf",
        False,
    ),
}

# Encoder names used by ffmpeg -codecs output for each codec key
_ENCODER_NAMES: dict[str, str] = {
    "h264": "libx264",
    "h265": "libx265",
    "prores4444": "prores_ks",
    "dnxhr_hqx": "dnxhd",
}


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a TrueType font with graceful fallback."""
    candidates = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "Helvetica.ttf",
        "Arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def encode_video(
    frames_dir: Path,
    output_path: Path,
    *,
    fps: int = 24,
    pattern: str = "frame_%06d.png",
    encoding: EncodingConfig | None = None,
) -> Path:
    """Encode PNG sequence to video using ffmpeg.

    Parameters
    ----------
    frames_dir
        Directory containing numbered PNG frames.
    output_path
        Destination file path (extension may be auto-corrected).
    fps
        Frames per second.
    pattern
        Frame filename pattern for ffmpeg input.
    encoding
        Encoding configuration. ``None`` falls back to H.264 defaults.

    Returns
    -------
    Path
        The actual output path (may differ from input if extension was corrected).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if encoding is None:
        # Backward-compatible H.264 default
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

    # PNG codec: copy frames to output directory
    if encoding.codec == "png":
        output_path.mkdir(parents=True, exist_ok=True)
        for src in sorted(frames_dir.glob("*.png")):
            shutil.copy2(src, output_path / src.name)
        n_copied = len(list(output_path.glob("*.png")))
        logger.info("Copied %d PNG frames to %s", n_copied, output_path)
        return output_path

    # Build ffmpeg command from preset
    preset_args, correct_ext, supports_crf = CODEC_PRESETS[encoding.codec]

    # Auto-correct extension
    if output_path.suffix != correct_ext:
        output_path = output_path.with_suffix(correct_ext)

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / pattern),
        *preset_args,
    ]

    # Override pixel format if specified
    if encoding.pixel_format is not None:
        if "-pix_fmt" in cmd:
            pf_idx = cmd.index("-pix_fmt")
            cmd[pf_idx + 1] = encoding.pixel_format
        else:
            cmd.extend(["-pix_fmt", encoding.pixel_format])

    # Add CRF if supported
    if supports_crf:
        cmd.extend(["-crf", str(encoding.crf)])

    cmd.append(str(output_path))

    logger.info("Encoding video: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603

    if result.returncode != 0:
        msg = f"ffmpeg failed: {result.stderr}"
        raise RuntimeError(msg)

    logger.info("Video encoded: %s", output_path)
    return output_path


def validate_ffmpeg_codec(codec: str) -> bool:
    """Check whether ffmpeg supports the given codec.

    Returns ``True`` for ``"png"`` unconditionally. For other codecs,
    runs ``ffmpeg -codecs`` and checks whether the encoder name appears.
    """
    if codec == "png":
        return True

    encoder_name = _ENCODER_NAMES.get(codec, codec)
    try:
        result = subprocess.run(
            ["ffmpeg", "-codecs"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False

    return encoder_name in result.stdout


def generate_slate(config: AppConfig) -> list[NDArray[np.uint8]]:
    """Generate title-slate frames as a list of uint8 numpy arrays.

    Produces ``config.output.fps * config.encoding.slate_duration_s`` identical
    frames at ``config.output.width x config.output.height`` resolution.
    """
    w, h = config.output.width, config.output.height
    num_frames = int(config.output.fps * config.encoding.slate_duration_s)

    # Near-black vertical gradient background
    img = Image.new("RGB", (w, h))
    pixels = np.zeros((h, w, 3), dtype=np.uint8)
    top = np.array([5, 5, 15], dtype=np.float64)
    bottom = np.array([15, 15, 25], dtype=np.float64)
    for row in range(h):
        t = row / max(h - 1, 1)
        color = (top * (1 - t) + bottom * t).astype(np.uint8)
        pixels[row, :] = color
    img = Image.fromarray(pixels, mode="RGB")
    draw = ImageDraw.Draw(img)

    # Text styling
    text_color = (170, 170, 170)
    base_size = max(h // 30, 16)
    font_large = _load_font(base_size * 2)
    font_normal = _load_font(base_size)

    # Lines
    lines = [
        ("Highveld Industrial Corridor CO2 Visualization", font_large),
        (f"{config.data_source.start_date} — {config.data_source.end_date}", font_normal),
        ("Data: NASA OCO-2/3 | ECMWF ERA5 | NOAA GML", font_normal),
        ("Generated by oco-viz", font_normal),
    ]

    # Compute total block height for vertical centering
    line_gap = base_size
    total_height = sum(
        draw.textbbox((0, 0), text, font=font)[3] - draw.textbbox((0, 0), text, font=font)[1]
        for text, font in lines
    ) + line_gap * (len(lines) - 1)

    y = (h - total_height) // 2
    for text, font in lines:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (w - tw) // 2
        draw.text((x, y), text, font=font, fill=text_color)
        y += th + line_gap

    frame_arr: NDArray[np.uint8] = np.array(img, dtype=np.uint8)
    return [frame_arr.copy() for _ in range(num_frames)]


def prepare_frames_with_slate(
    frames_dir: Path,
    slate_frames: list[NDArray[np.uint8]],
    work_dir: Path,
) -> Path:
    """Combine slate frames and render frames into a single directory.

    Slate frames are written first (indices 0..N-1), then render frames are
    symlinked (or copied) at indices N..N+M-1. The original ``frames_dir`` is
    never modified.

    Returns
    -------
    Path
        The work directory containing the combined sequence.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    # Write slate frames
    for i, frame in enumerate(slate_frames):
        img = Image.fromarray(frame)
        img.save(work_dir / f"frame_{i:06d}.png")

    # Symlink (or copy) render frames
    offset = len(slate_frames)
    render_frames = sorted(frames_dir.glob("frame_*.png"))
    for j, src in enumerate(render_frames):
        dst = work_dir / f"frame_{offset + j:06d}.png"
        try:
            dst.symlink_to(src.resolve())
        except OSError:
            shutil.copy2(src, dst)

    return work_dir
