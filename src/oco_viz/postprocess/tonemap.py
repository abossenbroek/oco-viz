"""ACES tone mapping (Narkowicz approximation)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def aces_tonemap(
    rgb: NDArray[np.float32],
    *,
    exposure: float = 1.0,
) -> NDArray[np.float32]:
    """Apply Narkowicz ACES filmic tone mapping.

    Parameters
    ----------
    rgb:
        HDR float32 image.
    exposure:
        Pre-tonemap multiplier for mood control.  Values below 1.0 darken
        the image; values above 1.0 brighten it.

    Returns
    -------
    NDArray[np.float32]
        Tone-mapped image with values in [0, 1].

    """
    x = rgb * exposure
    a = 2.51
    b = 0.03
    c = 2.43
    d = 0.59
    e = 0.14
    result = (x * (a * x + b)) / (x * (c * x + d) + e)
    return np.clip(result, 0.0, 1.0).astype(np.float32)
