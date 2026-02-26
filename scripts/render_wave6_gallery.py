"""Render Wave 6 gallery: advected plume evolution, overlay, and annotations.

Demonstrates:
- Semi-Lagrangian advection with MacCormack correction
- Temporal plume evolution across multiple timesteps
- PIL text annotations (timestamp, facility, credits, scale bar)
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import structlog
import xarray as xr

from oco_viz.config import load_config
from oco_viz.config.schema import (
    AdvectionConfig,
    AnnotationConfig,
    AppConfig,
    RenderingConfig,
    TransferFunctionConfig,
)
from oco_viz.data.era5 import load_era5_winds
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.annotations import apply_annotations
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer
from scripts.gallery._common import save_rgb

log = structlog.get_logger()

FIXTURES_DIR = Path("tests/fixtures")
ERA5_FIXTURE = FIXTURES_DIR / "era5_secunda_2025-10-13.nc"

OUTPUT_DIR = Path("output/examples/wave6")

# Advection frames to render (sub-frame indices within the advect_sequence output)
FRAME_INDICES = [0, 8, 16, 24]

IMAGE_MANIFEST: list[str] = [
    *[f"advected_study_t{i}.png" for i in FRAME_INDICES],
    "advected_study_annotated.png",
    "compare_gaussian.png",
    "compare_turbulent.png",
    "compare_advected.png",
]


def _build_synthetic_wind(nz: int, ny: int, nx: int) -> xr.Dataset:
    """Build a uniform synthetic wind field for advection demos.

    Wind is 3 m/s eastward (u) and 1 m/s northward (v).
    """
    return xr.Dataset(
        {
            "u_wind": (
                ["time", "z", "y", "x"],
                np.full((1, nz, ny, nx), 3.0, dtype=np.float32),
            ),
            "v_wind": (
                ["time", "z", "y", "x"],
                np.full((1, nz, ny, nx), 1.0, dtype=np.float32),
            ),
        },
    )


def _load_wind(config: AppConfig, *, use_fixture: bool) -> xr.Dataset:
    """Load ERA5 wind data from fixture, or fall back to synthetic wind."""
    if use_fixture and ERA5_FIXTURE.exists():
        log.info("loading ERA5 fixture", path=str(ERA5_FIXTURE))
        return load_era5_winds(ERA5_FIXTURE, config.data_source.domain, config.grid)

    log.info("using synthetic wind field", u=3.0, v=1.0)
    nz, ny, nx = config.grid.shape
    return _build_synthetic_wind(nz, ny, nx)


def _load_gallery_config() -> AppConfig:
    """Load config with small grid for gallery renders (study tier, soot preset)."""
    return load_config(
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "plume": {
                "source_x": 10.0,
                "source_y": 24.0,
                "source_z": 3.0,
                "emission_rate": 8000.0,
            },
            "scattering": {"shade": False},
            "advection": {"dt": 3600.0, "sub_steps": 4, "scheme": "maccormack"},
            "postprocess": {
                "bloom_threshold": 0.25,
                "bloom_intensity": 0.30,
                "fog_density": 0.06,
                "exposure": 6.0,
            },
        },
        tier="study",
    )


def _build_camera(config: AppConfig) -> CameraState:
    """Build a fixed camera positioned to frame the plume."""
    grid = config.grid
    plume = config.plume
    fx = plume.source_x * grid.dx + 8000.0
    fy = plume.source_y * grid.dy
    fz = plume.source_z * grid.dz + 2000.0
    cam_dist = max(grid.nx * grid.dx, grid.ny * grid.dy) * 0.4
    return FixedCamera(
        position=(fx + cam_dist * 0.7, fy - cam_dist * 0.5, fz + cam_dist * 0.3),
        focal_point=(fx, fy, fz),
    ).evaluate(0.0)


def _render_to_rgb(
    renderer: VolumeRenderer,
    conc: np.ndarray,
    camera_state: CameraState,
) -> np.ndarray:
    """Render a concentration field to a float32 RGB array via the shared renderer."""
    return renderer.render_frame_postprocessed(
        conc,
        camera_state,
        pre_normalized=False,
    )


def _render_advected_time_series(
    renderer: VolumeRenderer,
    adv_ds: xr.Dataset,
    camera_state: CameraState,
    output_dir: Path,
) -> int:
    """Render 4 advected plume frames. Returns the number of images rendered."""
    n_rendered = 0
    total_frames = adv_ds.sizes["time"]

    for idx in FRAME_INDICES:
        if idx >= total_frames:
            log.warning("frame index out of range", idx=idx, total=total_frames)
            continue
        conc = adv_ds["concentration"].values[idx].astype(np.float32)
        rgb = _render_to_rgb(renderer, conc, camera_state)
        save_rgb(rgb, output_dir / f"advected_study_t{idx}.png")
        n_rendered += 1

    return n_rendered


def _render_annotated_frame(
    renderer: VolumeRenderer,
    config: AppConfig,
    adv_ds: xr.Dataset,
    camera_state: CameraState,
    output_dir: Path,
) -> int:
    """Render annotated frame at t=16 (mid-sequence). Returns 1 on success."""
    total_frames = adv_ds.sizes["time"]
    target_idx = 16
    if target_idx >= total_frames:
        log.warning(
            "annotated frame index out of range",
            idx=target_idx,
            total=total_frames,
        )
        return 0

    conc = adv_ds["concentration"].values[target_idx].astype(np.float32)
    rgb_pp = _render_to_rgb(renderer, conc, camera_state)

    annotation_cfg = AnnotationConfig(
        show_timestamp=True,
        show_facility=True,
        show_credits=True,
        show_scale_bar=True,
        font_size=18,
        facility_name="Sasol Secunda",
    )

    rgb_annotated = apply_annotations(
        rgb_pp,
        annotation_cfg,
        frame_meta={
            "timestamp": "2024-01-15 14:00 UTC",
            "frame_index": target_idx,
            "total_frames": total_frames,
            "grid_dx_m": config.grid.dx,
        },
    )

    save_rgb(rgb_annotated, output_dir / "advected_study_annotated.png")
    return 1


def _render_comparison(
    renderer: VolumeRenderer,
    config: AppConfig,
    wind_ds: xr.Dataset,
    adv_ds: xr.Dataset,
    camera_state: CameraState,
    output_dir: Path,
) -> int:
    """Render gaussian, turbulent, and advected (t=8) for comparison."""
    n_rendered = 0

    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )

    # Gaussian plume
    gaussian_conc = generate_timestep(plume_cfg, config.grid, time_index=0)
    log.info("gaussian plume generated", max_conc=round(float(gaussian_conc.max()), 6))
    rgb = _render_to_rgb(renderer, gaussian_conc, camera_state)
    save_rgb(rgb, output_dir / "compare_gaussian.png")
    n_rendered += 1

    # Turbulent plume
    turbulent_conc = apply_turbulence(
        gaussian_conc,
        config.turbulence,
        config.grid,
        time_index=0,
    )
    log.info("turbulent plume generated", max_conc=round(float(turbulent_conc.max()), 6))
    rgb = _render_to_rgb(renderer, turbulent_conc, camera_state)
    save_rgb(rgb, output_dir / "compare_turbulent.png")
    n_rendered += 1

    # Advected plume at sub-frame 8
    total_frames = adv_ds.sizes["time"]
    target_idx = 8
    if target_idx < total_frames:
        adv_conc = adv_ds["concentration"].values[target_idx].astype(np.float32)
        log.info("advected plume (t=8)", max_conc=round(float(adv_conc.max()), 6))
        rgb = _render_to_rgb(renderer, adv_conc, camera_state)
        save_rgb(rgb, output_dir / "compare_advected.png")
        n_rendered += 1

    return n_rendered


def render_wave(
    *,
    tier_override: str | None = None,  # noqa: ARG001
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("6")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    config = _load_gallery_config()
    wind_ds = _load_wind(config, use_fixture=True)

    adv_cfg = AdvectionConfig(
        dt=3600.0,
        sub_steps=4,
        scheme="maccormack",
        mass_correction=True,
    )
    adv_ds = advect_sequence(
        config.plume,
        config.grid,
        wind_ds,
        config.turbulence,
        n_steps=8,
        adv_cfg=adv_cfg,
    )

    camera_state = _build_camera(config)

    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=1.0),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()

    try:
        _render_advected_time_series(renderer, adv_ds, camera_state, out)
        _render_annotated_frame(renderer, config, adv_ds, camera_state, out)
        _render_comparison(renderer, config, wind_ds, adv_ds, camera_state, out)
    finally:
        renderer.finalize()

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
