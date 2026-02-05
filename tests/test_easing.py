"""Tests for easing functions."""

from __future__ import annotations

import pytest

from oco_viz.render.easing import EasingFunction, apply_easing


class TestLinearEasing:
    def test_identity_at_endpoints(self) -> None:
        assert apply_easing(0.0, EasingFunction.linear) == pytest.approx(0.0)
        assert apply_easing(1.0, EasingFunction.linear) == pytest.approx(1.0)

    def test_identity_at_midpoint(self) -> None:
        assert apply_easing(0.5, EasingFunction.linear) == pytest.approx(0.5)

    def test_identity_at_quarter(self) -> None:
        assert apply_easing(0.25, EasingFunction.linear) == pytest.approx(0.25)


class TestEndpoints:
    """All easing functions must map 0 -> 0 and 1 -> 1."""

    @pytest.mark.parametrize("easing", list(EasingFunction))
    def test_zero_maps_to_zero(self, easing: EasingFunction) -> None:
        assert apply_easing(0.0, easing) == pytest.approx(0.0)

    @pytest.mark.parametrize("easing", list(EasingFunction))
    def test_one_maps_to_one(self, easing: EasingFunction) -> None:
        assert apply_easing(1.0, easing) == pytest.approx(1.0)


class TestMonotonicity:
    """All easing functions must be monotonically non-decreasing."""

    @pytest.mark.parametrize("easing", list(EasingFunction))
    def test_monotonic(self, easing: EasingFunction) -> None:
        samples = [apply_easing(t / 100.0, easing) for t in range(101)]
        for i in range(len(samples) - 1):
            assert samples[i] <= samples[i + 1] + 1e-12, (
                f"{easing.value} not monotonic at t={i / 100.0}: {samples[i]} > {samples[i + 1]}"
            )


class TestHeavyEaseIn:
    def test_slower_than_linear_at_early_t(self) -> None:
        for t in [0.1, 0.2, 0.3, 0.4]:
            heavy = apply_easing(t, EasingFunction.heavy_ease_in)
            linear = apply_easing(t, EasingFunction.linear)
            assert heavy < linear, f"heavy_ease_in({t}) = {heavy} not < linear({t}) = {linear}"


class TestSmoothstep:
    def test_symmetric_around_midpoint(self) -> None:
        v1 = apply_easing(0.25, EasingFunction.smoothstep)
        v2 = apply_easing(0.75, EasingFunction.smoothstep)
        assert v1 + v2 == pytest.approx(1.0, abs=1e-10)


class TestClamping:
    """Values outside [0, 1] should be clamped."""

    @pytest.mark.parametrize("easing", list(EasingFunction))
    def test_negative_clamped_to_zero(self, easing: EasingFunction) -> None:
        assert apply_easing(-0.5, easing) == pytest.approx(0.0)

    @pytest.mark.parametrize("easing", list(EasingFunction))
    def test_above_one_clamped_to_one(self, easing: EasingFunction) -> None:
        assert apply_easing(1.5, easing) == pytest.approx(1.0)


class TestEaseInOutCubic:
    def test_midpoint_is_half(self) -> None:
        assert apply_easing(0.5, EasingFunction.ease_in_out_cubic) == pytest.approx(0.5)

    def test_slow_at_start(self) -> None:
        v = apply_easing(0.1, EasingFunction.ease_in_out_cubic)
        assert v < 0.1
