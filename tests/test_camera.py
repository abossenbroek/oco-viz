import numpy as np
import pytest
import vtk

from oco_viz.render.camera import (
    CameraState,
    DollyCamera,
    FixedCamera,
    OrbitCamera,
    apply_camera,
)


def test_fixed_camera_constant():
    cam = FixedCamera(position=(1, 2, 3), focal_point=(0, 0, 0))
    s0 = cam.evaluate(0.0)
    s1 = cam.evaluate(0.5)
    s2 = cam.evaluate(1.0)
    assert s0 == s1 == s2


def test_orbit_full_revolution():
    cam = OrbitCamera(azimuth_start=0.0, azimuth_end=360.0)
    s0 = cam.evaluate(0.0)
    s1 = cam.evaluate(1.0)
    assert s0.position[0] == pytest.approx(s1.position[0], abs=1e-6)
    assert s0.position[1] == pytest.approx(s1.position[1], abs=1e-6)
    assert s0.position[2] == pytest.approx(s1.position[2], abs=1e-6)


def test_dolly_midpoint():
    cam = DollyCamera(
        start_position=(0, 0, 0),
        end_position=(100, 0, 0),
        focal_point=(50, 50, 0),
    )
    mid = cam.evaluate(0.5)
    assert mid.position[0] == pytest.approx(50.0, abs=1e-6)


def test_dolly_endpoints():
    cam = DollyCamera(
        start_position=(0, 0, 0),
        end_position=(100, 200, 300),
        focal_point=(0, 0, 0),
    )
    s0 = cam.evaluate(0.0)
    s1 = cam.evaluate(1.0)
    assert np.allclose(s0.position, (0, 0, 0), atol=1e-6)
    assert np.allclose(s1.position, (100, 200, 300), atol=1e-6)


def test_apply_camera_sets_vtk():
    state = CameraState(position=(10, 20, 30), focal_point=(0, 0, 0))
    renderer = vtk.vtkRenderer()
    apply_camera(state, renderer)
    cam = renderer.GetActiveCamera()
    assert cam.GetPosition() == pytest.approx((10, 20, 30), abs=1e-6)
    assert cam.GetFocalPoint() == pytest.approx((0, 0, 0), abs=1e-6)
