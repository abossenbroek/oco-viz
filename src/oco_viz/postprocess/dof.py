"""Shallow depth of field post-processing via variable Gaussian blur.

Limitation: VTK's z-buffer for volumetric rendering stores the first significant
opacity hit, not a true surface depth. For dense plumes this is usable but imperfect.
The artistic blur effect is valuable for pre-viz (Stage 0) even if not physically
accurate. Two focal-distance strategies are provided to mitigate this.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.ndimage import gaussian_filter

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import DOFConfig

# Number of discrete blur levels for circle-of-confusion simulation
_N_BLUR_LEVELS = 8


def _estimate_focal_zbuffer(
    depth: NDArray[np.float32],
    rgb: NDArray[np.float32],
) -> float:
    """Estimate focal distance from depth buffer at the plume centroid.

    Finds the brightest region (plume core) and returns its depth value.
    This is the default strategy (z-buffer based).
    """
    # Use luminance to find the plume center of mass
    luminance = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    total_lum = float(luminance.sum())
    if total_lum < 1e-8:
        return float(np.median(depth))

    h, w = depth.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy = float(np.sum(yy * luminance) / total_lum)
    cx = float(np.sum(xx * luminance) / total_lum)

    # Sample depth at plume centroid (clamped to valid indices)
    iy = min(max(int(cy), 0), h - 1)
    ix = min(max(int(cx), 0), w - 1)
    return float(depth[iy, ix])


def _estimate_focal_luminance(
    depth: NDArray[np.float32],
    rgb: NDArray[np.float32],
) -> float:
    """Estimate focal distance via luminance-weighted depth average.

    Fallback strategy for unreliable z-buffer regions. Computes a weighted
    average of depth values, where weights are pixel luminance. This gives
    a depth estimate biased toward bright (plume) regions.
    """
    luminance = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    total_lum = float(luminance.sum())
    if total_lum < 1e-8:
        return float(np.median(depth))

    return float(np.sum(depth * luminance) / total_lum)


def _compute_coc(
    depth: NDArray[np.float32],
    focal_dist: float,
    aperture: float,
) -> NDArray[np.float32]:
    """Compute circle-of-confusion map.

    CoC is proportional to |depth - focal_distance| / aperture.
    Returns values in [0, 1] normalized by max distance.
    """
    distance = np.abs(depth - focal_dist)
    max_dist = float(distance.max())
    if max_dist < 1e-8:
        return np.zeros_like(depth)
    coc = (distance / max_dist) / aperture
    result: NDArray[np.float32] = np.clip(coc, 0.0, 1.0).astype(np.float32)
    return result


def apply_dof(
    rgb: NDArray[np.float32],
    depth: NDArray[np.float32],
    config: DOFConfig,
) -> NDArray[np.float32]:
    """Apply variable-blur depth of field.

    Uses discrete blur levels blended by circle-of-confusion weight, following
    the same scipy.ndimage.gaussian_filter pattern as bloom.py.

    Parameters
    ----------
    rgb
        Float32 RGB image (H, W, 3) in [0, inf) (HDR linear space).
    depth
        Float32 depth buffer (H, W).
    config
        DOF configuration (focal_distance, aperture, max_blur_radius).

    Returns
    -------
    NDArray[np.float32]
        Image with depth-of-field blur applied.

    """
    if not config.enabled:
        return rgb

    # Determine depth source
    if config.depth_mode == "luminance":
        luminance = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        max_lum = float(luminance.max())
        if max_lum > 1e-8:
            # Brighter = closer = smaller depth value (range [0, 1])
            depth = (1.0 - (luminance / max_lum)).astype(np.float32)
        else:
            depth = np.zeros_like(luminance, dtype=np.float32)

    # Determine focal distance
    if config.focal_distance is not None:
        focal_dist = config.focal_distance
    else:
        # Try z-buffer strategy first; fall back to luminance-weighted
        focal_zbuf = _estimate_focal_zbuffer(depth, rgb)
        focal_lum = _estimate_focal_luminance(depth, rgb)
        # Use z-buffer if it's in a reasonable range, otherwise luminance
        depth_range = float(depth.max()) - float(depth.min())
        focal_dist = focal_zbuf if depth_range > 1e-4 else focal_lum

    # Compute circle-of-confusion
    coc = _compute_coc(depth, focal_dist, config.aperture)

    # Generate discrete blur levels
    sigmas = np.linspace(0, config.max_blur_radius, _N_BLUR_LEVELS)
    blurred_levels = []
    for sigma in sigmas:
        if sigma < 0.5:
            blurred_levels.append(rgb.copy())
        else:
            blurred = np.stack(
                [gaussian_filter(rgb[:, :, c], sigma=sigma) for c in range(3)],
                axis=-1,
            ).astype(np.float32)
            blurred_levels.append(blurred)

    # Blend between blur levels based on CoC
    result = np.zeros_like(rgb)
    n_levels = len(blurred_levels)
    # Map CoC [0, 1] to level index [0, n_levels - 1]
    level_index = coc * (n_levels - 1)
    low_idx = np.floor(level_index).astype(np.int32)
    high_idx = np.minimum(low_idx + 1, n_levels - 1)
    frac = (level_index - low_idx).astype(np.float32)

    for i in range(n_levels):
        mask_lo = low_idx == i
        mask_hi = high_idx == i
        for c in range(3):
            result[:, :, c] += blurred_levels[i][:, :, c] * mask_lo * (1.0 - frac)
            result[:, :, c] += blurred_levels[i][:, :, c] * mask_hi * frac

    return result.astype(np.float32)
