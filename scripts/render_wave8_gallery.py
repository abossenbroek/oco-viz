"""Render Wave 8 gallery: particle dissolution, depth of field, and ECD coupling.

Demonstrates:
- Particle dissolution at volume boundaries (vtkPointGaussianMapper billboard)
- Shallow depth of field (variable Gaussian blur, dual focal-distance strategy)
- ECD-driven turbulence amplitude modulation
- Exhibition-tier rendering with all three features combined
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image
from scipy.ndimage import gaussian_filter

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
from oco_viz.plume.noise import fbm_3d
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.particle_dissolve import create_dissolution_particles
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render Wave 8 gallery images.")
    return parser.parse_args()


def _load_exhibition_config(*, dof_enabled: bool = False) -> AppConfig:
    """Load exhibition config with wave 8 features.

    Grid is 96x96x64 with anisotropic Z-squash. DOF can be toggled per render.
    """
    dof_override: dict[str, object] = {"enabled": dof_enabled, "aperture": 2.8}
    if dof_enabled:
        dof_override["max_blur_radius"] = 8.0

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
            "postprocess": {"exposure": 25.0, "dof": dof_override},
            "particle_dissolution": {
                "enabled": True,
                "threshold": 0.05,
                "particle_count_scale": 1.0,
                "particle_scale": 150.0,
                "particle_opacity": 0.4,
            },
        },
        tier="exhibition",
    )


def _generate_exhibition_plume(
    shape: tuple[int, int, int],
    *,
    seed: int = 42,
    src_frac: tuple[float, float, float] = (0.15, 0.5, 0.35),
    sigma_frac: tuple[float, float, float] = (0.35, 0.22, 0.20),
    octaves: int = 4,
) -> np.ndarray:
    """Generate a synthetic volumetric plume for exhibition rendering."""
    nz, ny, nx = shape
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]

    cx = src_frac[0] * nx
    cy = src_frac[1] * ny
    cz = src_frac[2] * nz
    sx = sigma_frac[0] * nx
    sy = sigma_frac[1] * ny
    sz = sigma_frac[2] * nz

    envelope = np.exp(
        -((xx - cx) ** 2 / (2 * sx**2))
        - (yy - cy) ** 2 / (2 * sy**2)
        - (zz - cz) ** 2 / (2 * sz**2),
    ).astype(np.float32)

    noise = fbm_3d(shape, octaves=octaves, lacunarity=2.0, gain=0.5, seed=seed)
    conc = envelope * noise * 3.5
    np.clip(conc, 0.0, None, out=conc)
    conc = gaussian_filter(conc, sigma=2.0).astype(np.float32)

    max_val = float(conc.max())
    if max_val > 0:
        cutoff = 0.05 * max_val
        mask = conc < cutoff
        conc[mask] *= (conc[mask] / cutoff) ** 2

    # Domain boundary falloff
    margin = 0.25
    for axis, n in enumerate(shape):
        m = int(n * margin)
        if m < 1:
            continue
        ramp = np.ones(n, dtype=np.float32)
        t = np.linspace(0.0, np.pi / 2, m, dtype=np.float32)
        ramp[:m] = np.sin(t) ** 2
        ramp[-m:] = np.sin(t[::-1]) ** 2
        slices: list[None | slice] = [None, None, None]
        slices[axis] = slice(None)
        conc *= ramp[tuple(slices)]

    return conc.astype(np.float32)


def _build_camera(config: AppConfig) -> CameraState:
    """Build a telephoto camera for exhibition framing."""
    grid = config.grid
    fx = grid.nx * grid.dx * 0.45
    fy = grid.ny * grid.dy * 0.5
    fz = grid.nz * grid.dz * 0.45
    grid_extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    cam_dist = grid_extent * 1.7
    return FixedCamera(
        position=(fx + cam_dist * 0.80, fy - cam_dist * 0.15, fz + cam_dist * 0.50),
        focal_point=(fx, fy, fz),
    ).evaluate(0.0)


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file."""
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def _render_dissolution_comparison(
    config: AppConfig,
    shape: tuple[int, int, int],
    camera_state: CameraState,
) -> int:
    """Render with and without particle dissolution overlay.

    Returns the number of images rendered.
    """
    n_rendered = 0
    conc = _generate_exhibition_plume(shape, seed=42)

    # Normalize for dissolution
    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
            noise_octaves=3,
            noise_amplitude=1.2,
        )
        conc_dissolved = dissolved * max_val
    else:
        conc_dissolved = conc.copy()

    # --- Without particle dissolution ---
    render_cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
        },
    )
    renderer = VolumeRenderer(render_cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

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
    shape: tuple[int, int, int],
    camera_state: CameraState,
) -> int:
    """Render with and without depth of field.

    Returns the number of images rendered.
    """
    n_rendered = 0
    conc = _generate_exhibition_plume(shape, seed=88)

    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
        )
        conc = dissolved * max_val

    base_update = {
        "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
        "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
    }

    # --- Without DOF ---
    cfg_no_dof = config.model_copy(update=base_update)
    cfg_no_dof = cfg_no_dof.model_copy(
        update={
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=False,
                exposure=25.0,
                dof=DOFConfig(enabled=False),
            )
        },
    )
    renderer = VolumeRenderer(cfg_no_dof)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

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
                bloom_enabled=False,
                exposure=25.0,
                dof=DOFConfig(enabled=True, aperture=2.8, max_blur_radius=8.0),
            )
        },
    )
    renderer = VolumeRenderer(cfg_dof)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "dof_on.png")
        n_rendered += 1
    finally:
        renderer.finalize()

    return n_rendered


