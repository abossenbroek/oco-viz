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
    """Force pixels outside the plume bounding box to black.

    1. Compute luminance = max(R,G,B) per pixel
    2. Find bbox of pixels with luminance > 1/255
    3. Expand bbox by margin_px
    4. Create mask: 1.0 inside, smoothstep to 0.0 over falloff_px, 0.0 outside
    5. Multiply rgb * mask[:,:,np.newaxis]
    """
    h, w = rgb.shape[:2]
    luminance = np.max(rgb, axis=2)

    # Find bounding box of lit pixels
    lit_mask = luminance > (1.0 / 255.0)
    rows = np.any(lit_mask, axis=1)
    cols = np.any(lit_mask, axis=0)

    if not np.any(rows) or not np.any(cols):
        # No lit pixels -- return all black
        return np.zeros_like(rgb)

    row_indices = np.where(rows)[0]
    col_indices = np.where(cols)[0]
    y_min, y_max = int(row_indices[0]), int(row_indices[-1])
    x_min, x_max = int(col_indices[0]), int(col_indices[-1])

    # Expand bbox by margin
    y_min = max(0, y_min - margin_px)
    y_max = min(h - 1, y_max + margin_px)
    x_min = max(0, x_min - margin_px)
    x_max = min(w - 1, x_max + margin_px)

    # Build distance-to-bbox mask with smoothstep falloff
    ys = np.arange(h, dtype=np.float32)
    xs = np.arange(w, dtype=np.float32)

    # Distance from bbox edges (negative = inside, positive = outside)
    dy_min = np.clip(y_min - ys, 0, None)  # distance above top edge
    dy_max = np.clip(ys - y_max, 0, None)  # distance below bottom edge
    dy = np.maximum(dy_min, dy_max)

    dx_min = np.clip(x_min - xs, 0, None)
    dx_max = np.clip(xs - x_max, 0, None)
    dx = np.maximum(dx_min, dx_max)

    # 2D distance field
    dist = np.sqrt(dy[:, np.newaxis] ** 2 + dx[np.newaxis, :] ** 2)

    # Smoothstep: 1.0 at dist=0, 0.0 at dist>=falloff_px
    if falloff_px > 0:
        t = np.clip(dist / falloff_px, 0.0, 1.0)
        mask = 1.0 - t * t * (3.0 - 2.0 * t)  # smoothstep
    else:
        mask = (dist == 0).astype(np.float32)

    out: NDArray[np.float32] = rgb * mask[:, :, np.newaxis].astype(np.float32)
    return out
