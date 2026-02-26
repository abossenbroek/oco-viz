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
        fog -> bloom -> ACES tonemap -> grain; exhibition applies
        bloom -> ACES tonemap -> grain (no fog).
    """
    if tier == "sketch":
        # Minimal pipeline: disable fog/bloom, boost exposure to compensate for
        # low-opacity transfer functions (e.g. soot with max opacity 0.55).
        # exposure=5.0 ensures ~40-50% peak luminance even for dim TFs.
        return PostProcessPipeline(
            config.model_copy(
                update={"fog_enabled": False, "bloom_enabled": False, "exposure": 5.0},
            ),
        )

    if tier == "exhibition":
        # Exhibition: no fog, but bloom and grain are allowed for atmospheric halo
        return PostProcessPipeline(
            config.model_copy(update={"fog_enabled": False}),
        )

    # study (default): fog -> bloom -> ACES tonemap
    return PostProcessPipeline(config)
