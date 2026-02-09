"""Monochrome film grain to mask 8-bit quantization banding."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def apply_grain(
    rgb: NDArray[np.float32],
    *,
    strength: float = 0.04,
    seed: int | None = None,
) -> NDArray[np.float32]:
    """Add monochrome film grain to hide quantization banding.

    Grain is applied in luminance-only (same noise to all channels) so it
    does not introduce color fringing.  Applied AFTER tonemapping, BEFORE
    final quantization to uint8.

    Parameters
    ----------
    rgb
        Tonemapped float32 image in [0, 1], shape [H, W, 3].
    strength
        Standard deviation of Gaussian noise.  0.04 (4%) for exhibition,
        0.02 (2%) for study.
    seed
        Optional RNG seed for reproducibility.

    Returns
    -------
    NDArray[np.float32]
        Image with grain applied, clipped to [0, 1].

    """
    if strength <= 0:
        return rgb
    rng = np.random.default_rng(seed)
    noise = rng.normal(0.0, strength, rgb.shape[:2]).astype(np.float32)
    result = rgb + noise[..., np.newaxis]
    clipped: NDArray[np.float32] = np.clip(result, 0.0, 1.0).astype(np.float32)
    return clipped
