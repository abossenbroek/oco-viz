"""Render exhibition-tier gallery: geological turbulence on high-resolution grid.

Demonstrates:
- 96x96x64 grid with anisotropic Z-squash (dz=300m) for sedimentary folding
- 6-octave turbulence (lacunarity=2.5, gain=0.4, amplitude=0.8, curl=0.4)
- Telephoto camera with 60-80% frame fill
- Pure emission rendering (shade=false) via exhibition tier
- No annotations (exhibition tier forbids text overlay)
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
    AppConfig,
    RenderingConfig,
    TransferFunctionConfig,
)
from oco_viz.data.era5 import load_era5_winds
from oco_viz.plume.advection import advect_sequence
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

FIXTURES_DIR = Path("tests/fixtures")
ERA5_FIXTURE = FIXTURES_DIR / "era5_secunda_2025-10-13.nc"

OUTPUT_DIR = Path("output/examples/exhibition")

# Advection frames to render (sub-frame indices within the advect_sequence output)
FRAME_INDICES = [0, 8, 16, 24]


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Render exhibition gallery images.")
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


def _load_wind(config: AppConfig, *, use_fixture: bool) -> xr.Dataset:
    """Load ERA5 wind data from fixture, or fall back to synthetic wind."""
    if use_fixture and ERA5_FIXTURE.exists():
        log.info("loading ERA5 fixture", path=str(ERA5_FIXTURE))
        return load_era5_winds(ERA5_FIXTURE, config.data_source.domain, config.grid)

    log.info("using synthetic wind field", u=3.0, v=1.0)
    nz, ny, nx = config.grid.shape
    return _build_synthetic_wind(nz, ny, nx)


def _load_exhibition_config() -> AppConfig:
    """Load config with high-resolution grid for exhibition renders.

    Key exhibition overrides:
    - Large grid (96x96x64) with anisotropic Z-squash (dz=300m)
    - 6-octave turbulence (lacunarity=2.5, gain=0.4, amplitude=0.8)
    - Higher emission rate (15000) for visible plume on large grid
    - Exhibition tier handles soot_exhibition TF, shade=false, fog/bloom off
    """
    return load_config(
        "dev_mac",
        overrides={
            "grid": {
                "nx": 96,
                "ny": 96,
                "nz": 64,
                "dx": 1000.0,
                "dy": 1000.0,
                "dz": 300.0,
            },
            "plume": {
                "source_x": 20.0,
                "source_y": 48.0,
                "source_z": 6.0,
                "emission_rate": 15000.0,
            },
            "turbulence": {
                "octaves": 6,
                "lacunarity": 2.5,
                "gain": 0.4,
                "amplitude": 0.8,
                "curl_strength": 0.4,
            },
            "advection": {"dt": 3600.0, "sub_steps": 4, "scheme": "maccormack"},
            "postprocess": {"exposure": 1.5},
        },
        tier="exhibition",
    )


def _build_exhibition_camera(config: AppConfig) -> CameraState:
    """Build a telephoto camera for exhibition framing (60-80% frame fill).

    Camera is placed close (~12km for 96km grid) with a narrow FOV set
    separately via SetViewAngle(18.0). Slightly below plume center looking
    upward for vertical emphasis, offset for asymmetry.
    """
    grid = config.grid
    plume = config.plume
    # Focus on plume center-of-mass area (slightly downwind)
    fx = plume.source_x * grid.dx + 15000.0
    fy = plume.source_y * grid.dy
    fz = plume.source_z * grid.dz + 1500.0
    # Camera CLOSE — ~12km for 96km grid (much closer than study's 20km)
    cam_dist = max(grid.nx * grid.dx, grid.ny * grid.dy) * 0.12
    # Slightly below and to the side for vertical emphasis + asymmetry
    return FixedCamera(
        position=(fx + cam_dist * 0.5, fy - cam_dist * 0.8, fz + cam_dist * 0.15),
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


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file."""
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def _render_advected_time_series(
    renderer: VolumeRenderer,
    adv_ds: xr.Dataset,
    camera_state: CameraState,
) -> int:
    """Render 4 advected plume frames at sub-frame indices 0, 8, 16, 24.

    Returns the number of images rendered.
    """
    n_rendered = 0
    total_frames = adv_ds.sizes["time"]

    for idx in FRAME_INDICES:
        if idx >= total_frames:
            log.warning("frame index out of range", idx=idx, total=total_frames)
            continue
        conc = adv_ds["concentration"].values[idx].astype(np.float32)
        rgb = _render_to_rgb(renderer, conc, camera_state)
        _save_rgb(rgb, OUTPUT_DIR / f"advected_exhibition_t{idx}.png")
        n_rendered += 1

    return n_rendered


