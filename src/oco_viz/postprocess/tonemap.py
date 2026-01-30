"""ACES tone mapping (Narkowicz approximation)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def aces_tonemap(rgb: NDArray[np.float32]) -> NDArray[np.float32]:
    """Apply Narkowicz ACES filmic tone mapping.

    Maps HDR values to [0, 1].
    """
    a = 2.51
    b = 0.03
    c = 2.43
    d = 0.59
    e = 0.14
    result = (rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e)
    return np.clip(result, 0.0, 1.0).astype(np.float32)
