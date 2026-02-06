"""Tests for boundary dissolution noise modulation."""

from __future__ import annotations

import numpy as np

from oco_viz.plume.dissolution import apply_dissolution

SMALL_SHAPE = (16, 16, 16)


def _make_gradient_field() -> np.ndarray:
    """Create a 3D field with values smoothly ranging from 0 to 1."""
    field = np.zeros(SMALL_SHAPE, dtype=np.float32)
    for z in range(SMALL_SHAPE[0]):
        field[z] = z / (SMALL_SHAPE[0] - 1)
    return field


def test_apply_dissolution_preserves_shape() -> None:
    conc = _make_gradient_field()
    result = apply_dissolution(conc)
    assert result.shape == conc.shape
    assert result.dtype == np.float32


def test_apply_dissolution_creates_holes() -> None:
    """Some boundary cells should be reduced toward zero (holes)."""
    conc = _make_gradient_field()
    result = apply_dissolution(conc, noise_amplitude=1.5)
    # Boundary region: cells with values in [0.05, 0.30]
    boundary = (conc >= 0.05) & (conc <= 0.30)
    # At least some boundary cells should be reduced
    reduced = result[boundary] < conc[boundary]
    assert np.any(reduced), "Dissolution should create holes in the boundary region"


def test_apply_dissolution_preserves_core() -> None:
    """Cells above high_threshold should remain unchanged."""
    conc = _make_gradient_field()
    high = 0.30
    result = apply_dissolution(conc, high_threshold=high)
    core_mask = conc > high
    np.testing.assert_array_equal(result[core_mask], conc[core_mask])


def test_apply_dissolution_preserves_exterior() -> None:
    """Cells below low_threshold should remain unchanged."""
    conc = _make_gradient_field()
    low = 0.05
    result = apply_dissolution(conc, low_threshold=low)
    exterior_mask = conc < low
    np.testing.assert_array_equal(result[exterior_mask], conc[exterior_mask])