def _render_ecd_turbulence_comparison(
    config: AppConfig,
    shape: tuple[int, int, int],
    camera_state: CameraState,
) -> int:
    """Render turbulence with different amplitude modulators (simulating ECD coupling).

    Returns the number of images rendered.
    """
    n_rendered = 0

    # Base Gaussian plume
    plume_cfg = config.plume.model_copy(
        update={
            "source_x": shape[2] * 0.25,
            "source_y": shape[1] * 0.5,
            "emission_rate": 5000.0,
        },
    )
    base = generate_timestep(plume_cfg, config.grid, time_index=0)

    render_cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
        },
    )
    renderer = VolumeRenderer(render_cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        # Modulator = 1.0 (baseline, no ECD)
        turb_1 = apply_turbulence(base, config.turbulence, config.grid, 0, amplitude_modulator=1.0)
        rgb = renderer.render_frame_postprocessed(turb_1, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "ecd_modulator_1.0.png")
        n_rendered += 1
        log.info("ecd modulator=1.0", max_conc=round(float(turb_1.max()), 4))

        # Modulator = 1.5 (moderate ECD anomaly)
        turb_15 = apply_turbulence(
            base, config.turbulence, config.grid, 0, amplitude_modulator=1.5
        )
        rgb = renderer.render_frame_postprocessed(turb_15, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "ecd_modulator_1.5.png")
        n_rendered += 1
        log.info("ecd modulator=1.5", max_conc=round(float(turb_15.max()), 4))

        # Modulator = 2.0 (strong ECD anomaly)
        turb_20 = apply_turbulence(
            base, config.turbulence, config.grid, 0, amplitude_modulator=2.0
        )
        rgb = renderer.render_frame_postprocessed(turb_20, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "ecd_modulator_2.0.png")
        n_rendered += 1
        log.info("ecd modulator=2.0", max_conc=round(float(turb_20.max()), 4))
    finally:
        renderer.finalize()

    return n_rendered


def _render_combined_exhibition(
    config: AppConfig,
    shape: tuple[int, int, int],
    camera_state: CameraState,
) -> int:
    """Render the combined exhibition shot: dissolution + DOF + enhanced turbulence.

    This is the hero image demonstrating all three wave 8 features together.
    Returns the number of images rendered.
    """
    n_rendered = 0

    # Generate plume with enhanced turbulence (simulating ECD modulation)
    plume_cfg = config.plume.model_copy(
        update={
            "source_x": shape[2] * 0.25,
            "source_y": shape[1] * 0.5,
            "emission_rate": 5000.0,
        },
    )
    base = generate_timestep(plume_cfg, config.grid, time_index=0)
    conc = apply_turbulence(base, config.turbulence, config.grid, 0, amplitude_modulator=1.3)

    # Apply noise dissolution for organic edges
    max_val = float(np.max(conc))
    if max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
            noise_octaves=4,
            noise_amplitude=1.3,
        )
        conc = dissolved * max_val

    # Renderer with DOF enabled
    cfg = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
            "postprocess": PostProcessConfig(
                fog_enabled=False,
                bloom_enabled=False,
                exposure=25.0,
                dof=DOFConfig(enabled=True, aperture=2.8, max_blur_radius=6.0),
            ),
        },
    )
    renderer = VolumeRenderer(cfg)
    renderer.configure()
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        # Add particle dissolution overlay
        spacing = (config.grid.dx, config.grid.dy, config.grid.dz)
        pdiss_cfg = ParticleDissolutionConfig(
            enabled=True,
            particle_count_scale=1.2,
            particle_scale=180.0,
            particle_opacity=0.35,
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
    shape = config.grid.shape
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    camera_state = _build_camera(config)

    # 1. Particle dissolution: on vs off
    log.info("rendering dissolution comparison")
    n_dissolution = _render_dissolution_comparison(config, shape, camera_state)

    # 2. Depth of field: on vs off
    log.info("rendering dof comparison")
    n_dof = _render_dof_comparison(config, shape, camera_state)

    # 3. ECD turbulence coupling: modulator sweep
    log.info("rendering ecd turbulence modulator sweep")
    n_ecd = _render_ecd_turbulence_comparison(config, shape, camera_state)

    # 4. Combined hero shot: all three features together
    log.info("rendering combined exhibition hero shot")
    n_combined = _render_combined_exhibition(config, shape, camera_state)

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
