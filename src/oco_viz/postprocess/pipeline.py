"""Composable post-processing pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from oco_viz.config.schema import PostProcessConfig
from oco_viz.postprocess.bloom import apply_bloom
from oco_viz.postprocess.fog import apply_depth_fog
from oco_viz.postprocess.grain import apply_grain
from oco_viz.postprocess.tonemap import aces_tonemap

if TYPE_CHECKING:
    from numpy.typing import NDArray


class PostProcessPipeline:
    """Composable post-processing pipeline on float32 intermediates."""

    def __init__(self, config: PostProcessConfig) -> None:
        self._config = config

    def process(
        self,
        rgb: NDArray[np.float32],
        depth: NDArray[np.float32],
        *,
        extra_exposure: float = 1.0,
    ) -> NDArray[np.float32]:
        """Apply enabled stages: [fog] -> [bloom] -> tonemap -> [grain].

        Fog and bloom are skipped when their respective config flags are False.
        Bloom operates in HDR/linear space before tonemapping compresses the range.
        """
        result = rgb
        if self._config.fog_enabled:
            result = apply_depth_fog(
                result,
                depth,
                density=self._config.fog_density,
                fog_color=self._config.fog_color,
            )
        if self._config.bloom_enabled:
            result = apply_bloom(
                result,
                threshold=self._config.bloom_threshold,
                intensity=self._config.bloom_intensity,
                passes=self._config.bloom_passes,
            )
        result = aces_tonemap(result, exposure=self._config.exposure * extra_exposure)
        if self._config.grain_strength > 0:
            result = apply_grain(result, strength=self._config.grain_strength)
        return result

    def quantize(self, rgb: NDArray[np.float32]) -> NDArray[np.uint8]:
        """Convert float32 [0,1] to uint8 [0,255]."""
        result: NDArray[np.uint8] = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
        return result


def default_pipeline() -> PostProcessPipeline:
    """Create a pipeline with default config."""
    return PostProcessPipeline(PostProcessConfig())
