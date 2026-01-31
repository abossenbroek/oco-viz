"""Exponential depth fog post-processing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


def apply_depth_fog(
    rgb: NDArray[np.float32],
    depth: NDArray[np.float32],
    *,
    density: float = 0.02,
    fog_color: tuple[float, float, float] = (0.7, 0.75, 0.85),
) -> NDArray[np.float32]:
    """Apply exponential depth fog to an RGB image.

    Pixels at greater depth are blended toward fog_color.
    """
    fog = np.array(fog_color, dtype=np.float32).reshape(1, 1, 3)
    # Fog factor: 0 = no fog (near), 1 = full fog (far)
    fog_factor = 1.0 - np.exp(-density * depth)
    fog_factor_3d = fog_factor[:, :, np.newaxis]
    result: NDArray[np.float32] = (rgb * (1.0 - fog_factor_3d) + fog * fog_factor_3d).astype(
        np.float32
    )
    return result
