"""Tests for shallow depth of field post-processing."""

from __future__ import annotations

import numpy as np

from oco_viz.config.schema import DOFConfig, PostProcessConfig
from oco_viz.postprocess.dof import (
    _compute_coc,
    _estimate_focal_luminance,
    _estimate_focal_zbuffer,
    apply_dof,
)
from oco_viz.postprocess.pipeline import PostProcessPipeline


def _make_rgb(h: int = 32, w: int = 32) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.random((h, w, 3), dtype=np.float32)


def _make_depth(h: int = 32, w: int = 32) -> np.ndarray:
    return np.linspace(10, 200, h * w, dtype=np.float32).reshape(h, w)


def test_dof_disabled_passthrough() -> None:
    """When DOF is disabled, output should equal input."""
    rgb = _make_rgb()
    depth = _make_depth()
    config = DOFConfig(enabled=False)
    result = apply_dof(rgb, depth, config)
    np.testing.assert_array_equal(result, rgb)


def test_dof_enabled_changes_image() -> None:
    """When DOF is enabled, output should differ from input."""
    rgb = _make_rgb()
    depth = _make_depth()
    config = DOFConfig(enabled=True, aperture=2.8, max_blur_radius=5.0)
    result = apply_dof(rgb, depth, config)
    assert result.shape == rgb.shape
    assert result.dtype == np.float32
    # Image should be different (some pixels blurred)
    assert not np.array_equal(result, rgb)


def test_dof_fixed_focal_distance() -> None:
    """Explicit focal distance should be used."""
    rgb = _make_rgb()
    depth = _make_depth()
    config = DOFConfig(enabled=True, focal_distance=50.0, max_blur_radius=3.0)
    result = apply_dof(rgb, depth, config)
    assert result.shape == rgb.shape
    assert result.dtype == np.float32


def test_focal_zbuffer_estimate() -> None:
    """Z-buffer focal estimate should return depth at brightest region."""
    rgb = np.zeros((16, 16, 3), dtype=np.float32)
    depth = np.linspace(10, 100, 16 * 16, dtype=np.float32).reshape(16, 16)
    # Place a bright spot at row 8, col 8
    rgb[8, 8, :] = 10.0
    focal = _estimate_focal_zbuffer(depth, rgb)
    # Should be near the depth at (8, 8)
    expected = depth[8, 8]
    assert abs(focal - expected) < 5.0


def test_focal_luminance_estimate() -> None:
    """Luminance-weighted estimate should be biased toward bright regions."""
    rgb = np.zeros((16, 16, 3), dtype=np.float32)
    depth = np.linspace(10, 100, 16 * 16, dtype=np.float32).reshape(16, 16)
    # Bright spot at near depth
    rgb[2, 2, :] = 10.0
    focal = _estimate_focal_luminance(depth, rgb)
    # Should be close to the near depth
    assert focal < 50.0


def test_coc_at_focal_plane_is_zero() -> None:
    """CoC should be zero at the focal distance."""
    depth = np.full((8, 8), 50.0, dtype=np.float32)
    coc = _compute_coc(depth, focal_dist=50.0, aperture=2.8)
    np.testing.assert_array_equal(coc, 0.0)


def test_coc_increases_with_distance() -> None:
    """CoC should increase further from the focal plane."""
    depth = np.array([[10, 50, 90]], dtype=np.float32)
    coc = _compute_coc(depth, focal_dist=50.0, aperture=2.8)
    assert coc[0, 0] > 0.0  # far from focal
    assert coc[0, 1] == 0.0  # at focal
    assert coc[0, 2] > 0.0  # far from focal


def test_dof_config_defaults() -> None:
    """DOFConfig defaults should match spec."""
    config = DOFConfig()
    assert config.enabled is False
    assert config.focal_distance is None
    assert config.aperture == 2.8
    assert config.max_blur_radius == 10.0


def test_dof_nested_in_postprocess() -> None:
    """DOFConfig should be accessible as PostProcessConfig.dof."""
    config = PostProcessConfig()
    assert isinstance(config.dof, DOFConfig)
    assert config.dof.enabled is False


def test_pipeline_with_dof_enabled() -> None:
    """Pipeline should apply DOF when enabled in config."""
    config = PostProcessConfig(
        fog_enabled=False,
        bloom_enabled=False,
        exposure=1.0,
        dof=DOFConfig(enabled=True, aperture=2.8, max_blur_radius=3.0),
    )
    pipeline = PostProcessPipeline(config)
    rgb = _make_rgb()
    depth = _make_depth()
    result = pipeline.process(rgb, depth)
    assert result.shape == rgb.shape
    assert result.dtype == np.float32


def test_pipeline_without_dof() -> None:
    """Pipeline should work normally when DOF is disabled."""
    config = PostProcessConfig(fog_enabled=False, bloom_enabled=False, exposure=1.0)
    pipeline = PostProcessPipeline(config)
    rgb = _make_rgb()
    depth = _make_depth()
    result = pipeline.process(rgb, depth)
    assert result.shape == rgb.shape
