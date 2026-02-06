"""Wave-4 gallery: rendering — first dread register.

Demonstrates volume rendering capabilities:
- Default volume rendering with default transfer function
- Transfer function presets: cinematic_storm, cinematic_ember, cinematic_atmospheric
- Absolute atmospheric normalization mode
- Scattering on vs off comparison
- Sky gradient and ground plane scene
- Post-processing with ACES tonemapping, bloom, and fog

Usage:
    python scripts/render_wave4_gallery.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, RenderingConfig, TransferFunctionConfig
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave4")


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file."""
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path), shape=rgb.shape)


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
        _save_rgb(rgb, OUTPUT_DIR / f"{name}.png")
    finally:
        renderer.finalize()


def render_volume_default() -> None:
    """Render with default transfer function."""
    log.info("=== Volume default ===")
    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "volume_default", preset="default_plume")


def render_transfer_functions() -> None:
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
        _render_with_config(config, conc, camera, name, preset=preset)


def render_absolute_atmospheric() -> None:
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
        preset="absolute_atmospheric",
        rendering=RenderingConfig(mode="absolute"),
    )


def render_scattering_comparison() -> None:
    """Compare scattering off vs on."""
    log.info("=== Scattering comparison ===")

    # Scattering off
    config_off = _load_gallery_config(
        scattering={"shade": False, "sample_distance": 250.0},
    )
    camera = _build_camera(config_off)
    conc = _generate_plume(config_off)
    _render_with_config(config_off, conc, camera, "scattering_off")

    # Scattering on
    config_on = _load_gallery_config(
        scattering={"shade": True, "sample_distance": 250.0},
    )
    conc = _generate_plume(config_on)
    _render_with_config(config_on, conc, camera, "scattering_on")


def render_sky_ground() -> None:
    """Render full scene with sky gradient and ground plane."""
    log.info("=== Sky + ground plane ===")
    config = _load_gallery_config(
        sky={"enabled": True},
        ground_plane={"enabled": True, "opacity": 0.12},
    )
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "sky_ground")


def render_postprocess_aces() -> None:
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
            "exposure": 1.4,
        },
    )
    camera = _build_camera(config)
    conc = _generate_plume(config)
    _render_with_config(config, conc, camera, "postprocess_aces")


def main() -> None:
    """Generate Wave 4 gallery images."""

    def yaml_renderer(
        _logger: object,
        _name: str,
        event_dict: dict[str, object],
    ) -> str:
        return yaml.dump(
            dict(event_dict),
            default_flow_style=False,
            sort_keys=False,
        ).rstrip()

    structlog.configure(
        processors=[structlog.stdlib.add_log_level, yaml_renderer],
        wrapper_class=structlog.make_filtering_bound_logger(0),
    )

    log.info("wave-4 gallery starting")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_volume_default()
    render_transfer_functions()
    render_absolute_atmospheric()
    render_scattering_comparison()
    render_sky_ground()
    render_postprocess_aces()

    n_files = len(list(OUTPUT_DIR.glob("*.png")))
    log.info("wave-4 gallery complete", total_images=n_files, output_dir=str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
