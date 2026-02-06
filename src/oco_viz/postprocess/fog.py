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

    Pixels at greater depth are blended toward *fog_color* using the formula:
    ``blended = rgb * (1 - fog_factor) + fog_color * fog_factor``
    where ``fog_factor = 1 - exp(-density * depth)``.

    Parameters
    ----------
    rgb
        Float32 RGB image array with shape (H, W, 3) and values in [0, 1].
    depth
        Float32 depth buffer with shape (H, W). Values should be linearized
        (not z-buffer [0,1]) — larger values produce more fog.
    density
        Fog density coefficient. Higher values produce thicker fog.
    fog_color
        RGB color to blend toward at distance, default is a soft blue-grey.

    Returns
    -------
    NDArray[np.float32]
        Fogged image with same shape as *rgb*.
    """
    fog = np.array(fog_color, dtype=np.float32).reshape(1, 1, 3)
    # Fog factor: 0 = no fog (near), 1 = full fog (far)
    fog_factor = 1.0 - np.exp(-density * depth)
    fog_factor_3d = fog_factor[:, :, np.newaxis]
    result: NDArray[np.float32] = (rgb * (1.0 - fog_factor_3d) + fog * fog_factor_3d).astype(
        np.float32
    )
    return result
