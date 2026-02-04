"""Tier-conditional post-processing pipeline factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oco_viz.postprocess.pipeline import PostProcessPipeline

if TYPE_CHECKING:
    from oco_viz.config.schema import PostProcessConfig


def create_pipeline(config: PostProcessConfig, tier: str) -> PostProcessPipeline:
    """Create a post-processing pipeline appropriate for the given tier.

    Parameters
    ----------
    config
        Post-processing configuration with fog/bloom toggles.
    tier
        One of "sketch", "study", "exhibition".

    Returns
    -------
    PostProcessPipeline
        Configured pipeline. Sketch returns a passthrough; study applies
        fog -> bloom -> ACES tonemap; exhibition applies ACES tonemap only.
    """
    if tier == "sketch":
        # Passthrough: disable all stages, tonemap is essentially identity at exposure=1
        return PostProcessPipeline(
            config.model_copy(
                update={"fog_enabled": False, "bloom_enabled": False, "exposure": 1.0},
            ),
        )

    if tier == "exhibition":
        # ACES tonemap only: no fog, no bloom
        return PostProcessPipeline(
            config.model_copy(update={"fog_enabled": False, "bloom_enabled": False}),
        )

    # study (default): fog -> bloom -> ACES tonemap
    return PostProcessPipeline(config)
