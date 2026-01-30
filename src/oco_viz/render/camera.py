"""Camera rig system with time-parameterized cameras."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attr
import numpy as np

if TYPE_CHECKING:
    import vtk


def _smoothstep(t: float) -> float:
    """Hermite smoothstep interpolation."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


@attr.s(auto_attribs=True, frozen=True, slots=True)
class CameraState:
    """Snapshot of camera parameters at a given time."""

    position: tuple[float, float, float]
    focal_point: tuple[float, float, float]
    view_up: tuple[float, float, float] = (0.0, 0.0, 1.0)


class FixedCamera:
    """Camera that returns the same state for all t."""

    def __init__(
        self,
        position: tuple[float, float, float],
        focal_point: tuple[float, float, float],
        view_up: tuple[float, float, float] = (0.0, 0.0, 1.0),
    ) -> None:
        self._state = CameraState(
            position=position, focal_point=focal_point, view_up=view_up
        )

    def evaluate(self, t: float) -> CameraState:  # noqa: ARG002
        return self._state


class OrbitCamera:
    """Camera that orbits around a focal point."""

    def __init__(
        self,
        focal_point: tuple[float, float, float] = (50.0, 50.0, 30.0),
        distance: float = 300.0,
        elevation: float = 30.0,
        azimuth_start: float = 0.0,
        azimuth_end: float = 360.0,
    ) -> None:
        self._focal = focal_point
        self._dist = distance
        self._elev = np.radians(elevation)
        self._az_start = azimuth_start
        self._az_end = azimuth_end

    def evaluate(self, t: float) -> CameraState:
        az = np.radians(self._az_start + t * (self._az_end - self._az_start))
        x = self._focal[0] + self._dist * np.cos(self._elev) * np.cos(az)
        y = self._focal[1] + self._dist * np.cos(self._elev) * np.sin(az)
        z = self._focal[2] + self._dist * np.sin(self._elev)
        return CameraState(
            position=(float(x), float(y), float(z)),
            focal_point=self._focal,
        )


class DollyCamera:
    """Camera with smoothstep dolly between start and end positions."""

    def __init__(
        self,
        start_position: tuple[float, float, float],
        end_position: tuple[float, float, float],
        focal_point: tuple[float, float, float],
    ) -> None:
        self._start = np.array(start_position)
        self._end = np.array(end_position)
        self._focal = focal_point

    def evaluate(self, t: float) -> CameraState:
        s = _smoothstep(t)
        pos = self._start + s * (self._end - self._start)
        return CameraState(
            position=(float(pos[0]), float(pos[1]), float(pos[2])),
            focal_point=self._focal,
        )


def apply_camera(state: CameraState, renderer: vtk.vtkRenderer) -> None:
    """Apply a CameraState to a VTK renderer's active camera."""
    cam = renderer.GetActiveCamera()
    cam.SetPosition(*state.position)
    cam.SetFocalPoint(*state.focal_point)
    cam.SetViewUp(*state.view_up)
    renderer.ResetCameraClippingRange()
