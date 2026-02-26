"""Render exhibition-tier gallery: synthetic volumetric plumes for dark room projection.

Exhibition renders prioritize visual density and atmosphere over physical accuracy.
Uses synthetic Gaussian-envelope + fBm-noise plumes that fill the volume with
organic, clumpy structure. Edge dissolution and ash particles add granularity.

Demonstrates:
- 96x96x64 grid with anisotropic Z-squash for sedimentary folding
- 6-octave fBm noise modulated volumetric clouds
- Edge dissolution (noise-modulated boundary) + ash particle overlay
- Telephoto camera with 60-80% frame fill
- Pure emission rendering (shade=false) via exhibition tier
- No annotations (exhibition tier forbids text overlay)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import structlog
from scipy.ndimage import gaussian_filter

from oco_viz.config import load_config
from oco_viz.config.schema import (
    AppConfig,
    RenderingConfig,
    TransferFunctionConfig,
)
from oco_viz.plume.dissolution import apply_dissolution
from oco_viz.plume.noise import fbm_3d
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer
from scripts.gallery._common import save_rgb

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/exhibition")

IMAGE_MANIFEST: list[str] = [
    *[f"advected_exhibition_t{i * 8}.png" for i in range(4)],
    "compare_gaussian.png",
    "compare_turbulent.png",
    "compare_advected.png",
]


def _load_exhibition_config() -> AppConfig:
    """Load config for exhibition renders."""
    return load_config(
        "dev_mac",
        overrides={
            "grid": {
                "nx": 128,
                "ny": 128,
                "nz": 96,
                "dx": 75.0,
                "dy": 75.0,
                "dz": 35.0,
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
    octaves: int = 6,
    lacunarity: float = 2.0,
    gain: float = 0.5,
) -> np.ndarray:
    """Generate a synthetic volumetric plume for exhibition rendering."""
    nz, ny, nx = shape
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]

    # Wide Gaussian envelope
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

    # Primary fBm noise for organic structure
    noise = fbm_3d(shape, octaves=octaves, lacunarity=lacunarity, gain=gain, seed=seed)

    # Secondary noise field for boundary modulation
    boundary_noise = fbm_3d(shape, octaves=4, lacunarity=2.0, gain=0.55, seed=seed + 7)

    # Tertiary fine-detail noise for internal void pockets and filaments
    detail_noise = fbm_3d(shape, octaves=4, lacunarity=2.5, gain=0.45, seed=seed + 13)

    # Modulate: envelope * (noise * detail_noise)^1.2 creates organic clumps
    combined = noise * (0.5 + 0.5 * detail_noise)
    conc = envelope * np.power(combined, 1.2) * 6.0
    np.clip(conc, 0.0, None, out=conc)

    # Lighter smoothing at higher resolution
    conc = gaussian_filter(conc, sigma=1.0).astype(np.float32)

    # Soft thresholding
    max_val = float(conc.max())
    if max_val > 0:
        cutoff = 0.03 * max_val
        mask = conc < cutoff
        conc[mask] *= (conc[mask] / cutoff) ** 2

    # Noise-modulated radial boundary falloff
    rz, ry, rx = nz / 2.0, ny / 2.0, nx / 2.0
    dist = np.sqrt(
        ((zz - cz) / rz) ** 2 + ((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2,
    ).astype(np.float32)

    falloff_center = 0.35
    falloff_width = 0.15
    noise_amplitude = 0.25
    effective_dist = dist - noise_amplitude * (boundary_noise - 0.5) * 2.0
    boundary = 1.0 - np.clip(
        (effective_dist - falloff_center) / falloff_width,
        0.0,
        1.0,
    )
    conc *= boundary.astype(np.float32)

    return conc.astype(np.float32)


def _build_exhibition_camera(config: AppConfig) -> CameraState:
    """Build a telephoto camera for exhibition framing."""
    grid = config.grid
    fx = grid.nx * grid.dx * 0.45
    fy = grid.ny * grid.dy * 0.5
    fz = grid.nz * grid.dz * 0.45
    grid_extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    cam_dist = grid_extent * 1.6
    return FixedCamera(
        position=(fx + cam_dist * 0.80, fy - cam_dist * 0.15, fz + cam_dist * 0.50),
        focal_point=(fx, fy, fz),
    ).evaluate(0.0)


def _render_to_rgb(
    renderer: VolumeRenderer,
    conc: np.ndarray,
    camera_state: CameraState,
    *,
    with_effects: bool = True,
) -> np.ndarray:
    """Render a concentration field to a float32 RGB array."""
    max_val = float(np.max(conc))
    if with_effects and max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.08,
            high_threshold=0.45,
            noise_octaves=4,
            noise_amplitude=1.6,
        )
        conc[:] = dissolved * max_val

    return renderer.render_frame_postprocessed(
        conc,
        camera_state,
        pre_normalized=False,
    )


def render_wave(
    *,
    tier_override: str | None = None,  # noqa: ARG001
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("exhibition")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    config = _load_exhibition_config()
    shape = config.grid.shape

    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=1.0),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()

    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(45.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    camera_state = _build_exhibition_camera(config)

    try:
        # Time series: 4 frames with evolving plume
        for i, seed_offset in enumerate([0, 100, 200, 300]):
            t_idx = i * 8
            src_x_frac = 0.25 + i * 0.06
            conc = _generate_exhibition_plume(
                shape,
                seed=42 + seed_offset,
                src_frac=(src_x_frac, 0.5, 0.40 + i * 0.01),
                sigma_frac=(0.16 + i * 0.03, 0.13 + i * 0.02, 0.11 + i * 0.015),
            )
            rgb = _render_to_rgb(renderer, conc, camera_state)
            save_rgb(rgb, out / f"advected_exhibition_t{t_idx}.png")

        # Comparison variants
        conc_compact = _generate_exhibition_plume(
            shape,
            seed=77,
            src_frac=(0.35, 0.5, 0.42),
            sigma_frac=(0.15, 0.12, 0.10),
        )
        rgb = _render_to_rgb(renderer, conc_compact, camera_state)
        save_rgb(rgb, out / "compare_gaussian.png")

        conc_spread = _generate_exhibition_plume(
            shape,
            seed=88,
            src_frac=(0.38, 0.5, 0.40),
            sigma_frac=(0.20, 0.15, 0.13),
        )
        rgb = _render_to_rgb(renderer, conc_spread, camera_state)
        save_rgb(rgb, out / "compare_turbulent.png")

        conc_evolved = _generate_exhibition_plume(
            shape,
            seed=342,
            src_frac=(0.42, 0.48, 0.40),
            sigma_frac=(0.25, 0.18, 0.14),
        )
        rgb = _render_to_rgb(renderer, conc_evolved, camera_state)
        save_rgb(rgb, out / "compare_advected.png")

    finally:
        renderer.finalize()

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
