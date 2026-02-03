"""Tests for rendering modes (anomaly/absolute) and normalization."""

from __future__ import annotations

import numpy as np
import pytest

from oco_viz.config.schema import RenderingConfig, load_config
from oco_viz.render.normalize import (
    compute_background_profile,
    normalize_concentration,
)
from oco_viz.render.transfer import TransferFunction


def test_anomaly_normalization_background_zero() -> None:
    """Uniform field has zero enhancement in anomaly mode."""
    cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
    conc = np.full((10, 20, 20), 420.0, dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert result.max() == pytest.approx(0.0, abs=1e-5)


def test_anomaly_normalization_enhancement() -> None:
    """5 ppm above background maps to 0.5 with max=10."""
    cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
    conc = np.full((10, 20, 20), 420.0, dtype=np.float32)
    # Add a 5 ppm enhancement at one point
    conc[5, 10, 10] = 425.0
    result = normalize_concentration(conc, cfg)
    # The enhancement at that point should be close to 0.5
    # (slightly less because background average shifts up a tiny bit)
    assert result[5, 10, 10] > 0.4
    assert result[5, 10, 10] < 0.6


def test_absolute_normalization_range() -> None:
    """Absolute mode maps [415, 435] -> [0, 1]."""
    cfg = RenderingConfig(mode="absolute", absolute_min_ppm=415.0, absolute_max_ppm=435.0)
    conc = np.array([[[415.0, 425.0, 435.0]]], dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert result[0, 0, 0] == pytest.approx(0.0)
    assert result[0, 0, 1] == pytest.approx(0.5)
    assert result[0, 0, 2] == pytest.approx(1.0)


def test_absolute_normalization_clamped() -> None:
    """Values outside range are clamped to [0, 1]."""
    cfg = RenderingConfig(mode="absolute", absolute_min_ppm=415.0, absolute_max_ppm=435.0)
    conc = np.array([[[400.0, 450.0]]], dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert result[0, 0, 0] == pytest.approx(0.0)
    assert result[0, 0, 1] == pytest.approx(1.0)


def test_compute_background_profile() -> None:
    """Background profile is the horizontal mean at each level."""
    conc = np.random.default_rng(42).uniform(418, 422, (10, 20, 20)).astype(np.float32)
    profile = compute_background_profile(conc)
    assert profile.shape == (10, 1, 1)
    # Should be close to the per-level mean
    for k in range(10):
        expected = np.nanmean(conc[k, :, :])
        assert profile[k, 0, 0] == pytest.approx(expected, rel=1e-5)


def test_absolute_atmospheric_preset_peak_opacity() -> None:
    """absolute_atmospheric preset must have peak opacity <= 0.20."""
    tf = TransferFunction.absolute_atmospheric()
    max_opacity = max(cp.opacity for cp in tf.opacity_points)
    assert max_opacity <= 0.20


def test_rendering_config_mode_validation() -> None:
    """Invalid mode raises ValueError."""
    with pytest.raises(ValueError, match=r"max.*anomaly.*absolute"):
        RenderingConfig(mode="invalid")


def test_config_has_rendering_and_cams() -> None:
    """AppConfig includes cams and rendering sections."""
    config = load_config()
    assert config.rendering.mode == "max"
    assert config.rendering.anomaly_max_ppm > 0
    assert config.cams.dataset == "cams-global-ghg-forecasts"


# =============================================================================
# A1. Core functionality tests for max normalization
# =============================================================================


def test_max_normalization_sparse_plume() -> None:
    """Max normalization scales sparse plume to [0, 1] with peak at 1.0."""
    cfg = RenderingConfig(mode="max")
    conc = np.zeros((10, 20, 20), dtype=np.float32)
    conc[5, 10, 10] = 0.001
    result = normalize_concentration(conc, cfg)
    assert result[5, 10, 10] == pytest.approx(1.0)
    assert result[0, 0, 0] == pytest.approx(0.0)


def test_max_normalization_preserves_relative_values() -> None:
    """Max normalization preserves relative ordering of values."""
    cfg = RenderingConfig(mode="max")
    conc = np.array([[[0.1, 0.2, 0.4, 0.8]]], dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert result[0, 0, 0] == pytest.approx(0.125)
    assert result[0, 0, 3] == pytest.approx(1.0)


# =============================================================================
# A2. Edge case tests
# =============================================================================


@pytest.mark.parametrize("mode", ["max", "anomaly", "absolute"])
def test_normalization_all_zeros(mode: str) -> None:
    """All-zero input produces all-zero output for any mode."""
    cfg = RenderingConfig(mode=mode)
    conc = np.zeros((5, 10, 10), dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert result.max() == 0.0


@pytest.mark.parametrize("mode", ["max", "anomaly", "absolute"])
def test_normalization_output_range(mode: str) -> None:
    """Output is always in [0, 1] range for any mode."""
    cfg = RenderingConfig(mode=mode)
    conc = np.random.default_rng(42).uniform(400, 450, (10, 20, 20)).astype(np.float32)
    result = normalize_concentration(conc, cfg)
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_max_normalization_uniform_nonzero() -> None:
    """Uniform non-zero field produces all 1.0 in max mode."""
    cfg = RenderingConfig(mode="max")
    conc = np.full((5, 10, 10), 42.0, dtype=np.float32)
    result = normalize_concentration(conc, cfg)
    assert np.allclose(result, 1.0)


def test_max_normalization_very_small_values() -> None:
    """Max mode handles very small values (1e-10) without numerical issues."""
    cfg = RenderingConfig(mode="max")
    conc = np.zeros((5, 10, 10), dtype=np.float32)
    conc[2, 5, 5] = 1e-10
    result = normalize_concentration(conc, cfg)
    assert result[2, 5, 5] == pytest.approx(1.0)
    assert not np.isnan(result).any()


# =============================================================================
# A3. Document limitation
# =============================================================================


def test_anomaly_mode_sparse_plume_produces_near_zero() -> None:
    """Anomaly mode produces near-zero for sparse plumes (documents limitation)."""
    cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
    conc = np.zeros((10, 20, 20), dtype=np.float32)
    conc[5, 10, 10] = 0.001
    result = normalize_concentration(conc, cfg)
    assert result.max() < 0.01


# =============================================================================
# A4. Config validation tests
# =============================================================================


def test_rendering_config_accepts_all_valid_modes() -> None:
    """Config accepts 'max', 'anomaly', 'absolute'."""
    for mode in ("max", "anomaly", "absolute"):
        cfg = RenderingConfig(mode=mode)
        assert cfg.mode == mode


def test_rendering_config_rejects_invalid_mode() -> None:
    """Invalid mode raises ValueError with helpful message."""
    with pytest.raises(ValueError, match=r"max.*anomaly.*absolute"):
        RenderingConfig(mode="invalid")


def test_rendering_config_default_mode_is_max() -> None:
    """Default mode is 'max' for backward compatibility."""
    cfg = RenderingConfig()
    assert cfg.mode == "max"
