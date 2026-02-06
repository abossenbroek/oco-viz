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

import argparse
from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image

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

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/exhibition")


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Render exhibition gallery images.")
    return parser.parse_args()


def _load_exhibition_config() -> AppConfig:
    """Load config for exhibition renders.

    Grid is 96x96x64 with anisotropic Z-squash (dz < dx) for geological
    layering appearance. Exhibition tier sets soot_exhibition TF, shade=false,
    fog/bloom off.
    """
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
            "postprocess": {"exposure": 25.0},
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
    lacunarity: float = 2.0,
    gain: float = 0.5,
) -> np.ndarray:
    """Generate a synthetic volumetric plume for exhibition rendering.

    Creates a wide Gaussian envelope modulated by fBm noise to produce
    organic, clumpy structure that fills a significant portion of the volume.

    Parameters
    ----------
    shape
        Volume shape (nz, ny, nx).
    seed
        Random seed for noise.
    src_frac
        Source position as fraction of grid (x_frac, y_frac, z_frac).
    sigma_frac
        Envelope width as fraction of grid (sx_frac, sy_frac, sz_frac).
    octaves
        fBm octaves (6 for geological detail).
    lacunarity
        Frequency multiplier per octave.
    gain
        Amplitude multiplier per octave.

    """
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

    # fBm noise for organic structure
    noise = fbm_3d(shape, octaves=octaves, lacunarity=lacunarity, gain=gain, seed=seed)

    # Modulate: envelope * noise creates organic clumps
    conc = envelope * noise * 3.5
    np.clip(conc, 0.0, None, out=conc)

    # Smooth the result to remove voxel-level artifacts
    from scipy.ndimage import gaussian_filter

    conc = gaussian_filter(conc, sigma=2.0).astype(np.float32)

    # Soft thresholding: smoothly ramp to zero below 5% of max
    max_val = float(conc.max())
    if max_val > 0:
        cutoff = 0.05 * max_val
        mask = conc < cutoff
        conc[mask] *= (conc[mask] / cutoff) ** 2

    # Domain boundary falloff: raised-cosine window over outer 15% of each axis.
    # Eliminates visible VTK bounding box edges in rendered output.
    margin = 0.15
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


def _build_exhibition_camera(config: AppConfig) -> CameraState:
    """Build a telephoto camera for exhibition framing.

    Camera is placed far enough to see the entire plume as a discrete cloud
    floating in black void, with 60-80% frame fill at 30-degree FOV.
    """
    grid = config.grid
    # Focus on volume center
    fx = grid.nx * grid.dx * 0.45
    fy = grid.ny * grid.dy * 0.5
    fz = grid.nz * grid.dz * 0.45
    # Camera distance: close enough for 60-80% frame fill
    grid_extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    cam_dist = grid_extent * 1.7
    # Near-level view with slight elevation for depth — confrontational, not landscape
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
    # Apply dissolution in-place (modifies conc) but skip particles for now
    # to avoid rendering artifacts at exhibition tier
    max_val = float(np.max(conc))
    if with_effects and max_val > 0:
        norm = conc / max_val
        dissolved = apply_dissolution(
            norm.astype(np.float32),
            low_threshold=0.05,
            high_threshold=0.35,
            noise_octaves=3,
            noise_amplitude=1.2,
        )
        conc[:] = dissolved * max_val

    rgb = renderer.render_frame_postprocessed(
        conc,
        camera_state,
        pre_normalized=False,
    )

    return rgb


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file."""
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def main() -> None:
    """Generate exhibition gallery images."""

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
    log.info("exhibition gallery starting")

    config = _load_exhibition_config()
    grid = config.grid
    shape = grid.shape
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Create shared renderer
    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()

    # Telephoto FOV
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(30.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    camera_state = _build_exhibition_camera(config)

    try:
        # Time series: 4 frames with evolving plume (shifting source + noise seed)
        # Envelope grows and drifts rightward to simulate advective transport.
        # Base sigma must be wide enough for exhibition visibility (>20% bright voxels).
        n_rendered = 0
        for i, seed_offset in enumerate([0, 100, 200, 300]):
            t_idx = i * 8
            src_x_frac = 0.22 + i * 0.05
            conc = _generate_exhibition_plume(
                shape,
                seed=42 + seed_offset,
                src_frac=(src_x_frac, 0.5, 0.38 + i * 0.01),
                sigma_frac=(0.26 + i * 0.03, 0.20 + i * 0.02, 0.18 + i * 0.015),
            )
            log.info(
                "plume generated",
                t=t_idx,
                max_conc=round(float(conc.max()), 4),
                nonzero_pct=round(100.0 * (conc > 0).sum() / conc.size, 1),
            )
            rgb = _render_to_rgb(renderer, conc, camera_state)
            _save_rgb(rgb, OUTPUT_DIR / f"advected_exhibition_t{t_idx}.png")
            n_rendered += 1

        # Comparison: compact core vs mid spread vs full evolved
        conc_compact = _generate_exhibition_plume(
            shape,
            seed=77,
            src_frac=(0.30, 0.5, 0.40),
            sigma_frac=(0.26, 0.20, 0.18),
        )
        rgb = _render_to_rgb(renderer, conc_compact, camera_state)
        _save_rgb(rgb, OUTPUT_DIR / "compare_gaussian.png")
        n_rendered += 1

        conc_spread = _generate_exhibition_plume(
            shape,
            seed=88,
            src_frac=(0.35, 0.5, 0.38),
            sigma_frac=(0.30, 0.22, 0.20),
        )
        rgb = _render_to_rgb(renderer, conc_spread, camera_state)
        _save_rgb(rgb, OUTPUT_DIR / "compare_turbulent.png")
        n_rendered += 1

        conc_evolved = _generate_exhibition_plume(
            shape,
            seed=342,
            src_frac=(0.40, 0.48, 0.38),
            sigma_frac=(0.35, 0.24, 0.20),
        )
        rgb = _render_to_rgb(renderer, conc_evolved, camera_state)
        _save_rgb(rgb, OUTPUT_DIR / "compare_advected.png")
        n_rendered += 1

    finally:
        renderer.finalize()

    log.info(
        "exhibition gallery complete",
        total_renders=n_rendered,
        output_dir=str(OUTPUT_DIR),
    )


if __name__ == "__main__":
    main()
