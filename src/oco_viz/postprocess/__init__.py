"""Post-processing pipeline for rendered frames."""

from __future__ import annotations

from oco_viz.postprocess.compose import create_pipeline
from oco_viz.postprocess.pipeline import PostProcessPipeline, default_pipeline

__all__ = ["PostProcessPipeline", "create_pipeline", "default_pipeline"]
