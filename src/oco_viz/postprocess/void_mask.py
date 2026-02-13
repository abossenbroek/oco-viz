"""Post-process void mask to guarantee black frame edges."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def apply_void_mask(
    rgb: NDArray[np.float32],
    *,
    margin_px: int = 20,
    falloff_px: int = 5,
) -> NDArray[np.float32]:
    """Unconditional frame-edge fadeout to black.

    Builds 1D ramps per axis (0.0 at edge, smoothstep rise over falloff_px,
    1.0 in interior) and multiplies the RGB image by the resulting 2D mask.
    The outermost ``margin_px`` pixels are pure black; the next ``falloff_px``
    pixels transition smoothly to full brightness.
    """
    h, w = rgb.shape[:2]

    # --- horizontal (x-axis) ramp ---
    xs = np.arange(w, dtype=np.float32)
    # Distance into the fade region, normalized to [0, 1]
    ramp_left = np.clip((xs - margin_px) / max(falloff_px, 1), 0.0, 1.0)
    ramp_right = np.clip(((w - 1 - xs) - margin_px) / max(falloff_px, 1), 0.0, 1.0)
    t_x = np.minimum(ramp_left, ramp_right)
    ramp_x = t_x * t_x * (3.0 - 2.0 * t_x)  # smoothstep

    # --- vertical (y-axis) ramp ---
    ys = np.arange(h, dtype=np.float32)
    ramp_top = np.clip((ys - margin_px) / max(falloff_px, 1), 0.0, 1.0)
    ramp_bottom = np.clip(((h - 1 - ys) - margin_px) / max(falloff_px, 1), 0.0, 1.0)
    t_y = np.minimum(ramp_top, ramp_bottom)
    ramp_y = t_y * t_y * (3.0 - 2.0 * t_y)  # smoothstep

    # Combine into 2D mask and apply
    mask_2d = ramp_y[:, None] * ramp_x[None, :]
    out: NDArray[np.float32] = rgb * mask_2d[..., None].astype(np.float32)
    return out
