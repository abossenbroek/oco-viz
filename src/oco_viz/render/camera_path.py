"""Spline-based camera path with keyframes and easing."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline

from oco_viz.render.camera import CameraState
from oco_viz.render.easing import EasingFunction, apply_easing


class CameraPath:
    """Camera path interpolating between keyframes via cubic spline."""

    def __init__(
        self,
        keyframes: list[tuple[float, CameraState]],
        easing: EasingFunction = EasingFunction.smoothstep,
    ) -> None:
        if len(keyframes) < 2:
            msg = "CameraPath requires at least 2 keyframes"
            raise ValueError(msg)
        self._easing = easing
        self._view_up = keyframes[0][1].view_up
        times = np.array([kf[0] for kf in keyframes])
        positions = np.array([kf[1].position for kf in keyframes])
        focals = np.array([kf[1].focal_point for kf in keyframes])
        self._pos_spline = CubicSpline(times, positions, bc_type="clamped")
        self._foc_spline = CubicSpline(times, focals, bc_type="clamped")
        self._t_min = float(times[0])
        self._t_max = float(times[-1])

    def evaluate(self, t: float) -> CameraState:
        """Evaluate the camera path at normalized time t in [0, 1]."""
        eased = apply_easing(t, self._easing)
        t_mapped = self._t_min + eased * (self._t_max - self._t_min)
        pos = self._pos_spline(t_mapped)
        foc = self._foc_spline(t_mapped)
        return CameraState(
            position=(float(pos[0]), float(pos[1]), float(pos[2])),
            focal_point=(float(foc[0]), float(foc[1]), float(foc[2])),
            view_up=self._view_up,
        )


def reveal_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Start high above, descend to eye level."""
    fx, fy, fz = focal_point
    high_elev = np.radians(75.0)
    low_elev = np.radians(25.0)
    start_pos = (
        fx + distance * np.cos(high_elev) * 1.0,
        fy + distance * np.cos(high_elev) * 0.0,
        fz + distance * np.sin(high_elev),
    )
    end_pos = (
        fx + distance * np.cos(low_elev) * 1.0,
        fy + distance * np.cos(low_elev) * 0.0,
        fz + distance * np.sin(low_elev),
    )
    return CameraPath(
        [
            (0.0, CameraState(position=_ftuple(start_pos), focal_point=focal_point)),
            (1.0, CameraState(position=_ftuple(end_pos), focal_point=focal_point)),
        ],
        easing=easing,
    )


def orbit_rise_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Orbit around focal point while rising in elevation."""
    fx, fy, fz = focal_point
    keyframes: list[tuple[float, CameraState]] = []
    n_keyframes = 5
    for i in range(n_keyframes):
        frac = i / (n_keyframes - 1)
        az = np.radians(frac * 90.0)
        elev = np.radians(20.0 + frac * 30.0)
        pos = (
            fx + distance * np.cos(elev) * np.cos(az),
            fy + distance * np.cos(elev) * np.sin(az),
            fz + distance * np.sin(elev),
        )
        keyframes.append((frac, CameraState(position=_ftuple(pos), focal_point=focal_point)))
    return CameraPath(keyframes, easing=easing)


def push_in_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Slow approach from far to close."""
    fx, fy, fz = focal_point
    elev = np.radians(30.0)
    far_dist = distance * 2.0
    close_dist = distance * 0.5
    start_pos = (
        fx + far_dist * np.cos(elev),
        fy,
        fz + far_dist * np.sin(elev),
    )
    end_pos = (
        fx + close_dist * np.cos(elev),
        fy,
        fz + close_dist * np.sin(elev),
    )
    return CameraPath(
        [
            (0.0, CameraState(position=_ftuple(start_pos), focal_point=focal_point)),
            (1.0, CameraState(position=_ftuple(end_pos), focal_point=focal_point)),
        ],
        easing=easing,
    )


def glacial_drift_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Barely perceptible lateral drift."""
    fx, fy, fz = focal_point
    elev = np.radians(30.0)
    drift = distance * 0.05
    base_x = fx + distance * np.cos(elev)
    base_z = fz + distance * np.sin(elev)
    start_pos = (float(base_x), fy - drift, float(base_z))
    end_pos = (float(base_x), fy + drift, float(base_z))
    return CameraPath(
        [
            (0.0, CameraState(position=start_pos, focal_point=focal_point)),
            (1.0, CameraState(position=end_pos, focal_point=focal_point)),
        ],
        easing=easing,
    )


def _ftuple(vals: tuple[float, ...]) -> tuple[float, float, float]:
    return (float(vals[0]), float(vals[1]), float(vals[2]))
