"""Frame writers for 8-bit and 16-bit PNG output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


def save_frame_16bit(image_float32: NDArray[np.float32], path: Path) -> Path:
    """Save a float32 [0,1] RGB image as a 16-bit-per-channel PNG.

    Quantizes to uint16 [0, 65535] and writes a 48-bit RGB PNG using
    raw struct encoding, since Pillow's ``fromarray`` does not natively
    support uint16 RGB.
    """
    clamped = np.clip(image_float32, 0.0, 1.0)
    img_u16: NDArray[np.uint16] = (clamped * 65535.0).astype(np.uint16)

    h, w = img_u16.shape[:2]
    # Pillow can create a 48-bit RGB image via frombytes with rawmode "RGB;16B"
    raw_bytes = img_u16.astype(">u2").tobytes()
    img = Image.frombytes("RGB", (w, h), raw_bytes, "raw", "RGB;16B")
    img.save(str(path), format="PNG")
    return path


def save_frame_8bit(image_float32: NDArray[np.float32], path: Path) -> Path:
    """Save a float32 [0,1] RGB image as an 8-bit PNG."""
    clamped = np.clip(image_float32, 0.0, 1.0)
    img_u8: NDArray[np.uint8] = (clamped * 255.0).astype(np.uint8)
    Image.fromarray(img_u8, mode="RGB").save(str(path), format="PNG")
    return path
