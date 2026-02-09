"""Render Wave 8 gallery: particle dissolution, depth of field, and ECD coupling.

Demonstrates:
- Particle dissolution at volume boundaries (vtkPointGaussianMapper billboard)
- Shallow depth of field (variable Gaussian blur, dual focal-distance strategy)
- ECD-driven turbulence amplitude modulation
- Exhibition-tier rendering with all three features combined
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import (
    AppConfig,
    DOFConfig,
    ParticleDissolutionConfig,
    PostProcessConfig,
    RenderingConfig,
    TransferFunctionConfig,
)
from oco_viz.plume.dissolution import apply_dissolution
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.particle_dissolve import create_dissolution_particles
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave8")

_EXPOSURE = 55.0
_VIEW_ANGLE = 35.0
_CAMERA_FILL_SCALE = 0.55


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Wave 8 gallery images.")
    return parser.parse_args()


def _load_exhibition_config(*, dof_enabled: bool = False) -> AppConfig:
    """Load exhibition config with wave 8 features.

    Grid is 96x96x64 with anisotropic Z-squash. DOF can be toggled per render.
    """
    dof_override: dict[str, object] = {"enabled": dof_enabled, "aperture": 2.8}
    if dof_enabled:
        dof_override["max_blur_radius"] = 12.0

    return load_config(
        "dev_mac",
        overrides={
            "grid": {
                "nx": 96,
                "ny": 96,
                "nz": 64,
                "dx": 100.0,
                "dy": 100.0,
                "dz": 50.0,
            },
            "postprocess": {
                "exposure": _EXPOSURE,
                "bloom_enabled": False,
                "dof": dof_override,
            },
            "particle_dissolution": {
                "enabled": True,
                "threshold": 0.03,
                "particle_count_scale": 3.5,
                "particle_scale": 500.0,
                "particle_opacity": 0.85,
            },
        },
        tier="exhibition",
    )


def _get_standard_plume(config: AppConfig, modulator: float = 1.0) -> np.ndarray:
    """Generate a standard turbulent plume for gallery consistency."""
    grid = config.grid
    plume_cfg = config.plume.model_copy(
        update={
            "source_x": grid.nx * 0.4,
            "source_y": grid.ny * 0.5,
            "emission_rate": 15000.0,
            "stability_class": "C",
            "wind_speed": 4.0,
        },
    )
    base = generate_timestep(plume_cfg, grid, time_index=0)
    return apply_turbulence(base, config.turbulence, grid, 0, amplitude_modulator=modulator)


def _frame_camera(
    config: AppConfig,
    conc: np.ndarray,
    *,
    fill_scale: float = _CAMERA_FILL_SCALE,
) -> CameraState:
    """Compute camera position that tightly frames the plume.

    Uses the plume bounding box (thresholded at 5% of max to ignore trace voxels),
    places the focal point at bbox center, and positions the camera close enough
    that the wispy volumetric plume fills 60-80% of the frame. ``fill_scale``
    multiplies the bbox diagonal to get the camera distance — smaller values mean
    a tighter crop.
    """
    grid = config.grid
    max_conc = float(np.max(conc))
    threshold = 0.05 * max_conc if max_conc > 0 else 0.0

    mask = conc > threshold
    coords = np.argwhere(mask)

    if len(coords) == 0:
        fx = grid.nx * grid.dx * 0.5
        fy = grid.ny * grid.dy * 0.5
        fz = grid.nz * grid.dz * 0.5
        cam_dist = max(grid.nx * grid.dx, grid.ny * grid.dy) * 0.25
    else:
        # coords are (z, y, x) indices — convert to world
        z_min, y_min, x_min = coords.min(axis=0)
        z_max, y_max, x_max = coords.max(axis=0)

        wx_min, wx_max = x_min * grid.dx, x_max * grid.dx
        wy_min, wy_max = y_min * grid.dy, y_max * grid.dy
        wz_min, wz_max = z_min * grid.dz, z_max * grid.dz

        fx = (wx_min + wx_max) * 0.5
        fy = (wy_min + wy_max) * 0.5
        fz = (wz_min + wz_max) * 0.5

        bbox_diag = math.sqrt(
            (wx_max - wx_min) ** 2 + (wy_max - wy_min) ** 2 + (wz_max - wz_min) ** 2
        )
        cam_dist = bbox_diag * fill_scale

    return FixedCamera(
        position=(fx + cam_dist * 0.90, fy + cam_dist * 0.05, fz + cam_dist * 0.30),
        focal_point=(fx, fy, fz),
    ).evaluate(0.0)


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file with dithering to reduce banding."""
    # Add tiny noise before quantization to break up tonal banding
    rng = np.random.default_rng(42)
    dither = rng.uniform(-0.5 / 255.0, 0.5 / 255.0, size=rgb.shape).astype(np.float32)
    rgb_dithered = rgb + dither
    rgb_uint8 = np.clip(rgb_dithered * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def _render_dissolution_comparison(
    config: AppConfig,
) -> int:
    """Render with and without particle dissolution overlay.

    Returns the number of images rendered.
    """
    n_rendered = 0
    conc = _get_standard_plume(config)

    # Normalize for dissolution
    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
            noise_octaves=4,
            noise_amplitude=1.5,
        )
        conc_dissolved = dissolved * max_val
    else:
        conc_dissolved = conc.copy()

    camera_state = _frame_camera(config, conc_dissolved)

    # --- Without particle dissolution ---
    render_cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=1.6),
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=True,
                bloom_threshold=0.3,
                bloom_intensity=0.6,
                bloom_passes=4,
                exposure=_EXPOSURE,
                dof=DOFConfig(enabled=False),
            ),
        },
    )
    renderer = VolumeRenderer(render_cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(_VIEW_ANGLE)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        rgb = renderer.render_frame_postprocessed(
            conc_dissolved,
            camera_state,
            pre_normalized=False,
        )
        _save_rgb(rgb, OUTPUT_DIR / "dissolution_off.png")
        n_rendered += 1

        # --- With particle dissolution overlay ---
        pdiss_cfg = config.particle_dissolution
        spacing = (config.grid.dx, config.grid.dy, config.grid.dz)
        norm = conc_dissolved / max(float(conc_dissolved.max()), 1e-8)
        particle_actor = create_dissolution_particles(norm.astype(np.float32), spacing, pdiss_cfg)
        renderer.add_actor(particle_actor)

        rgb = renderer.render_frame_postprocessed(
            conc_dissolved,
            camera_state,
            pre_normalized=False,
        )
        _save_rgb(rgb, OUTPUT_DIR / "dissolution_on.png")
        n_rendered += 1
    finally:
        renderer.finalize()

    return n_rendered


def _render_dof_comparison(
    config: AppConfig,
) -> int:
    """Render with and without depth of field.

    Returns the number of images rendered.
    """
    n_rendered = 0
    conc = _get_standard_plume(config)

    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
        )
        conc = dissolved * max_val

    camera_state = _frame_camera(config, conc)

    base_update = {
        "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
        "rendering": RenderingConfig(mode="max", opacity_gamma=1.6),
    }

    # --- Without DOF ---
    cfg_no_dof = config.model_copy(update=base_update)
    cfg_no_dof = cfg_no_dof.model_copy(
        update={
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=True,
                bloom_threshold=0.3,
                bloom_intensity=0.5,
                bloom_passes=4,
                exposure=_EXPOSURE,
                dof=DOFConfig(enabled=False),
            )
        },
    )
    renderer = VolumeRenderer(cfg_no_dof)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(_VIEW_ANGLE)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "dof_off.png")
        n_rendered += 1
    finally:
        renderer.finalize()

    # --- With DOF ---
    cfg_dof = config.model_copy(update=base_update)
    cfg_dof = cfg_dof.model_copy(
        update={
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=True,
                bloom_threshold=0.3,
                bloom_intensity=0.5,
                bloom_passes=4,
                exposure=_EXPOSURE,
                dof=DOFConfig(
                    enabled=True,
                    aperture=2.8,
                    max_blur_radius=12.0,
                    depth_mode="luminance",
                ),
            )
        },
    )
    renderer = VolumeRenderer(cfg_dof)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(_VIEW_ANGLE)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "dof_on.png")
        n_rendered += 1
    finally:
        renderer.finalize()

    return n_rendered


