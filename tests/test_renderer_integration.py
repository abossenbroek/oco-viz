"""Integration tests for wave 3 visual polish features."""

from __future__ import annotations

import pytest

from oco_viz.config import load_config
from oco_viz.config.schema import GroundPlaneConfig, SkyConfig
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState
from oco_viz.render.renderer import VolumeRenderer


@pytest.mark.skipci
def test_renderer_applies_sky_gradient() -> None:
    config = load_config(
        "dev_mac",
        overrides={"output": {"width": 64, "height": 64}, "sky": {"enabled": True}},
    )
    renderer = VolumeRenderer(config)
    renderer.configure()

    assert renderer._renderer is not None
    assert renderer._renderer.GetGradientBackground() is True
    bg = renderer._renderer.GetBackground()
    bg2 = renderer._renderer.GetBackground2()
    assert bg == config.sky.bottom_color
    assert bg2 == config.sky.top_color

    renderer.finalize()


@pytest.mark.skipci
def test_renderer_adds_ground_plane_actor() -> None:
    config = load_config(
        "dev_mac",
        overrides={
            "output": {"width": 64, "height": 64},
            "ground_plane": {"enabled": True},
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()

    assert renderer._renderer is not None
    # Ground plane is an actor (not volume), so check actor count > 0
    assert renderer._renderer.GetActors().GetNumberOfItems() > 0

    renderer.finalize()


@pytest.mark.skipci
def test_renderer_disabled_ground_plane() -> None:
    config = load_config(
        "dev_mac",
        overrides={
            "output": {"width": 64, "height": 64},
            "ground_plane": {"enabled": False},
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()

    assert renderer._renderer is not None
    assert renderer._renderer.GetActors().GetNumberOfItems() == 0

    renderer.finalize()


@pytest.mark.skipci
def test_volume_has_material_properties() -> None:
    config = load_config("dev_mac", overrides={"output": {"width": 64, "height": 64}})
    renderer = VolumeRenderer(config)
    renderer.configure()

    concentration = generate_timestep(config.plume, config.grid, time_index=0)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))
    renderer.render_frame(concentration, camera)

    assert renderer._volume is not None
    vol_prop = renderer._volume.GetProperty()
    assert abs(vol_prop.GetAmbient() - config.scattering.ambient) < 1e-6
    assert abs(vol_prop.GetDiffuse() - config.scattering.diffuse) < 1e-6
    assert abs(vol_prop.GetSpecular() - config.scattering.specular) < 1e-6

    renderer.finalize()


def test_config_has_sky_and_ground_plane() -> None:
    config = load_config()
    assert isinstance(config.sky, SkyConfig)
    assert isinstance(config.ground_plane, GroundPlaneConfig)
    # Default tier is study, which disables sky and ground plane (Soot aesthetic)
    assert config.sky.enabled is False
    assert config.ground_plane.enabled is False


def test_dev_mac_uses_8bit() -> None:
    config = load_config("dev_mac")
    assert config.output.bit_depth == 8


def test_base_config_has_exposure() -> None:
    config = load_config()
    assert config.postprocess.exposure == pytest.approx(1.4)


def test_base_config_has_material_properties() -> None:
    config = load_config()
    assert config.scattering.ambient == pytest.approx(0.4)
    assert config.scattering.diffuse == pytest.approx(0.5)
    assert config.scattering.specular == pytest.approx(0.0)
