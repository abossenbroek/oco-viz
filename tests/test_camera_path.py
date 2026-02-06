"""Tests for spline-based camera paths."""

from __future__ import annotations

import math

import pytest

from oco_viz.render.camera import CameraState
from oco_viz.render.camera_path import (
    CameraPath,
    glacial_drift_path,
    orbit_rise_path,
    push_in_path,
    reveal_path,
)
from oco_viz.render.easing import EasingFunction


def _distance(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b, strict=True)))


FOCAL = (50.0, 50.0, 30.0)
KF_START = CameraState(position=(200.0, 200.0, 100.0), focal_point=FOCAL)
KF_MID = CameraState(position=(150.0, 250.0, 80.0), focal_point=FOCAL)
KF_END = CameraState(position=(100.0, 100.0, 60.0), focal_point=FOCAL)


class TestCameraPathEndpoints:
    def test_start_preserved(self) -> None:
        path = CameraPath([(0.0, KF_START), (1.0, KF_END)])
        state = path.evaluate(0.0)
        assert state.position == pytest.approx(KF_START.position, abs=1e-6)

    def test_end_preserved(self) -> None:
        path = CameraPath([(0.0, KF_START), (1.0, KF_END)])
        state = path.evaluate(1.0)
        assert state.position == pytest.approx(KF_END.position, abs=1e-6)

    def test_focal_point_preserved_at_start(self) -> None:
        path = CameraPath([(0.0, KF_START), (1.0, KF_END)])
        state = path.evaluate(0.0)
        assert state.focal_point == pytest.approx(FOCAL, abs=1e-6)

    def test_focal_point_preserved_at_end(self) -> None:
        path = CameraPath([(0.0, KF_START), (1.0, KF_END)])
        state = path.evaluate(1.0)
        assert state.focal_point == pytest.approx(FOCAL, abs=1e-6)


class TestCameraPathInterpolation:
    def test_midpoint_between_two_keyframes(self) -> None:
        path = CameraPath(
            [(0.0, KF_START), (1.0, KF_END)],
            easing=EasingFunction.linear,
        )
        state = path.evaluate(0.5)
        for i in range(3):
            expected = (KF_START.position[i] + KF_END.position[i]) / 2
            assert state.position[i] == pytest.approx(expected, abs=5.0)

    def test_three_keyframe_passes_through_middle(self) -> None:
        path = CameraPath(
            [(0.0, KF_START), (0.5, KF_MID), (1.0, KF_END)],
            easing=EasingFunction.linear,
        )
        state = path.evaluate(0.5)
        assert state.position == pytest.approx(KF_MID.position, abs=1e-6)

    def test_view_up_held_constant(self) -> None:
        path = CameraPath([(0.0, KF_START), (1.0, KF_END)])
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            state = path.evaluate(t)
            assert state.view_up == KF_START.view_up


class TestCameraPathValidation:
    def test_single_keyframe_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            CameraPath([(0.0, KF_START)])

    def test_empty_keyframes_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            CameraPath([])


class TestEasingEffect:
    def test_easing_changes_trajectory(self) -> None:
        path_linear = CameraPath(
            [(0.0, KF_START), (1.0, KF_END)],
            easing=EasingFunction.linear,
        )
        path_heavy = CameraPath(
            [(0.0, KF_START), (1.0, KF_END)],
            easing=EasingFunction.heavy_ease_in,
        )
        state_linear = path_linear.evaluate(0.3)
        state_heavy = path_heavy.evaluate(0.3)
        # Heavy ease-in should be closer to start at early t
        dist_linear = _distance(state_linear.position, KF_START.position)
        dist_heavy = _distance(state_heavy.position, KF_START.position)
        assert dist_heavy < dist_linear


class TestPresets:
    @pytest.mark.parametrize(
        "factory",
        [reveal_path, orbit_rise_path, push_in_path, glacial_drift_path],
    )
    def test_preset_evaluable(
        self,
        factory: object,
    ) -> None:
        path = factory(FOCAL, 300.0)  # type: ignore[operator]
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            state = path.evaluate(t)
            assert len(state.position) == 3
            assert len(state.focal_point) == 3

    def test_push_in_distance_decreases(self) -> None:
        path = push_in_path(FOCAL, 300.0, easing=EasingFunction.linear)
        d_start = _distance(path.evaluate(0.0).position, FOCAL)
        d_end = _distance(path.evaluate(1.0).position, FOCAL)
        assert d_end < d_start

    def test_reveal_starts_higher(self) -> None:
        path = reveal_path(FOCAL, 300.0, easing=EasingFunction.linear)
        z_start = path.evaluate(0.0).position[2]
        z_end = path.evaluate(1.0).position[2]
        assert z_start > z_end
