"""Multi-scale Gaussian bloom post-processing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.ndimage import gaussian_filter

if TYPE_CHECKING:
    from numpy.typing import NDArray


def apply_bloom(
    rgb: NDArray[np.float32],
    *,
    threshold: float = 0.8,
    intensity: float = 0.3,
    passes: int = 3,
) -> NDArray[np.float32]:
    """Apply multi-scale Gaussian bloom.

    Bright pixels above threshold are blurred at multiple scales and added back.
    """
    bright = np.maximum(rgb - threshold, 0.0)

    bloom_accum = np.zeros_like(rgb)
    for i in range(passes):
        sigma = 2.0 ** (i + 1)
        blurred = np.stack(
            [gaussian_filter(bright[:, :, c], sigma=sigma) for c in range(3)],
            axis=-1,
        )
        bloom_accum += blurred

    if passes > 0:
        bloom_accum /= passes

    result: NDArray[np.float32] = (rgb + intensity * bloom_accum).astype(np.float32)
    return result
