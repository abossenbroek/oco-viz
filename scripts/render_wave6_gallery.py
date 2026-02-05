"""Render Wave 6 gallery: advected plume evolution, overlay, and annotations.

Demonstrates:
- Semi-Lagrangian advection with MacCormack correction
- Temporal plume evolution across multiple timesteps
- PIL text annotations (timestamp, facility, credits, scale bar)
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import structlog
import xarray as xr
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import (
    AdvectionConfig,
    AnnotationConfig,
    RenderingConfig,
    TransferFunctionConfig,
)
from oco_viz.data.era5 import load_era5_winds
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.annotations import apply_annotations
from oco_viz.render.camera import FixedCamera
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

FIXTURES_DIR = Path("tests/fixtures")
ERA5_FIXTURE = FIXTURES_DIR / "era5_secunda_2025-10-13.nc"

OUTPUT_DIR = Path("output/examples/wave6")

# Advection frames to render (sub-frame indices within the advect_sequence output)
FRAME_INDICES = [0, 4, 8, 12]


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Render Wave 6 gallery images.")
    parser.add_argument(
        "--no-fixture",
        action="store_true",
        help="Force synthetic wind data even if ERA5 fixture exists.",
    )
    return parser.parse_args()


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


def _load_wind(config: object, *, use_fixture: bool) -> xr.Dataset:
    """Load ERA5 wind data from fixture, or fall back to synthetic wind.

    Parameters
    ----------
    config
        Application config (must have grid and data_source attributes).
    use_fixture
        Whether to attempt loading the ERA5 fixture file.

    """
    if use_fixture and ERA5_FIXTURE.exists():
        log.info("loading ERA5 fixture", path=str(ERA5_FIXTURE))
        return load_era5_winds(ERA5_FIXTURE, config.data_source.domain, config.grid)  # type: ignore[attr-defined]

    log.info("using synthetic wind field", u=3.0, v=1.0)
    nz, ny, nx = config.grid.shape  # type: ignore[attr-defined]
    return _build_synthetic_wind(nz, ny, nx)


def _load_gallery_config() -> object:
    """Load config with small grid for gallery renders (study tier, soot preset)."""
    return load_config(
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "plume": {"source_x": 10.0, "source_y": 24.0, "source_z": 3.0},
            "scattering": {"shade": False, "sample_distance": 250.0},
            "advection": {"dt": 3600.0, "sub_steps": 4, "scheme": "maccormack"},
        },
        tier="study",
    )


def _build_camera(config: object) -> object:
    """Build a fixed camera positioned to show the full grid."""
    grid = config.grid  # type: ignore[attr-defined]
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    return FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)


def _render_and_save(
    config: object,
    conc: np.ndarray,
    camera_state: object,
    out_path: Path,
) -> None:
    """Render a single concentration field and save as PNG."""
    render_config = config.model_copy(  # type: ignore[attr-defined]
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max"),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    rgb_pp = renderer.render_frame_postprocessed(
        conc,
        camera_state,
        pre_normalized=False,
    )
    renderer.finalize()

    rgb_uint8 = np.clip(rgb_pp * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def _render_annotated(
    config: object,
    conc: np.ndarray,
    camera_state: object,
    out_path: Path,
    frame_index: int,
    total_frames: int,
) -> None:
    """Render a concentration field with all annotations enabled."""
    render_config = config.model_copy(  # type: ignore[attr-defined]
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max"),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    rgb_pp = renderer.render_frame_postprocessed(
        conc,
        camera_state,
        pre_normalized=False,
    )
    renderer.finalize()

    annotation_cfg = AnnotationConfig(
        show_timestamp=True,
        show_facility=True,
        show_credits=True,
        show_scale_bar=True,
        font_size=18,
        facility_name="Sasol Secunda",
    )

    grid = config.grid  # type: ignore[attr-defined]
    rgb_annotated = apply_annotations(
        rgb_pp,
        annotation_cfg,
        frame_meta={
            "timestamp": "2024-01-15 14:00 UTC",
            "frame_index": frame_index,
            "total_frames": total_frames,
            "grid_dx_m": grid.dx,
        },
    )

    rgb_uint8 = np.clip(rgb_annotated * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def _render_advected_time_series(
    config: object,
    adv_ds: xr.Dataset,
    camera_state: object,
) -> int:
    """Render 4 advected plume frames at sub-frame indices 0, 4, 8, 12.

    Returns the number of images rendered.
    """
    n_rendered = 0
    total_frames = adv_ds.sizes["time"]

    for idx in FRAME_INDICES:
        if idx >= total_frames:
            log.warning("frame index out of range", idx=idx, total=total_frames)
            continue
        conc = adv_ds["concentration"].values[idx].astype(np.float32)
        out_path = OUTPUT_DIR / f"advected_study_t{idx}.png"
        _render_and_save(config, conc, camera_state, out_path)
        n_rendered += 1

    return n_rendered


def _render_annotated_frame(
    config: object,
    adv_ds: xr.Dataset,
    camera_state: object,
) -> int:
    """Render annotated frame at t=8. Returns 1 on success."""
    total_frames = adv_ds.sizes["time"]
    target_idx = 8
    if target_idx >= total_frames:
        log.warning("annotated frame index out of range", idx=target_idx, total=total_frames)
        return 0

    conc = adv_ds["concentration"].values[target_idx].astype(np.float32)
    out_path = OUTPUT_DIR / "advected_study_annotated.png"
    _render_annotated(config, conc, camera_state, out_path, target_idx, total_frames)
    return 1


def _render_comparison(
    config: object,
    wind_ds: xr.Dataset,
    adv_ds: xr.Dataset,
    camera_state: object,
) -> int:
    """Render gaussian, turbulent, and advected (t=8) for comparison.

    Returns the number of images rendered.
    """
    n_rendered = 0

    # Derive wind speed and direction from wind data
    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

    plume_cfg = config.plume.model_copy(  # type: ignore[attr-defined]
        update={"wind_speed": speed, "wind_direction": direction},
    )

    # Gaussian plume
    gaussian_conc = generate_timestep(plume_cfg, config.grid, time_index=0)  # type: ignore[attr-defined]
    log.info("gaussian plume generated", max_conc=round(float(gaussian_conc.max()), 6))
    _render_and_save(
        config,
        gaussian_conc,
        camera_state,
        OUTPUT_DIR / "compare_gaussian.png",
    )
    n_rendered += 1

    # Turbulent plume
    turbulent_conc = apply_turbulence(
        gaussian_conc, config.turbulence, config.grid, time_index=0,  # type: ignore[attr-defined]
    )
    log.info("turbulent plume generated", max_conc=round(float(turbulent_conc.max()), 6))
    _render_and_save(
        config,
        turbulent_conc,
        camera_state,
        OUTPUT_DIR / "compare_turbulent.png",
    )
    n_rendered += 1

    # Advected plume at t=8
    total_frames = adv_ds.sizes["time"]
    target_idx = 8
    if target_idx < total_frames:
        adv_conc = adv_ds["concentration"].values[target_idx].astype(np.float32)
        log.info("advected plume (t=8)", max_conc=round(float(adv_conc.max()), 6))
        _render_and_save(
            config,
            adv_conc,
            camera_state,
            OUTPUT_DIR / "compare_advected.png",
        )
        n_rendered += 1

    return n_rendered


def main() -> None:
    """Generate Wave 6 gallery images."""
    # 1. Setup logging
    def yaml_renderer(_logger: object, _name: str, event_dict: dict[str, object]) -> str:
        return yaml.dump(dict(event_dict), default_flow_style=False, sort_keys=False).rstrip()

    structlog.configure(
        processors=[structlog.stdlib.add_log_level, yaml_renderer],
        wrapper_class=structlog.make_filtering_bound_logger(0),
    )

    args = _parse_args()
    log.info("wave-6 gallery starting")

    # 2. Load config (small grid, study tier)
    config = _load_gallery_config()

    # 3. Build wind data (synthetic or ERA5)
    use_fixture = not args.no_fixture
    wind_ds = _load_wind(config, use_fixture=use_fixture)
    log.info("wind data ready", n_times=wind_ds.sizes["time"])

    # 4. Run advect_sequence for 3 major timesteps (= 3*4+1 = 13 sub-frames)
    adv_cfg = AdvectionConfig(dt=3600.0, sub_steps=4, scheme="maccormack")
    adv_ds = advect_sequence(
        config.plume,  # type: ignore[attr-defined]
        config.grid,  # type: ignore[attr-defined]
        wind_ds,
        config.turbulence,  # type: ignore[attr-defined]
        n_steps=3,
        adv_cfg=adv_cfg,
    )
    n_total_frames = adv_ds.sizes["time"]
    log.info("advection complete", total_frames=n_total_frames)

    # 5. Setup camera
    camera_state = _build_camera(config)

    # 6. Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 7. Render advected time series (t=0, 4, 8, 12)
    n_time_series = _render_advected_time_series(config, adv_ds, camera_state)

    # 8. Render annotated frame (t=8)
    n_annotated = _render_annotated_frame(config, adv_ds, camera_state)

    # 9. Render comparison: gaussian, turbulent, advected
    n_comparison = _render_comparison(config, wind_ds, adv_ds, camera_state)

    # 10. Log summary
    total = n_time_series + n_annotated + n_comparison
    log.info(
        "wave-6 gallery complete",
        total_renders=total,
        time_series=n_time_series,
        annotated=n_annotated,
        comparison=n_comparison,
        output_dir=str(OUTPUT_DIR),
    )


if __name__ == "__main__":
    main()
