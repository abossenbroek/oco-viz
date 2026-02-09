"""Concentration normalization for rendering modes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import RenderingConfig


def _compute_edge_falloff(
    shape: tuple[int, int, int],
    margin_cells: int = 5,
    mode: str = "ellipsoidal",
) -> NDArray[np.float32]:
    """Smooth falloff at volume edges (1.0 interior, tapering to 0.0 at boundary).

    This is applied as a visual effect AFTER normalization, not to raw data.
    Applying it to raw concentration data corrupts background profile estimation.

    Args:
        shape: Volume shape (nz, ny, nx)
        margin_cells: Margin width for rectangular mode (ignored in ellipsoidal mode)
        mode: "rectangular" (axis-aligned ramps) or "ellipsoidal" (radial from center)

    Notes:
        Ellipsoidal mode matches the turbulent plume's natural falloff geometry,
        preventing visible rectangular shell artifacts at volume boundaries.

        For ellipsoidal mode, the fade range maps distance [0.5, 1.0] from the
        normalized center to opacity [1.0, 0.0], so the central 50% of the volume
        is untouched and the outer 50% tapers smoothly to zero.
    """
    nz, ny, nx = shape

    if mode == "ellipsoidal":
        # Match turbulent.py falloff geometry for visual consistency
        cz, cy, cx = nz / 2.0, ny / 2.0, nx / 2.0
        zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]

        # Normalized distance from center (1.0 at corners)
        dist = np.sqrt(((zz - cz) / cz) ** 2 + ((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)

        # Smooth falloff: 1.0 at center → 0.0 at edges
        # Fade starts at r=0.5 (half-extent) and reaches 0.0 at r=1.0 (corners)
        falloff = 1.0 - np.clip((dist - 0.5) * 2.0, 0.0, 1.0)
        return cast("NDArray[np.float32]", falloff.astype(np.float32))

    # Rectangular mode (preserved for compatibility)
    falloff = np.ones((nz, ny, nx), dtype=np.float32)

    for axis, size in enumerate([nz, ny, nx]):
        if size <= 2 * margin_cells:
            continue
        ramp = np.linspace(0.0, 1.0, margin_cells, dtype=np.float32)

        # Create proper reshape for broadcasting
        reshape = [1, 1, 1]
        reshape[axis] = margin_cells

        # Start edge ramp (0→1)
        slices_start: list[slice] = [slice(None), slice(None), slice(None)]
        slices_start[axis] = slice(0, margin_cells)
        falloff[tuple(slices_start)] *= ramp.reshape(reshape)

        # End edge ramp (1→0)
        slices_end: list[slice] = [slice(None), slice(None), slice(None)]
        slices_end[axis] = slice(size - margin_cells, size)
        falloff[tuple(slices_end)] *= ramp[::-1].reshape(reshape)

    return falloff


def compute_background_profile(conc: NDArray[np.float32]) -> NDArray[np.float32]:
    """Estimate background CO2 as the horizontal mean at each altitude level.

    Assumes *conc* has shape ``(nz, ny, nx)``.
    Returns an array broadcastable to *conc* shape ``(nz, 1, 1)``.
    """
    profile = np.nanmean(conc, axis=(1, 2), keepdims=True)
    return cast("NDArray[np.float32]", profile.astype(np.float32))


def _compute_adaptive_divisor(
    enhancement: NDArray[np.float32],
    percentile: float,
    min_value: float,
) -> float:
    """Compute adaptive normalization divisor from enhancement data.

    Args:
        enhancement: Array of enhancement values (concentration - background).
        percentile: Percentile of positive values to use (e.g., 95.0).
        min_value: Floor value to prevent division by tiny numbers.

    Returns:
        Divisor for normalization: max(percentile_value, min_value).
    """
    positive_mask = enhancement > 0
    if not np.any(positive_mask):
        return min_value

    positive_values = enhancement[positive_mask]
    percentile_value = float(np.percentile(positive_values, percentile))
    return max(percentile_value, min_value)


def _apply_gamma_scaling(
    normalized: NDArray[np.float32],
    gamma: float,
) -> NDArray[np.float32]:
    """Apply power-law gamma scaling: output = input^(1/gamma).

    Args:
        normalized: Array of normalized values (ideally in [0, 1]).
        gamma: Gamma value (>1 boosts low/mid-range values).

    Returns:
        Gamma-corrected array, clipped to [0, 1].

    Notes:
        Input is clipped to [0, 1] before power to avoid NaN from
        negative^fractional (complex result) or values > 1 being amplified.
    """
    if gamma == 1.0:
        return normalized

    exponent = 1.0 / gamma
    # Clip BEFORE power to prevent NaN from negative values raised to fractional power
    clipped = np.clip(normalized, 0.0, 1.0)
    return cast(
        "NDArray[np.float32]",
        np.power(clipped, exponent).astype(np.float32),
    )


def _normalize_max(
    conc: NDArray[np.float32],
    rendering_cfg: RenderingConfig,
) -> NDArray[np.float32]:
    """Max-normalize: divide by maximum value, optionally gamma-correct."""
    if np.all(np.isnan(conc)):
        return np.zeros_like(conc)
    max_val = float(np.nanmax(conc))
    if max_val > 0:
        normalized = np.clip(conc / max_val, 0, 1).astype(np.float32)
    else:
        normalized = np.zeros_like(conc)

    if rendering_cfg.opacity_gamma != 1.0:
        normalized = _apply_gamma_scaling(normalized, rendering_cfg.opacity_gamma)

    return cast("NDArray[np.float32]", normalized)


def _normalize_anomaly(
    conc: NDArray[np.float32],
    rendering_cfg: RenderingConfig,
) -> NDArray[np.float32]:
    """Anomaly-normalize: subtract background profile, clip, divide."""
    background = compute_background_profile(conc)
    enhancement = np.clip(conc - background, 0, None)

    if rendering_cfg.adaptive_normalization:
        divisor = _compute_adaptive_divisor(
            enhancement,
            rendering_cfg.adaptive_percentile,
            rendering_cfg.min_enhancement_ppm,
        )
    else:
        divisor = rendering_cfg.anomaly_max_ppm

    normalized = np.clip(enhancement / divisor, 0, 1).astype(np.float32)

    # Order matters: gamma first (boosts values), then edge falloff (tapers to zero).
    if rendering_cfg.opacity_gamma != 1.0:
        normalized = _apply_gamma_scaling(normalized, rendering_cfg.opacity_gamma)

    # Edge feathering applied AFTER normalization to avoid corrupting background estimation
    normalized *= _compute_edge_falloff(normalized.shape, mode="ellipsoidal")
    return cast("NDArray[np.float32]", normalized)


def _normalize_absolute(
    conc: NDArray[np.float32],
    rendering_cfg: RenderingConfig,
) -> NDArray[np.float32]:
    """Absolute-normalize: map [lo, hi] ppm range linearly to [0, 1]."""
    if rendering_cfg.adaptive_normalization:
        lo = float(np.nanpercentile(conc, rendering_cfg.absolute_low_percentile))
        hi = float(np.nanpercentile(conc, rendering_cfg.absolute_high_percentile))
        if hi <= lo:
            hi = lo + 1.0
    else:
        lo = rendering_cfg.absolute_min_ppm
        hi = rendering_cfg.absolute_max_ppm

    span = hi - lo
    if span <= 0:
        return np.zeros_like(conc)
    return cast("NDArray[np.float32]", np.clip((conc - lo) / span, 0, 1).astype(np.float32))


def normalize_concentration(
    conc: NDArray[np.float32],
    rendering_cfg: RenderingConfig,
) -> NDArray[np.float32]:
    """Normalize concentration to [0, 1] based on rendering mode.

    **max** mode:
        Simple max-normalization: divide by maximum value.
        Appropriate for pure plume data without background.

    **anomaly** mode:
        Subtract horizontal-mean background profile, clip to [0, anomaly_max_ppm],
        then divide by anomaly_max_ppm. Background regions become ~0 (transparent).

    **absolute** mode:
        Map [absolute_min_ppm, absolute_max_ppm] linearly to [0, 1].
    """
    if rendering_cfg.mode == "max":
        return _normalize_max(conc, rendering_cfg)

    if rendering_cfg.mode == "anomaly":
        return _normalize_anomaly(conc, rendering_cfg)

    return _normalize_absolute(conc, rendering_cfg)
