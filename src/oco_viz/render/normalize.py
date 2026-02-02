"""Concentration normalization for rendering modes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import RenderingConfig


def compute_background_profile(conc: NDArray[np.float32]) -> NDArray[np.float32]:
    """Estimate background CO2 as the horizontal mean at each altitude level.

    Assumes *conc* has shape ``(nz, ny, nx)``.
    Returns an array broadcastable to *conc* shape ``(nz, 1, 1)``.
    """
    profile = np.nanmean(conc, axis=(1, 2), keepdims=True)
    return profile.astype(np.float32)


def normalize_concentration(
    conc: NDArray[np.float32],
    rendering_cfg: RenderingConfig,
) -> NDArray[np.float32]:
    """Normalize concentration to [0, 1] based on rendering mode.

    **anomaly** mode:
        Subtract horizontal-mean background profile, clip to [0, anomaly_max_ppm],
        then divide by anomaly_max_ppm. Background regions become ~0 (transparent).

    **absolute** mode:
        Map [absolute_min_ppm, absolute_max_ppm] linearly to [0, 1].
    """
    if rendering_cfg.mode == "anomaly":
        background = compute_background_profile(conc)
        enhancement = np.clip(conc - background, 0, None)
        return np.clip(
            enhancement / rendering_cfg.anomaly_max_ppm, 0, 1,
        ).astype(np.float32)

    # absolute mode
    lo = rendering_cfg.absolute_min_ppm
    hi = rendering_cfg.absolute_max_ppm
    span = hi - lo
    if span <= 0:
        return np.zeros_like(conc)
    return np.clip((conc - lo) / span, 0, 1).astype(np.float32)
