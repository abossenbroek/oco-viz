"""Render real-data gallery: ERA5 wind-driven advection + OCO-2/3 satellite overlay.

Exercises the full pipeline end-to-end with real fixtures:
  1. Synthetic Sasol plume at t=0
  2. ERA5 reanalysis winds for physical advection
  3. VTK volume rendering with soot transfer function
  4. OCO-2/OCO-3 satellite XCO2 observation overlay
  5. Matplotlib diagnostic panels (footprints, wind profile)

Output directory: ``output/examples/real_data/``
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import structlog

mpl.use("Agg")

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, RenderingConfig, TransferFunctionConfig
from oco_viz.data.era5 import load_era5_winds
from oco_viz.data.oco import load_granule
from oco_viz.data.pipeline import attach_satellite_overlay
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer
from scripts.gallery._common import save_rgb

log = structlog.get_logger()

FIXTURES_DIR = Path("tests/fixtures")
ERA5_OCT13 = FIXTURES_DIR / "era5_secunda_2025-10-13.nc"
ERA5_OCT26 = FIXTURES_DIR / "era5_secunda_2025-10-26.nc"
OCO2_FIXTURE = FIXTURES_DIR / "oco2_secunda_2025-10-13.nc4"
OCO3_FIXTURE = FIXTURES_DIR / "oco3_secunda_2025-10-26.nc4"

OUTPUT_DIR = Path("output/examples/real_data")

# Manifest includes minimum guaranteed images (oct13 + oco2 + comparison + diagnostics).
# Oct26 images are conditional on fixture availability.
IMAGE_MANIFEST: list[str] = [
    *[f"oct13_advected_t{t:02d}.png" for t in [0, 8, 16, 24]],
    "oct13_oco2_overlay.png",
    "compare_synthetic_vs_real_wind.png",
    "diagnostic_oco2_footprint.png",
    "diagnostic_era5_wind_profile.png",
]


def _load_config() -> AppConfig:
    """Load config with gallery-sized grid."""
    return load_config(  # type: ignore[return-value]
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
            "scattering": {"shade": False, "sample_distance": 250.0},
        },
    )


def _camera_state(config: AppConfig) -> CameraState:
    """Build a fixed camera state centred on the grid."""
    grid = config.grid
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    return FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)


def _render_frame(config: AppConfig, conc: np.ndarray, cam_state: CameraState) -> np.ndarray:
    """Render a single concentration frame and return float32 RGB."""
    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max"),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    rgb = renderer.render_frame_postprocessed(conc, cam_state, pre_normalized=False)
    renderer.finalize()
    return rgb


# ── Scene helpers ──────────────────────────────────────────────────


def render_advected_scene(
    config: AppConfig,
    era5_path: Path,
    cam_state: CameraState,
    prefix: str,
    output_dir: Path,
) -> None:
    """Render an ERA5-advected plume sequence for a given date's wind field."""
    grid = config.grid
    domain = config.data_source.domain

    wind_ds = load_era5_winds(era5_path, domain, grid)
    log.info("ERA5 loaded", prefix=prefix, n_times=wind_ds.sizes["time"])

    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )

    n_steps = 25
    ds = advect_sequence(
        plume_cfg,
        grid,
        wind_ds,
        config.turbulence,
        n_steps,
        adv_cfg=config.advection,
    )

    for t in [0, 8, 16, 24]:
        conc = ds["concentration"].isel(time=t).values
        rgb = _render_frame(config, conc, cam_state)
        save_rgb(rgb, output_dir / f"{prefix}_advected_t{t:02d}.png")


def render_overlay_scene(
    config: AppConfig,
    era5_path: Path,
    oco_path: Path,
    cam_state: CameraState,
    prefix: str,
    sat_label: str,
    output_dir: Path,
) -> None:
    """Render a plume + satellite overlay frame."""
    grid = config.grid
    domain = config.data_source.domain

    wind_ds = load_era5_winds(era5_path, domain, grid)
    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )

    ds = advect_sequence(
        plume_cfg,
        grid,
        wind_ds,
        config.turbulence,
        10,
        adv_cfg=config.advection,
    )
    ds = attach_satellite_overlay(ds, [oco_path], domain, grid)

    conc = ds["concentration"].isel(time=-1).values
    rgb = _render_frame(config, conc, cam_state)
    save_rgb(rgb, output_dir / f"{prefix}_{sat_label}_overlay.png")


