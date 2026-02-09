"""Wave-3 gallery: plume generation — emergence register.

Demonstrates mathematical beauty of plume generation:
- Basic Gaussian plume (study tier)
- Stability classes A through F (Pasquill-Gifford sigma curves)
- Turbulent plume with 2, 4, and 6 octaves of fractal noise
- Wind direction variation across 4 timesteps

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

OUTPUT_DIR = Path("output/examples/wave3")

IMAGE_MANIFEST: list[str] = [
    "gaussian_basic.png",
    *[f"gaussian_stability_{s}.png" for s in "ABCDEF"],
    *[f"turbulent_{o}oct.png" for o in [2, 4, 6]],
    *[f"wind_variation_t{t}.png" for t in [0, 12, 24, 36]],
]


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
    output_dir: Path,
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
        save_rgb(rgb, output_dir / f"{name}.png")
    finally:
        renderer.finalize()


def render_gaussian_basic(output_dir: Path) -> None:
    """Render basic Gaussian plume with default settings."""
    log.info("=== Gaussian basic ===")
    config = _load_gallery_config()
    camera = _build_camera(config)
    conc = generate_timestep(config.plume, config.grid, time_index=0)
    log.info("gaussian plume", max_conc=round(float(conc.max()), 6))
    _render_single(config, conc, camera, "gaussian_basic", output_dir)


def render_stability_classes(output_dir: Path) -> None:
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
        _render_single(config, conc, camera, f"gaussian_stability_{stability}", output_dir)


def render_turbulence_octaves(output_dir: Path) -> None:
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
        _render_single(config, conc, camera, f"turbulent_{octaves}oct", output_dir)


def render_wind_variation(output_dir: Path) -> None:
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
        _render_single(config, conc, camera, f"wind_variation_t{t_idx}", output_dir)


def render_wave(
    *,
    tier_override: str | None = None,  # noqa: ARG001
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("3")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    render_gaussian_basic(out)
    render_stability_classes(out)
    render_turbulence_octaves(out)
    render_wind_variation(out)

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
