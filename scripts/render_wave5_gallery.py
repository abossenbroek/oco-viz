"""Wave-5 gallery: soot TF, camera paths, composition, and tier rendering.

Generates images demonstrating wave-5 features:
- Soot transfer function (achromatic rendering) across tiers
- Camera path presets (reveal, orbit_rise, push_in, glacial_drift)
- Automatic composition from plume geometry
- Exhibition vs study vs sketch tier comparisons

Usage:
    python scripts/render_wave5_gallery.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import GridConfig
from oco_viz.plume.turbulent import generate_turbulent_timestep
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.camera_path import (
    glacial_drift_path,
    orbit_rise_path,
    push_in_path,
    reveal_path,
)
from oco_viz.render.composition import compose_camera_from_plume
from oco_viz.render.easing import EasingFunction
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave5")
GALLERY_GRID = GridConfig(nx=48, ny=48, nz=32, dx=1000.0, dy=1000.0, dz=500.0)


def _save(rgb: np.ndarray, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    out_path = OUTPUT_DIR / f"{name}.png"
    Image.fromarray(rgb_uint8).save(str(out_path))
    log.info("saved", path=str(out_path), shape=rgb.shape)


def _generate_plume(config):
    """Generate a turbulent plume for gallery rendering."""
    return generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)


def render_tier_comparison() -> None:
    """Render the same plume at study, exhibition, and sketch tiers."""
    log.info("=== Tier comparison (soot TF) ===")

    for tier in ["study", "exhibition", "sketch"]:
        config = load_config(
            "dev_mac",
            tier=tier,
            overrides={
                "grid": {"nx": 48, "ny": 48, "nz": 32},
                "output": {"width": 960, "height": 540},
                "turbulence": {"octaves": 4},
                "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
                "composition": {"enabled": True},
            },
        )
        conc = _generate_plume(config)

        grid = config.grid
        focal, distance, elevation = compose_camera_from_plume(
            conc,
            config.composition,
            (grid.dz, grid.dy, grid.dx),
        )
        elev_rad = math.radians(elevation)
        az_rad = math.radians(30.0)
        pos = (
            focal[0] + distance * math.cos(elev_rad) * math.cos(az_rad),
            focal[1] + distance * math.cos(elev_rad) * math.sin(az_rad),
            focal[2] + distance * math.sin(elev_rad),
        )
        camera = CameraState(position=pos, focal_point=focal)

        renderer = VolumeRenderer(config)
        renderer.configure()
        rgb = renderer.render_frame_postprocessed(conc, camera)
        renderer.finalize()
        _save(rgb, f"tier_{tier}_soot")


def render_camera_paths() -> None:
    """Render frames from each camera path preset."""
    log.info("=== Camera path presets ===")

    config = load_config(
        "dev_mac",
        tier="study",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "output": {"width": 960, "height": 540},
            "turbulence": {"octaves": 4},
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
            "composition": {"enabled": True},
        },
    )
    conc = _generate_plume(config)

    grid = config.grid
    focal, distance, _elevation = compose_camera_from_plume(
        conc,
        config.composition,
        (grid.dz, grid.dy, grid.dx),
    )

    presets = {
        "reveal": reveal_path,
        "orbit_rise": orbit_rise_path,
        "push_in": push_in_path,
        "glacial_drift": glacial_drift_path,
    }

    for name, factory in presets.items():
        path = factory(focal, distance, EasingFunction.smoothstep)
        # Render 5 frames along the path: t = 0.0, 0.25, 0.5, 0.75, 1.0
        for ti, t in enumerate([0.0, 0.25, 0.5, 0.75, 1.0]):
            camera = path.evaluate(t)
            renderer = VolumeRenderer(config)
            renderer.configure()
            rgb = renderer.render_frame_postprocessed(conc, camera)
            renderer.finalize()
            _save(rgb, f"path_{name}_t{ti}")


def render_composition_comparison() -> None:
    """Compare manual vs auto-composed camera framing."""
    log.info("=== Composition comparison ===")

    config = load_config(
        "dev_mac",
        tier="exhibition",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "output": {"width": 960, "height": 540},
            "turbulence": {"octaves": 4},
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
        },
    )
    conc = _generate_plume(config)

    # Manual camera (fixed, may not frame plume well)
    grid = config.grid
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)

    manual_cam = CameraState(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    )

    renderer = VolumeRenderer(config)
    renderer.configure()
    rgb = renderer.render_frame_postprocessed(conc, manual_cam)
    renderer.finalize()
    _save(rgb, "compose_manual")

    # Auto-composed camera from plume geometry
    focal, distance, elevation = compose_camera_from_plume(
        conc,
        config.composition,
        (grid.dz, grid.dy, grid.dx),
    )
    elev_rad = math.radians(elevation)
    az_rad = math.radians(30.0)  # 30° azimuth
    pos = (
        focal[0] + distance * math.cos(elev_rad) * math.cos(az_rad),
        focal[1] + distance * math.cos(elev_rad) * math.sin(az_rad),
        focal[2] + distance * math.sin(elev_rad),
    )
    composed_cam = CameraState(position=pos, focal_point=focal)

    renderer = VolumeRenderer(config)
    renderer.configure()
    rgb = renderer.render_frame_postprocessed(conc, composed_cam)
    renderer.finalize()
    _save(rgb, "compose_auto")

    # Auto-composed + reveal camera path
    path = reveal_path(focal, distance, EasingFunction.heavy_ease_in)
    for ti, t in enumerate([0.0, 0.5, 1.0]):
        camera = path.evaluate(t)
        renderer = VolumeRenderer(config)
        renderer.configure()
        rgb = renderer.render_frame_postprocessed(conc, camera)
        renderer.finalize()
        _save(rgb, f"compose_reveal_t{ti}")


def render_easing_comparison() -> None:
    """Compare easing functions on the same camera path."""
    log.info("=== Easing comparison ===")

    config = load_config(
        "dev_mac",
        tier="study",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "output": {"width": 960, "height": 540},
            "turbulence": {"octaves": 4},
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
            "composition": {"enabled": True},
        },
    )
    conc = _generate_plume(config)

    grid = config.grid
    focal, distance, _elevation = compose_camera_from_plume(
        conc,
        config.composition,
        (grid.dz, grid.dy, grid.dx),
    )

    easings = [
        EasingFunction.linear,
        EasingFunction.smoothstep,
        EasingFunction.heavy_ease_in,
        EasingFunction.ease_in_out_cubic,
    ]

    for t_val, t_name in [(0.2, "t02"), (0.5, "t05"), (0.8, "t08")]:
        for easing in easings:
            path = push_in_path(focal, distance, easing)
            camera = path.evaluate(t_val)
            renderer = VolumeRenderer(config)
            renderer.configure()
            rgb = renderer.render_frame_postprocessed(conc, camera)
            renderer.finalize()
            _save(rgb, f"easing_{easing.value}_{t_name}")


def main() -> None:
    def yaml_renderer(_logger: object, _name: str, event_dict: dict[str, object]) -> str:
        return yaml.dump(dict(event_dict), default_flow_style=False, sort_keys=False).rstrip()

    structlog.configure(
        processors=[structlog.stdlib.add_log_level, yaml_renderer],
        wrapper_class=structlog.make_filtering_bound_logger(0),
    )

    log.info("wave-5 gallery starting")

    render_tier_comparison()
    render_camera_paths()
    render_composition_comparison()
    render_easing_comparison()

    n_files = len(list(OUTPUT_DIR.glob("*.png")))
    log.info("wave-5 gallery complete", total_images=n_files, output_dir=str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
