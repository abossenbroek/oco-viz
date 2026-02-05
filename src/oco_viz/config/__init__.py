"""Configuration system with YAML layering."""

from __future__ import annotations

from oco_viz.config.schema import (
    AppConfig,
    CameraConfig,
    CompositionConfig,
    DataSourceConfig,
    DomainConfig,
    ERA5Config,
    GridConfig,
    LightingConfig,
    MotionConfig,
    OCO3Config,
    OutputConfig,
    PlumeConfig,
    PostProcessConfig,
    ScatteringConfig,
    TransferFunctionConfig,
    TurbulenceConfig,
    load_config,
)
from oco_viz.config.tier import Tier

__all__ = [
    "AppConfig",
    "CameraConfig",
    "CompositionConfig",
    "DataSourceConfig",
    "DomainConfig",
    "ERA5Config",
    "GridConfig",
    "LightingConfig",
    "MotionConfig",
    "OCO3Config",
    "OutputConfig",
    "PlumeConfig",
    "PostProcessConfig",
    "ScatteringConfig",
    "Tier",
    "TransferFunctionConfig",
    "TurbulenceConfig",
    "load_config",
]