def render_comparison_scene(
    config: AppConfig,
    era5_path: Path,
    cam_state: CameraState,
    output_dir: Path,
) -> None:
    """Side-by-side comparison: synthetic vs ERA5-driven advection."""
    grid = config.grid
    domain = config.data_source.domain
    n_steps = 10

    synth_conc = generate_timestep(config.plume, grid, time_index=n_steps)
    rgb_synth = _render_frame(config, synth_conc, cam_state)

    wind_ds = load_era5_winds(era5_path, domain, grid)
    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)
    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )
    ds = advect_sequence(
        plume_cfg,
        grid,
        wind_ds,
        config.turbulence,
        n_steps,
        adv_cfg=config.advection,
    )
    real_conc = ds["concentration"].isel(time=-1).values
    rgb_real = _render_frame(config, real_conc, cam_state)

    combined = np.concatenate([rgb_synth, rgb_real], axis=1)
    save_rgb(combined, output_dir / "compare_synthetic_vs_real_wind.png")


# ── Diagnostic panels ─────────────────────────────────────────────


def _render_footprint_diagnostic(oco_path: Path, label: str, output_dir: Path) -> None:
    """Plot satellite footprint XCO2 locations."""
    oco_ds = load_granule(oco_path)
    if "latitude" not in oco_ds or "longitude" not in oco_ds or "xco2" not in oco_ds:
        log.warning("missing fields for diagnostic", path=str(oco_path))
        return

    lats = oco_ds["latitude"].values
    lons = oco_ds["longitude"].values
    xco2 = oco_ds["xco2"].values
    valid = np.isfinite(xco2) & np.isfinite(lats) & np.isfinite(lons)

    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(lons[valid], lats[valid], c=xco2[valid], cmap="turbo", s=10)
    fig.colorbar(sc, ax=ax, label="XCO2 (ppm)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"{label} sounding footprints")
    out = output_dir / f"diagnostic_{label.lower().replace('-', '')}_footprint.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("saved diagnostic", path=str(out))


def _render_wind_diagnostic(era5_path: Path, config: AppConfig, output_dir: Path) -> None:
    """Plot ERA5 wind speed and direction vs altitude."""
    grid = config.grid
    domain = config.data_source.domain
    wind_ds = load_era5_winds(era5_path, domain, grid)

    u = wind_ds["u_wind"].isel(time=0).values
    v = wind_ds["v_wind"].isel(time=0).values
    speed = np.sqrt(u**2 + v**2)

    nz = speed.shape[0]
    z_m = np.arange(nz) * grid.dz
    mean_speed = np.nanmean(speed, axis=(1, 2))
    mean_dir = (
        np.degrees(
            np.arctan2(
                np.nanmean(u, axis=(1, 2)),
                np.nanmean(v, axis=(1, 2)),
            )
        )
        % 360
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))
    ax1.plot(mean_speed, z_m / 1000)
    ax1.set_xlabel("Wind speed (m/s)")
    ax1.set_ylabel("Altitude (km)")
    ax1.set_title("ERA5 wind speed profile")

    ax2.plot(mean_dir, z_m / 1000)
    ax2.set_xlabel("Wind direction (deg)")
    ax2.set_ylabel("Altitude (km)")
    ax2.set_title("ERA5 wind direction profile")

    fig.tight_layout()
    out = output_dir / "diagnostic_era5_wind_profile.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=150, bbox_inches="tight")
    plt.close(fig)
    log.info("saved diagnostic", path=str(out))


# ── Public API ─────────────────────────────────────────────────────


def render_wave(
    *,
    tier_override: str | None = None,  # noqa: ARG001
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("real_data")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    required = {"era5_oct13": ERA5_OCT13, "oco2": OCO2_FIXTURE}
    missing = [k for k, v in required.items() if not v.exists()]
    if missing:
        log.error("missing required fixtures", missing=missing)
        sys.exit(1)

    config = _load_config()
    cam = _camera_state(config)

    render_advected_scene(config, ERA5_OCT13, cam, "oct13", out)
    render_overlay_scene(config, ERA5_OCT13, OCO2_FIXTURE, cam, "oct13", "oco2", out)

    if ERA5_OCT26.exists() and OCO3_FIXTURE.exists():
        render_advected_scene(config, ERA5_OCT26, cam, "oct26", out)
        render_overlay_scene(config, ERA5_OCT26, OCO3_FIXTURE, cam, "oct26", "oco3", out)

    render_comparison_scene(config, ERA5_OCT13, cam, out)

    _render_footprint_diagnostic(OCO2_FIXTURE, "OCO-2", out)
    if OCO3_FIXTURE.exists():
        _render_footprint_diagnostic(OCO3_FIXTURE, "OCO-3", out)
    _render_wind_diagnostic(ERA5_OCT13, config, out)

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
