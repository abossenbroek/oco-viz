"""Spline-based camera path with keyframes and easing."""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline

from oco_viz.render.camera import CameraState
from oco_viz.render.easing import EasingFunction, apply_easing


def _spherical_position(
    focal_point: tuple[float, float, float],
    distance: float,
    elevation_rad: float,
    azimuth_rad: float = 0.0,
) -> tuple[float, float, float]:
    """Compute cartesian position from spherical coordinates around a focal point."""
    fx, fy, fz = focal_point
    return (
        float(fx + distance * np.cos(elevation_rad) * np.cos(azimuth_rad)),
        float(fy + distance * np.cos(elevation_rad) * np.sin(azimuth_rad)),
        float(fz + distance * np.sin(elevation_rad)),
    )


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
    start_pos = _spherical_position(focal_point, distance, np.radians(75.0))
    end_pos = _spherical_position(focal_point, distance, np.radians(25.0))
    return CameraPath(
        [
            (0.0, CameraState(position=start_pos, focal_point=focal_point)),
            (1.0, CameraState(position=end_pos, focal_point=focal_point)),
        ],
        easing=easing,
    )


def orbit_rise_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Orbit around focal point while rising in elevation."""
    keyframes: list[tuple[float, CameraState]] = []
    n_keyframes = 5
    for i in range(n_keyframes):
        frac = i / (n_keyframes - 1)
        pos = _spherical_position(
            focal_point, distance, np.radians(20.0 + frac * 30.0), np.radians(frac * 90.0),
        )
        keyframes.append((frac, CameraState(position=pos, focal_point=focal_point)))
    return CameraPath(keyframes, easing=easing)


def push_in_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Slow approach from far to close."""
    elev = np.radians(30.0)
    start_pos = _spherical_position(focal_point, distance * 2.0, elev)
    end_pos = _spherical_position(focal_point, distance * 0.5, elev)
    return CameraPath(
        [
            (0.0, CameraState(position=start_pos, focal_point=focal_point)),
            (1.0, CameraState(position=end_pos, focal_point=focal_point)),
        ],
        easing=easing,
    )


def glacial_drift_path(
    focal_point: tuple[float, float, float],
    distance: float,
    easing: EasingFunction = EasingFunction.smoothstep,
) -> CameraPath:
    """Barely perceptible lateral drift."""
    elev = np.radians(30.0)
    drift = distance * 0.05
    base = _spherical_position(focal_point, distance, elev)
    start_pos = (base[0], base[1] - drift, base[2])
    end_pos = (base[0], base[1] + drift, base[2])
    return CameraPath(
        [
            (0.0, CameraState(position=start_pos, focal_point=focal_point)),
            (1.0, CameraState(position=end_pos, focal_point=focal_point)),
        ],
        easing=easing,
    )
