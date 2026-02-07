"""Wave-3 gallery: plume generation — emergence register.

Demonstrates mathematical beauty of plume generation:
- Basic Gaussian plume (study tier)
- Stability classes A through F (Pasquill-Gifford sigma curves)
- Turbulent plume with 2, 4, and 6 octaves of fractal noise
- Wind direction variation across 4 timesteps

Usage:
    python scripts/render_wave3_gallery.py
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

OUTPUT_DIR = Path("output/examples/wave3")


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


def _render_single(
    config: AppConfig,
    conc: np.ndarray,
    camera_state: CameraState,
    name: str,
) -> None:
    """Render a single concentration field and save to output."""
    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max"),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / f"{name}.png")
    finally:
        renderer.finalize()


def render_gaussian_basic() -> None:
    """Render basic Gaussian plume with default settings."""
    log.info("=== Gaussian basic ===")
    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = generate_timestep(config.plume, config.grid, time_index=0)
    log.info("gaussian plume", max_conc=round(float(conc.max()), 6))
    _render_single(config, conc, camera, "gaussian_basic")


def render_stability_classes() -> None:
    """Render Gaussian plume for each stability class A-F."""
    log.info("=== Stability classes A-F ===")

    for stability in "ABCDEF":
        config = _load_gallery_config(
            plume={
                "source_x": 38.0,
                "source_y": 38.0,
                "source_z": 3.0,
                "stability_class": stability,
            },
        )
        camera = _build_camera(config)
        conc = generate_timestep(config.plume, config.grid, time_index=0)
        log.info(
            "stability class",
            cls=stability,
            max_conc=round(float(conc.max()), 6),
        )
        _render_single(config, conc, camera, f"gaussian_stability_{stability}")


def render_turbulence_octaves() -> None:
    """Render turbulent plume with 2, 4, and 6 octaves of noise."""
    log.info("=== Turbulence octaves ===")

    for octaves in [2, 4, 6]:
        config = _load_gallery_config(
            turbulence={"octaves": octaves, "enabled": True},
        )
        camera = _build_camera(config)
        base_conc = generate_timestep(config.plume, config.grid, time_index=0)
        conc = apply_turbulence(base_conc, config.turbulence, config.grid, time_index=0)
        log.info(
            "turbulence",
            octaves=octaves,
            max_conc=round(float(conc.max()), 6),
        )
        _render_single(config, conc, camera, f"turbulent_{octaves}oct")


def render_wind_variation() -> None:
    """Render 4 timesteps showing wind direction oscillation."""
    log.info("=== Wind direction variation ===")

    config = _load_gallery_config()
    camera = _build_camera(config)

    for t_idx in [0, 12, 24, 36]:
        conc = generate_timestep(config.plume, config.grid, time_index=t_idx)
        log.info(
            "wind variation",
            t=t_idx,
            max_conc=round(float(conc.max()), 6),
        )
        _render_single(config, conc, camera, f"wind_variation_t{t_idx}")


def main() -> None:
    """Generate Wave 3 gallery images."""

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

    log.info("wave-3 gallery starting")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_gaussian_basic()
    render_stability_classes()
    render_turbulence_octaves()
    render_wind_variation()

    n_files = len(list(OUTPUT_DIR.glob("*.png")))
    log.info("wave-3 gallery complete", total_images=n_files, output_dir=str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
