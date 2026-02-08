"""Wave 5 integration tests: soot rendering + camera composition + tier configs."""

from __future__ import annotations

import numpy as np
import pytest

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, GridConfig
from oco_viz.plume.turbulent import generate_turbulent_timestep
from oco_viz.render.camera import CameraState
from oco_viz.render.camera_path import reveal_path
from oco_viz.render.composition import compose_camera_from_plume, plume_bounding_box
from oco_viz.render.easing import EasingFunction
from oco_viz.render.renderer import VolumeRenderer, resolve_transfer_function

# Compact grid overrides for low-res render tests — keeps plume visible at 64x64.
_COMPACT_GRID: dict[str, object] = {
    "grid": {"nx": 100, "ny": 100, "nz": 60},
    "plume": {"source_x": 50.0, "source_y": 10.0},
}

# Small grid for fast integration tests
SMALL_GRID = GridConfig(nx=20, ny=20, nz=12, dx=1000.0, dy=1000.0, dz=500.0)


# --- Config-only tests (no VTK, fast) ---


def test_study_tier_config_overlay() -> None:
    """Study tier: soot TF preset, fog on, bloom on, basic lighting, exposure 4.0."""
    config = load_config(tier="study")
    assert config.transfer_function.preset == "soot"
    assert config.postprocess.fog_enabled is True
    assert config.postprocess.bloom_enabled is True
    assert config.lighting.mode == "basic"
    assert config.postprocess.exposure == pytest.approx(4.0)
    assert config.postprocess.fog_color == pytest.approx((0.08, 0.08, 0.12))
    assert config.scattering.ambient == pytest.approx(0.65)
    assert config.scattering.diffuse == pytest.approx(0.75)


def test_exhibition_tier_config_overlay() -> None:
    """Exhibition tier: no sky/ground/fog, smoldering lighting, scattering overrides."""
    config = load_config(tier="exhibition")
    assert config.sky.enabled is False
    assert config.ground_plane.enabled is False
    assert config.postprocess.fog_enabled is False
    assert config.lighting.mode == "smoldering"
    assert config.scattering.volumetric_scattering_blending == pytest.approx(0.0)
    assert config.scattering.ambient == pytest.approx(0.85)
    assert config.scattering.diffuse == pytest.approx(0.0)
    assert config.scattering.specular == pytest.approx(0.0)
    assert config.postprocess.exposure == pytest.approx(4.0)


def test_sketch_tier_config_overlay() -> None:
    """Sketch tier: no sky/ground, no lighting, scattering disabled."""
    config = load_config(tier="sketch")
    assert config.sky.enabled is False
    assert config.ground_plane.enabled is False
    assert config.lighting.mode == "none"
    assert config.scattering.volumetric_scattering_blending == pytest.approx(0.0)
    assert config.scattering.global_illumination_reach == pytest.approx(0.0)


def test_exhibition_motion_config() -> None:
    """Exhibition tier: heavy_ease_in, tempo 0.3."""
    config = load_config(tier="exhibition")
    assert config.motion.easing == "heavy_ease_in"
    assert config.motion.tempo_multiplier == pytest.approx(0.3)


def test_study_motion_config() -> None:
    """Study tier: smoothstep, tempo 1.0."""
    config = load_config(tier="study")
    assert config.motion.easing == "smoothstep"
    assert config.motion.tempo_multiplier == pytest.approx(1.0)


def test_exhibition_composition_enabled() -> None:
    """Exhibition tier: composition enabled, vertical_emphasis."""
    config = load_config(tier="exhibition")
    assert config.composition.enabled is True
    assert config.composition.vertical_emphasis is True


def test_study_composition_disabled() -> None:
    """Study tier: composition disabled."""
    config = load_config(tier="study")
    assert config.composition.enabled is False


def test_soot_tf_is_achromatic() -> None:
    """Verify R=G=B on soot TF color points (grayscale)."""
    tf = resolve_transfer_function("soot")
    for cp in tf.color_points:
        assert cp.r == pytest.approx(cp.g, abs=0.01), f"R!=G at scalar {cp.scalar}"
        assert cp.r == pytest.approx(cp.b, abs=0.01), f"R!=B at scalar {cp.scalar}"


def test_camera_path_with_plume_composition() -> None:
    """Camera path + composition pipeline produces valid state."""
    config = load_config(
        tier="exhibition",
        overrides={"turbulence": {"octaves": 2}, "plume": {"source_x": 10.0, "source_y": 10.0}},
    )
    conc = generate_turbulent_timestep(config.plume, SMALL_GRID, config.turbulence, 0)
    focal, distance, _elevation = compose_camera_from_plume(
        conc,
        config.composition,
        (SMALL_GRID.dz, SMALL_GRID.dy, SMALL_GRID.dx),
    )
    path = reveal_path(focal, distance, EasingFunction(config.motion.easing))
    state = path.evaluate(0.5)
    assert len(state.position) == 3
    assert len(state.focal_point) == 3
    assert all(np.isfinite(state.position))
    assert all(np.isfinite(state.focal_point))


