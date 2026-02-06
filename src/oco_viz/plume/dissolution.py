"""Boundary dissolution: noise-modulated density at volume edges."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from oco_viz.plume.noise import fbm_3d

if TYPE_CHECKING:
    from numpy.typing import NDArray


def apply_dissolution(
    conc: NDArray[np.float32],
    *,
    low_threshold: float = 0.05,
    high_threshold: float = 0.30,
    noise_octaves: int = 4,
    noise_seed: int = 12345,
    noise_amplitude: float = 1.5,
) -> NDArray[np.float32]:
    """Inject multiplicative noise into the boundary region of a concentration field.

    Cells with normalized concentration between *low_threshold* and *high_threshold*
    are multiplied by a fractal noise field, creating clumps and holes that
    simulate particulate dissolution at the volume boundary.

    Parameters
    ----------
    conc
        3D concentration array (z, y, x), values in [0, 1].
    low_threshold
        Lower bound of the boundary region.
    high_threshold
        Upper bound of the boundary region.
    noise_octaves
        Number of fBm octaves for the noise field.
    noise_seed
        Random seed for reproducible noise.
    noise_amplitude
        Scaling factor for the noise modulation. Higher = more holes.

    """
    result = conc.copy()
    shape = (conc.shape[0], conc.shape[1], conc.shape[2])

    # Generate noise field in [0, 1]
    noise = fbm_3d(shape, octaves=noise_octaves, seed=noise_seed)

    # Build boundary mask: cells in the dissolution zone
    boundary = (conc >= low_threshold) & (conc <= high_threshold)

    # Modulation: scale noise so that some cells are multiplied toward zero
    # (creating holes) and others are boosted (creating clumps).
    # noise is in [0, 1], we want modulation in [0, noise_amplitude].
    modulation = noise.astype(np.float32) * noise_amplitude

    # Apply: multiply boundary cells by modulation
    result[boundary] *= modulation[boundary]

    # Clamp to [0, 1]
    np.clip(result, 0.0, 1.0, out=result)

    return result
