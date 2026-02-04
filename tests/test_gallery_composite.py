"""Tests for gallery composite rendering and OCO overlay."""

from __future__ import annotations

import numpy as np
import pytest
from scripts.render_gallery import build_oco_overlay_actor

from oco_viz.config.schema import RenderingConfig, load_config
from oco_viz.render.normalize import normalize_concentration
from oco_viz.render.renderer import PRESETS
from oco_viz.render.transfer import TransferFunction


def test_absolute_atmospheric_in_presets() -> None:
    """absolute_atmospheric preset is registered in renderer PRESETS."""
    assert "absolute_atmospheric" in PRESETS


def test_all_presets_produce_valid_tf() -> None:
    """All registered presets produce valid TransferFunction instances."""
    for name, factory in PRESETS.items():
        tf = factory()
        assert isinstance(tf, TransferFunction), f"Preset {name} failed"
        assert len(tf.color_points) > 0
        assert len(tf.opacity_points) > 0


def test_composite_normalization_absolute() -> None:
    """Absolute normalization of composite field (background + plume)."""
    # Simulate composite: 420 background + 5 ppm plume enhancement
    conc = np.full((10, 20, 20), 420.0, dtype=np.float32)
    conc[5, 10, 10] = 430.0  # plume peak

    cfg = RenderingConfig(mode="absolute", absolute_min_ppm=415.0, absolute_max_ppm=435.0)
    result = normalize_concentration(conc, cfg)

    # 420 ppm -> (420-415)/(435-415) = 0.25
    assert result[0, 0, 0] > 0.2
    assert result[0, 0, 0] < 0.3
    # 430 ppm -> (430-415)/(435-415) = 0.75
    assert result[5, 10, 10] > 0.7
    assert result[5, 10, 10] < 0.8


def test_composite_normalization_anomaly() -> None:
    """Anomaly normalization makes background transparent."""
    conc = np.full((10, 20, 20), 420.0, dtype=np.float32)
    conc[5, 10, 10] = 430.0

    cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
    result = normalize_concentration(conc, cfg)

    # Background should be ~0
    assert result[0, 0, 0] < 0.05
    # Plume should be ~1.0 (10 ppm enhancement / 10 max)
    assert result[5, 10, 10] > 0.9


def test_build_oco_overlay_actor_returns_none_for_empty() -> None:
    """Overlay builder returns None for non-Dataset input."""
    result = build_oco_overlay_actor("not_a_dataset", 0.0, 0.0, 1000.0, 1000.0)
    assert result is None


def test_config_loads_with_new_sections() -> None:
    """Config loads with cams and rendering sections."""
    config = load_config()
    assert hasattr(config, "cams")
    assert hasattr(config, "rendering")
    assert config.rendering.mode in ("max", "anomaly", "absolute")


# =============================================================================
# Gallery smoke tests for plume_type + mode combinations
# =============================================================================


@pytest.mark.parametrize(
    ("plume_type", "mode"),
    [
        ("gaussian", "max"),
        ("turbulent", "max"),
        ("composite", "anomaly"),
    ],
)
def test_gallery_plume_type_mode_produces_nonzero(plume_type: str, mode: str) -> None:
    """Each plume_type + mode produces non-zero normalized output."""
    cfg = RenderingConfig(mode=mode)
    if plume_type in ("gaussian", "turbulent"):
        # Sparse plume data without background
        conc = np.zeros((10, 20, 20), dtype=np.float32)
        conc[5, 10, 10] = 0.001
        conc[4:7, 9:12, 9:12] = 0.0005
    else:
        # Composite: CAMS background + plume enhancement
        conc = np.full((10, 20, 20), 420.0, dtype=np.float32)
        conc[5, 10, 10] = 430.0
    result = normalize_concentration(conc, cfg)
    assert result.max() > 0.5, f"{plume_type}+{mode} should produce visible output"