def test_plume_bounds_from_turbulent_field() -> None:
    """Turbulent plume produces non-degenerate bounding box."""
    config = load_config(
        tier="study",
        overrides={"turbulence": {"octaves": 2}, "plume": {"source_x": 10.0, "source_y": 10.0}},
    )
    conc = generate_turbulent_timestep(config.plume, SMALL_GRID, config.turbulence, 0)
    centroid, bmin, bmax = plume_bounding_box(
        conc,
        0.01,
        (SMALL_GRID.dz, SMALL_GRID.dy, SMALL_GRID.dx),
    )
    # Non-degenerate: extent > 0 in at least one axis
    extents = [mx - mn for mx, mn in zip(bmax, bmin, strict=True)]
    assert max(extents) > 0, "Bounding box is degenerate"
    # Centroid within bounds
    for i in range(3):
        assert bmin[i] <= centroid[i] <= bmax[i]


# --- VTK rendering tests ---


def _grid_camera(config: AppConfig) -> CameraState:
    """Compute a camera that frames the plume volume for the given config grid."""
    g = config.grid
    focal = (g.nx * g.dx / 2.0, g.ny * g.dy / 2.0, g.nz * g.dz / 2.0)
    extent = max(g.nx * g.dx, g.ny * g.dy)
    return CameraState(
        position=(focal[0] + extent * 0.5, focal[1] + extent * 0.5, focal[2] + 50_000),
        focal_point=focal,
    )


@pytest.mark.skipci
def test_soot_render_produces_non_black_frame() -> None:
    """Study tier, 64x64, non-black + non-uniform."""
    config = load_config(
        "dev_mac",
        tier="study",
        overrides={
            "output": {"width": 64, "height": 64},
            "turbulence": {"octaves": 2},
            **_COMPACT_GRID,
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    conc = generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)
    camera = _grid_camera(config)
    rgb, _ = renderer.render_frame(conc, camera)
    renderer.finalize()

    assert rgb.shape == (64, 64, 3)
    assert rgb.max() > 0.01, "Frame is all black"
    assert rgb.std() > 0.0005, "Frame is uniform"


@pytest.mark.skipci
def test_soot_render_achromatic_output() -> None:
    """Study tier, verify R~=G~=B on non-black pixels (mean channel deviation < 0.15)."""
    config = load_config(
        "dev_mac",
        tier="study",
        overrides={
            "output": {"width": 64, "height": 64},
            "turbulence": {"octaves": 2},
            **_COMPACT_GRID,
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    conc = generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)
    camera = _grid_camera(config)
    rgb, _ = renderer.render_frame(conc, camera)
    renderer.finalize()

    # Check only non-black pixels
    brightness = rgb.mean(axis=2)
    mask = brightness > 0.02
    if mask.sum() > 0:
        non_black = rgb[mask]
        channel_mean = non_black.mean(axis=1, keepdims=True)
        deviation = np.abs(non_black - channel_mean).mean()
        assert deviation < 0.15, f"Mean channel deviation {deviation:.3f} too high for achromatic"


@pytest.mark.skipci
def test_exhibition_render_no_fog_no_bloom() -> None:
    """Exhibition tier, postprocessed output in [0, 1]."""
    config = load_config(
        "dev_mac",
        tier="exhibition",
        overrides={
            "output": {"width": 64, "height": 64},
            "turbulence": {"octaves": 2},
            **_COMPACT_GRID,
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    conc = generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)
    camera = _grid_camera(config)
    rgb, _ = renderer.render_frame(conc, camera)
    renderer.finalize()

    assert rgb.min() >= 0.0
    assert rgb.max() <= 1.0


@pytest.mark.skipci
def test_exhibition_render_non_black() -> None:
    """Exhibition tier must produce non-black output (regression for smoldering fix)."""
    config = load_config(
        "dev_mac",
        tier="exhibition",
        overrides={
            "output": {"width": 64, "height": 64},
            "turbulence": {"octaves": 2},
            **_COMPACT_GRID,
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()
    conc = generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)
    camera = _grid_camera(config)
    rgb = renderer.render_frame_postprocessed(conc, camera)
    renderer.finalize()

    assert rgb.max() > 0.01, "Exhibition tier renders black — smoldering lighting regression"