def _render_comparison(
    renderer: VolumeRenderer,
    config: AppConfig,
    wind_ds: xr.Dataset,
    adv_ds: xr.Dataset,
    camera_state: CameraState,
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

    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )

    # Gaussian plume
    gaussian_conc = generate_timestep(plume_cfg, config.grid, time_index=0)
    log.info("gaussian plume generated", max_conc=round(float(gaussian_conc.max()), 6))
    rgb = _render_to_rgb(renderer, gaussian_conc, camera_state)
    _save_rgb(rgb, OUTPUT_DIR / "compare_gaussian.png")
    n_rendered += 1

    # Turbulent plume
    turbulent_conc = apply_turbulence(
        gaussian_conc, config.turbulence, config.grid, time_index=0,
    )
    log.info("turbulent plume generated", max_conc=round(float(turbulent_conc.max()), 6))
    rgb = _render_to_rgb(renderer, turbulent_conc, camera_state)
    _save_rgb(rgb, OUTPUT_DIR / "compare_turbulent.png")
    n_rendered += 1

    # Advected plume at sub-frame 8
    total_frames = adv_ds.sizes["time"]
    target_idx = 8
    if target_idx < total_frames:
        adv_conc = adv_ds["concentration"].values[target_idx].astype(np.float32)
        log.info("advected plume (t=8)", max_conc=round(float(adv_conc.max()), 6))
        rgb = _render_to_rgb(renderer, adv_conc, camera_state)
        _save_rgb(rgb, OUTPUT_DIR / "compare_advected.png")
        n_rendered += 1

    return n_rendered


def main() -> None:
    """Generate exhibition gallery images."""
    # 1. Setup logging
    def yaml_renderer(
        _logger: object, _name: str, event_dict: dict[str, object],
    ) -> str:
        return yaml.dump(
            dict(event_dict), default_flow_style=False, sort_keys=False,
        ).rstrip()

    structlog.configure(
        processors=[structlog.stdlib.add_log_level, yaml_renderer],
        wrapper_class=structlog.make_filtering_bound_logger(0),
    )

    args = _parse_args()
    log.info("exhibition gallery starting")

    # 2. Load config (high-res grid, exhibition tier)
    config = _load_exhibition_config()

    # 3. Build wind data (synthetic or ERA5)
    use_fixture = not args.no_fixture
    wind_ds = _load_wind(config, use_fixture=use_fixture)
    log.info("wind data ready", n_times=wind_ds.sizes["time"])

    # 4. Run advect_sequence for 8 major timesteps (= 8*4+1 = 33 sub-frames)
    adv_cfg = AdvectionConfig(
        dt=3600.0, sub_steps=4, scheme="maccormack", mass_correction=True,
    )
    adv_ds = advect_sequence(
        config.plume,
        config.grid,
        wind_ds,
        config.turbulence,
        n_steps=8,
        adv_cfg=adv_cfg,
    )
    n_total_frames = adv_ds.sizes["time"]
    log.info("advection complete", total_frames=n_total_frames)

    # 5. Setup camera (telephoto, close framing)
    camera_state = _build_exhibition_camera(config)

    # 6. Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 7. Create shared renderer with exhibition settings
    #    Exhibition tier already sets soot_exhibition preset, but we override
    #    transfer_function and rendering explicitly for clarity.
    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot_exhibition"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.2),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()

    # Set telephoto FOV — narrow angle for "long lens" look
    assert renderer._renderer is not None  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    renderer._renderer.GetActiveCamera().SetViewAngle(18.0)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    try:
        # 8. Render advected time series (t=0, 8, 16, 24)
        n_time_series = _render_advected_time_series(
            renderer, adv_ds, camera_state,
        )

        # 9. Render comparison: gaussian, turbulent, advected
        n_comparison = _render_comparison(
            renderer, config, wind_ds, adv_ds, camera_state,
        )
    finally:
        renderer.finalize()

    # 10. Log summary
    total = n_time_series + n_comparison
    log.info(
        "exhibition gallery complete",
        total_renders=total,
        time_series=n_time_series,
        comparison=n_comparison,
        output_dir=str(OUTPUT_DIR),
    )


if __name__ == "__main__":
    main()