def _render_ecd_turbulence_comparison(
    config: AppConfig,
) -> int:
    """Render turbulence with different amplitude modulators (simulating ECD coupling).

    Uses shared normalization so amplitude differences are preserved across renders.
    Modulator sweep: 1.0, 2.0, 3.0 for visible density progression.
    Returns the number of images rendered.
    """
    n_rendered = 0
    modulators = [1.0, 2.0, 3.0]

    # Generate all plumes first to find shared normalization reference
    plumes = {m: _get_standard_plume(config, modulator=m) for m in modulators}
    all_values = np.concatenate([v.ravel() for v in plumes.values()])
    global_max = float(np.percentile(all_values, 99.9))
    global_max = max(global_max, 1e-8)

    # Camera frames the densest plume (highest modulator)
    camera_state = _frame_camera(config, plumes[modulators[-1]], fill_scale=0.75)

    render_cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=1.6),
        },
    )
    renderer = VolumeRenderer(render_cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(_VIEW_ANGLE)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    gamma = render_cfg.rendering.opacity_gamma

    def shared_norm(c: np.ndarray) -> np.ndarray:
        n = np.clip(c / global_max, 0, 1)
        if gamma != 1.0:
            n = np.power(n, 1.0 / gamma)
        return n.astype(np.float32)

    try:
        for mod in modulators:
            conc = plumes[mod]
            rgb = renderer.render_frame_postprocessed(
                shared_norm(conc), camera_state, pre_normalized=True
            )
            _save_rgb(rgb, OUTPUT_DIR / f"ecd_modulator_{mod:.1f}.png")
            n_rendered += 1
            log.info(f"ecd modulator={mod}", max_conc=round(float(conc.max()), 4))
    finally:
        renderer.finalize()

    return n_rendered


def _render_combined_exhibition(
    config: AppConfig,
) -> int:
    """Render the combined exhibition shot: dissolution + DOF + enhanced turbulence.

    This is the hero image demonstrating all three wave 8 features together.
    Returns the number of images rendered.
    """
    n_rendered = 0

    # Generate plume with enhanced turbulence (simulating ECD modulation)
    conc = _get_standard_plume(config, modulator=1.3)

    # Apply noise dissolution for organic edges
    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
            noise_octaves=4,
            noise_amplitude=1.6,
        )
        conc = dissolved * max_val

    camera_state = _frame_camera(config, conc)

    # Renderer with DOF enabled
    cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=1.6),
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=True,
                bloom_threshold=0.3,
                bloom_intensity=0.5,
                bloom_passes=4,
                exposure=_EXPOSURE,
                dof=DOFConfig(
                    enabled=True,
                    aperture=2.8,
                    max_blur_radius=10.0,
                    depth_mode="luminance",
                ),
            ),
        },
    )
    renderer = VolumeRenderer(cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(_VIEW_ANGLE)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        # Add particle dissolution overlay
        spacing = (config.grid.dx, config.grid.dy, config.grid.dz)
        pdiss_cfg = ParticleDissolutionConfig(
            enabled=True,
            particle_count_scale=4.0,
            particle_scale=550.0,
            particle_opacity=0.80,
        )
        norm = conc / max(float(conc.max()), 1e-8)
        particle_actor = create_dissolution_particles(norm.astype(np.float32), spacing, pdiss_cfg)
        renderer.add_actor(particle_actor)

        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "combined_exhibition.png")
        n_rendered += 1
        log.info(
            "combined exhibition hero shot",
            max_conc=round(float(conc.max()), 4),
            features="dissolution+dof+ecd_modulation",
        )
    finally:
        renderer.finalize()

    return n_rendered


def main() -> None:
    """Generate Wave 8 gallery images."""

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

    _parse_args()
    log.info("wave-8 gallery starting")

    config = _load_exhibition_config()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Particle dissolution: on vs off
    log.info("rendering dissolution comparison")
    n_dissolution = _render_dissolution_comparison(config)

    # 2. Depth of field: on vs off
    log.info("rendering dof comparison")
    n_dof = _render_dof_comparison(config)

    # 3. ECD turbulence coupling: modulator sweep
    log.info("rendering ecd turbulence modulator sweep")
    n_ecd = _render_ecd_turbulence_comparison(config)

    # 4. Combined hero shot: all three features together
    log.info("rendering combined exhibition hero shot")
    n_combined = _render_combined_exhibition(config)

    total = n_dissolution + n_dof + n_ecd + n_combined
    log.info(
        "wave-8 gallery complete",
        total_renders=total,
        dissolution=n_dissolution,
        dof=n_dof,
        ecd=n_ecd,
        combined=n_combined,
        output_dir=str(OUTPUT_DIR),
    )


if __name__ == "__main__":
    main()
