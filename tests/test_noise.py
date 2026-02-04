"""Tests for fractal Brownian motion noise module."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import laplace

from oco_viz.plume.noise import curl_noise_3d, fbm_3d, fbm_4d

SMALL_SHAPE = (16, 16, 16)


def test_fbm_3d_shape() -> None:
    result = fbm_3d(SMALL_SHAPE)
    assert result.shape == SMALL_SHAPE
    assert result.dtype == np.float32


def test_fbm_3d_range() -> None:
    result = fbm_3d(SMALL_SHAPE)
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_fbm_3d_deterministic() -> None:
    a = fbm_3d(SMALL_SHAPE, seed=123)
    b = fbm_3d(SMALL_SHAPE, seed=123)
    np.testing.assert_array_equal(a, b)


def test_fbm_3d_octaves_effect() -> None:
    low = fbm_3d(SMALL_SHAPE, octaves=1, seed=0)
    high = fbm_3d(SMALL_SHAPE, octaves=6, seed=0)
    # More octaves adds higher-frequency content, which increases the
    # variance of the Laplacian (a proxy for high-frequency energy).
    lap_low = np.var(laplace(low.astype(np.float64)))
    lap_high = np.var(laplace(high.astype(np.float64)))
    assert lap_high > lap_low


def test_fbm_4d_shape() -> None:
    time_slices = 5
    result = fbm_4d(SMALL_SHAPE, time_slices=time_slices)
    assert result.shape == (time_slices, *SMALL_SHAPE)
    assert result.dtype == np.float32


def test_fbm_4d_temporal_coherence() -> None:
    result = fbm_4d(SMALL_SHAPE, time_slices=10, temporal_speed=0.02, seed=7)
    # Adjacent frames should be highly correlated
    for t in range(result.shape[0] - 1):
        a = result[t].ravel()
        b = result[t + 1].ravel()
        corr = np.corrcoef(a, b)[0, 1]
        assert corr > 0.8, f"Frame {t} -> {t + 1} correlation {corr:.4f} < 0.8"


def test_curl_noise_shape() -> None:
    dx, dy, dz = curl_noise_3d(SMALL_SHAPE)
    assert dx.shape == SMALL_SHAPE
    assert dy.shape == SMALL_SHAPE
    assert dz.shape == SMALL_SHAPE
    assert dx.dtype == np.float32
    assert dy.dtype == np.float32
    assert dz.dtype == np.float32


def test_curl_noise_divergence_free() -> None:
    shape = (24, 24, 24)
    dx, dy, dz = curl_noise_3d(shape, octaves=4, seed=99)
    # Divergence = d(dx)/dx + d(dy)/dy + d(dz)/dz
    ddx_dx = np.gradient(dx.astype(np.float64), axis=2)
    ddy_dy = np.gradient(dy.astype(np.float64), axis=1)
    ddz_dz = np.gradient(dz.astype(np.float64), axis=0)
    divergence = ddx_dx + ddy_dy + ddz_dz
    # Mean absolute divergence should be very small
    assert np.mean(np.abs(divergence)) < 0.05, (
        f"Mean |divergence| = {np.mean(np.abs(divergence)):.6f}"
    )
