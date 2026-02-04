"""Integration tests for wave 3 visual polish features."""

from __future__ import annotations

import numpy as np
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


# =============================================================================
# Integration tests for rendering mode regression fix
# =============================================================================


@pytest.mark.skipci
@pytest.mark.parametrize("mode", ["max", "anomaly", "absolute"])
def test_renderer_produces_nonzero_rgb_for_mode(mode: str) -> None:
    """Renderer produces non-black RGB for appropriate data."""
    config = load_config(
        "dev_mac",
        overrides={
            "output": {"width": 64, "height": 64},
            "rendering": {"mode": mode},
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    if mode == "max":
        conc = generate_timestep(config.plume, config.grid, time_index=0)
    else:
        # Create composite-style data for anomaly/absolute modes
        # Use a larger enhancement region (5x5x5 voxels) for visibility
        # with smooth opacity ramps and ellipsoidal edge falloff
        conc = np.full(config.grid.shape, 420.0, dtype=np.float32)
        cz, cy, cx = config.grid.nz // 2, config.grid.ny // 2, config.grid.nx // 2
        for dz in range(-2, 3):
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    conc[cz + dz, cy + dy, cx + dx] = 430.0
    # Camera position in world units (meters) - must match grid extent
    # Grid: nx*dx=100km, ny*dy=100km, nz*dz=30km
    # Plume source at (50km, 10km, 2.5km), so position camera to view it
    grid = config.grid
    focal = (grid.nx * grid.dx / 2, grid.ny * grid.dy / 2, grid.nz * grid.dz / 2)
    # Position camera at distance from focal point
    camera = CameraState(
        position=(focal[0] + 150_000, focal[1] + 150_000, focal[2] + 50_000),
        focal_point=focal,
    )
    rgb, _ = renderer.render_frame(conc, camera)
    renderer.finalize()
    assert rgb.max() > 0.01, f"Mode {mode} produced black output"


@pytest.mark.skipci
def test_sparse_plume_with_max_mode_produces_visible_output() -> None:
    """Critical regression test: sparse plume + max mode must be visible."""
    config = load_config(
        "dev_mac",
        overrides={
            "output": {"width": 64, "height": 64},
            "rendering": {"mode": "max"},
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    conc = generate_timestep(config.plume, config.grid, time_index=0)
    # Camera position in world units (meters) - must match grid extent
    grid = config.grid
    focal = (grid.nx * grid.dx / 2, grid.ny * grid.dy / 2, grid.nz * grid.dz / 2)
    camera = CameraState(
        position=(focal[0] + 150_000, focal[1] + 150_000, focal[2] + 50_000),
        focal_point=focal,
    )
    rgb, _ = renderer.render_frame(conc, camera)
    renderer.finalize()
    assert rgb.max() > 0.05, "Sparse plume rendered as black - REGRESSION!"
