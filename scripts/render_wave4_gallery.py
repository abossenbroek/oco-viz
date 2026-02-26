"""Wave-4 gallery: rendering — first dread register.

Demonstrates volume rendering capabilities:
- Default volume rendering with default transfer function
- Transfer function presets: cinematic_storm, cinematic_ember, cinematic_atmospheric
- Absolute atmospheric normalization mode
- Scattering on vs off comparison
- Sky gradient and ground plane scene
- Post-processing with ACES tonemapping, bloom, and fog

"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import structlog

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, RenderingConfig, TransferFunctionConfig
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer
from scripts.gallery._common import save_rgb

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave4")

IMAGE_MANIFEST: list[str] = [
    "volume_default.png",
    "tf_storm.png",
    "tf_ember.png",
    "tf_atmospheric.png",
    "tf_absolute.png",
    "scattering_off.png",
    "scattering_on.png",
    "sky_ground.png",
    "postprocess_aces.png",
]


def _load_gallery_config(**extra_overrides: object) -> AppConfig:
    """Load config with small grid for gallery renders (study tier)."""
    overrides: dict[str, object] = {
        "grid": {"nx": 48, "ny": 48, "nz": 32},
        "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
        "scattering": {"shade": False, "sample_distance": 250.0},
        "output": {"width": 960, "height": 540},
        "turbulence": {"octaves": 4, "enabled": True},
    }
    overrides.update(extra_overrides)
    return load_config("dev_mac", overrides=overrides, tier="study")


def _build_camera(config: AppConfig) -> CameraState:
    """Build a fixed camera to frame the plume."""
    grid = config.grid
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    return FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)


def _generate_plume(config: AppConfig) -> np.ndarray:
    """Generate a turbulent plume for rendering demos."""
    base = generate_timestep(config.plume, config.grid, time_index=0)
    return apply_turbulence(base, config.turbulence, config.grid, time_index=0)


def _render_with_config(
    config: AppConfig,
    conc: np.ndarray,
    camera_state: CameraState,
    name: str,
    output_dir: Path,
    *,
    preset: str = "soot",
    rendering: RenderingConfig | None = None,
) -> None:
    """Render a single frame with specific TF preset and rendering config."""
    updates: dict[str, object] = {
        "transfer_function": TransferFunctionConfig(preset=preset),
    }
    if rendering is not None:
        updates["rendering"] = rendering
    else:
        updates["rendering"] = RenderingConfig(mode="max")

    render_config = config.model_copy(update=updates)
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        save_rgb(rgb, output_dir / f"{name}.png")
    finally:
        renderer.finalize()


def render_volume_default(output_dir: Path) -> None:
    """Render with default transfer function."""
    log.info("=== Volume default ===")
    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "volume_default", output_dir, preset="default_plume")


def render_transfer_functions(output_dir: Path) -> None:
    """Render with each cinematic transfer function preset."""
    log.info("=== Transfer function presets ===")

    presets = {
        "tf_storm": "cinematic_storm",
        "tf_ember": "cinematic_ember",
        "tf_atmospheric": "cinematic_atmospheric",
    }

    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = _generate_plume(config)

    for name, preset in presets.items():
        log.info("rendering TF", preset=preset)
        _render_with_config(config, conc, camera, name, output_dir, preset=preset)


def render_absolute_atmospheric(output_dir: Path) -> None:
    """Render with absolute normalization mode and absolute_atmospheric TF."""
    log.info("=== Absolute atmospheric ===")
    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(
        config,
        conc,
        camera,
        "tf_absolute",
        output_dir,
        preset="absolute_atmospheric",
        rendering=RenderingConfig(mode="absolute", adaptive_normalization=True),
    )


def render_scattering_comparison(output_dir: Path) -> None:
    """Compare scattering off vs on."""
    log.info("=== Scattering comparison ===")

    # Scattering off
    config_off = _load_gallery_config(
        scattering={"shade": False, "sample_distance": 250.0},
    )
    camera = _build_camera(config_off)
    conc = _generate_plume(config_off)
    _render_with_config(config_off, conc, camera, "scattering_off", output_dir)

    # Scattering on
    config_on = _load_gallery_config(
        scattering={"shade": True, "sample_distance": 250.0},
    )
    conc = _generate_plume(config_on)
    _render_with_config(config_on, conc, camera, "scattering_on", output_dir)


def render_sky_ground(output_dir: Path) -> None:
    """Render full scene with sky gradient and ground plane."""
    log.info("=== Sky + ground plane ===")
    config = _load_gallery_config(
        sky={"enabled": True},
        ground_plane={"enabled": True, "opacity": 0.12},
    )
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "sky_ground", output_dir)


def render_postprocess_aces(output_dir: Path) -> None:
    """Render with ACES tonemapping, bloom, and fog post-processing."""
    log.info("=== Post-process: ACES + bloom + fog ===")
    config = _load_gallery_config(
        postprocess={
            "tonemap": "aces",
            "bloom_enabled": True,
            "bloom_threshold": 0.4,
            "bloom_intensity": 0.35,
            "bloom_passes": 4,
            "fog_enabled": True,
            "fog_density": 0.04,
            "exposure": 6.0,
        },
    )
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "postprocess_aces", output_dir)


def render_wave(
    *,
    tier_override: str | None = None,  # noqa: ARG001
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("4")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    render_volume_default(out)
    render_transfer_functions(out)
    render_absolute_atmospheric(out)
    render_scattering_comparison(out)
    render_sky_ground(out)
    render_postprocess_aces(out)

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
