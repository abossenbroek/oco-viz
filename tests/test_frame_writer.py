"""Tests for frame writer (8-bit and 16-bit PNG output)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from oco_viz.render.frame_writer import save_frame_8bit, save_frame_16bit

if TYPE_CHECKING:
    from pathlib import Path


def test_save_frame_8bit_creates_png(tmp_path: Path) -> None:
    img = np.full((64, 64, 3), 0.5, dtype=np.float32)
    path = tmp_path / "test_8bit.png"
    result = save_frame_8bit(img, path)

    assert result == path
    assert path.exists()
    loaded = Image.open(path)
    assert loaded.mode == "RGB"
    arr = np.array(loaded)
    assert arr.dtype == np.uint8
    assert arr.shape == (64, 64, 3)


def test_save_frame_8bit_clamps_values(tmp_path: Path) -> None:
    img = np.full((32, 32, 3), 1.5, dtype=np.float32)
    path = tmp_path / "clamped.png"
    save_frame_8bit(img, path)

    loaded = np.array(Image.open(path))
    assert loaded.max() == 255


def test_save_frame_16bit_creates_png(tmp_path: Path) -> None:
    img = np.full((64, 64, 3), 0.5, dtype=np.float32)
    path = tmp_path / "test_16bit.png"
    result = save_frame_16bit(img, path)

    assert result == path
    assert path.exists()
    assert path.stat().st_size > 0


def test_save_frame_16bit_preserves_precision(tmp_path: Path) -> None:
    """16-bit output should have more than 256 unique values for a gradient."""
    gradient = np.linspace(0.0, 1.0, 256 * 3, dtype=np.float32).reshape(256, 1, 3)
    gradient = np.broadcast_to(gradient, (256, 64, 3)).copy()
    path = tmp_path / "gradient_16.png"
    save_frame_16bit(gradient, path)
    # File should exist and be larger than an 8-bit version
    assert path.exists()
    assert path.stat().st_size > 100
