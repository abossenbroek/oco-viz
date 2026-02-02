"""Render fixture gallery: 5 TF presets x 3 plume types = 15 example images."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import structlog
import vtk
import xarray as xr
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import RenderingConfig, TransferFunctionConfig
from oco_viz.data.cams import load_cams_co2
from oco_viz.data.era5 import load_era5_winds
from oco_viz.data.oco import load_granule
from oco_viz.data.transform import latlon_to_local_km
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence
from oco_viz.render.camera import FixedCamera
from oco_viz.render.normalize import normalize_concentration
from oco_viz.render.renderer import VolumeRenderer

log = structlog.get_logger()

FIXTURES_DIR = Path("tests/fixtures")
ERA5_FIXTURE = FIXTURES_DIR / "era5_secunda_sample.nc"
OCO3_FIXTURE = FIXTURES_DIR / "oco3_secunda_2025-10-26.nc4"
OCO2_FIXTURE = FIXTURES_DIR / "oco2_secunda_2025-10-13.nc4"
CAMS_FIXTURE = FIXTURES_DIR / "cams_secunda_sample.nc"

OUTPUT_DIR = Path("output/examples")

PRESET_NAMES = [
    "default_plume",
    "cinematic_storm",
    "cinematic_ember",
    "cinematic_atmospheric",
    "absolute_atmospheric",
]


def validate_fixtures() -> None:
    """Fail hard if any required fixture files are missing."""
    missing = [
        str(fixture) for fixture in [ERA5_FIXTURE, OCO3_FIXTURE, OCO2_FIXTURE]
        if not fixture.exists()
    ]
    if missing:
        log.error("missing fixture files", files=missing)
        sys.exit(1)
    log.info("all fixtures present")


def build_oco_overlay_actor(
    oco_ds: object,
    domain_origin_lat: float,
    domain_origin_lon: float,
    grid_dx: float,
    grid_dy: float,
) -> vtk.vtkActor | None:
    """Build VTK point actor for OCO footprint markers on the ground plane.

    Returns a VTK actor with color-coded spheres at OCO footprint locations,
    or None if no valid data.
    """
    if not isinstance(oco_ds, xr.Dataset):
        return None
    if "xco2" not in oco_ds or "latitude" not in oco_ds or "longitude" not in oco_ds:
        return None

    lats = oco_ds["latitude"].values
    lons = oco_ds["longitude"].values
    xco2 = oco_ds["xco2"].values

    valid = np.isfinite(xco2) & np.isfinite(lats) & np.isfinite(lons)
    if not np.any(valid):
        return None

    lats = lats[valid]
    lons = lons[valid]
    xco2 = xco2[valid]

    # Convert to local coordinates (meters)
    x_km, y_km = latlon_to_local_km(
        lats, lons, origin_lat=domain_origin_lat, origin_lon=domain_origin_lon,
    )
    x_m = np.asarray(x_km, dtype=np.float64) * 1000.0
    y_m = np.asarray(y_km, dtype=np.float64) * 1000.0

    # Build VTK points
    points = vtk.vtkPoints()
    scalars = vtk.vtkFloatArray()
    scalars.SetName("xco2")

    for i in range(len(x_m)):
        points.InsertNextPoint(float(x_m[i]), float(y_m[i]), 0.0)
        scalars.InsertNextValue(float(xco2[i]))

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.GetPointData().SetScalars(scalars)

    # Glyph: small sphere at each point
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(min(grid_dx, grid_dy) * 0.5)
    sphere.SetThetaResolution(8)
    sphere.SetPhiResolution(8)

    glypher = vtk.vtkGlyph3D()
    glypher.SetSourceConnection(sphere.GetOutputPort())
    glypher.SetInputData(polydata)
    glypher.SetScaleModeToDataScalingOff()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(glypher.GetOutputPort())
    # Color by XCO2 value
    xco2_range = (float(np.nanmin(xco2)), float(np.nanmax(xco2)))
    if xco2_range[0] < xco2_range[1]:
        mapper.SetScalarRange(xco2_range[0], xco2_range[1])

    lut = vtk.vtkLookupTable()
    lut.SetHueRange(0.33, 0.0)  # green to red
    lut.SetRange(xco2_range[0], xco2_range[1])
    lut.Build()
    mapper.SetLookupTable(lut)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


def _load_gallery_config() -> object:
    """Load config with small grid for gallery renders."""
    white_bg = "--white-bg" in sys.argv
    sky_override = (
        {"top_color": [1.0, 1.0, 1.0], "bottom_color": [0.95, 0.95, 0.95]}
        if white_bg
        else {}
    )
    ground_override = {"color": [0.85, 0.85, 0.85]} if white_bg else {}
    return load_config(
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            # Place source upwind so plume spreads toward grid centre
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
            # Gallery-optimised scattering: shade off for bright volumes on
            # white background; post-processing already provides the cinematic look
            "scattering": {"shade": False, "sample_distance": 250.0},
            **({"sky": sky_override} if sky_override else {}),
            **({"ground_plane": ground_override} if ground_override else {}),
        },
    )


def _build_plume_variants(config, wind_ds):
    """Build gaussian, turbulent, and optional composite plume fields."""
    u_mean = float(np.nanmean(wind_ds["u_wind"].isel(time=0).values))
    v_mean = float(np.nanmean(wind_ds["v_wind"].isel(time=0).values))
    speed = max(math.sqrt(u_mean**2 + v_mean**2), 0.1)
    direction = float(np.degrees(np.arctan2(-u_mean, -v_mean)) % 360)

    plume_cfg = config.plume.model_copy(
        update={"wind_speed": speed, "wind_direction": direction},
    )
    gaussian_conc = generate_timestep(plume_cfg, config.grid, time_index=0)
    log.info("gaussian plume generated", max_conc=round(float(gaussian_conc.max()), 6))

    turbulent_conc = apply_turbulence(gaussian_conc, config.turbulence, config.grid, time_index=0)
    log.info("turbulent plume generated", max_conc=round(float(turbulent_conc.max()), 6))

    variants = {"gaussian": gaussian_conc, "turbulent": turbulent_conc}

    if CAMS_FIXTURE.exists():
        background = load_cams_co2(CAMS_FIXTURE, config.data_source.domain, config.grid)
        variants["composite"] = background + turbulent_conc
        log.info("composite field built", max_conc=round(float(variants["composite"].max()), 3))

    return variants


def _render_all_presets(config, plume_variants, camera_state) -> int:
    """Render all preset x plume_type combinations, return count."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    n_rendered = 0

    for preset_name in PRESET_NAMES:
        for plume_type, conc in plume_variants.items():
            log.info("rendering", preset=preset_name, plume_type=plume_type)

            use_pre_normalized = (
                plume_type == "composite" and preset_name == "absolute_atmospheric"
            )
            render_conc = (
                normalize_concentration(conc, RenderingConfig(mode="absolute"))
                if use_pre_normalized
                else conc
            )

            render_config = config.model_copy(
                update={"transfer_function": TransferFunctionConfig(preset=preset_name)},
            )
            renderer = VolumeRenderer(render_config)
            renderer.configure()
            rgb_pp = renderer.render_frame_postprocessed(
                render_conc, camera_state, pre_normalized=use_pre_normalized,
            )
            renderer.finalize()

            rgb_uint8 = np.clip(rgb_pp * 255.0, 0, 255).astype(np.uint8)
            img = Image.fromarray(rgb_uint8)
            out_path = OUTPUT_DIR / f"{preset_name}_{plume_type}.png"
            img.save(str(out_path))
            log.info("saved", path=str(out_path))
            n_rendered += 1

    return n_rendered


def main() -> None:
    def yaml_renderer(
        _logger: object, _name: str, event_dict: dict[str, object]
    ) -> str:
        return yaml.dump(
            dict(event_dict), default_flow_style=False, sort_keys=False
        ).rstrip()

    structlog.configure(
        processors=[structlog.stdlib.add_log_level, yaml_renderer],
        wrapper_class=structlog.make_filtering_bound_logger(0),
    )

    log.info("render gallery starting")
    validate_fixtures()

    config = _load_gallery_config()

    wind_ds = load_era5_winds(ERA5_FIXTURE, config.data_source.domain, config.grid)
    log.info("ERA5 winds ready", n_times=wind_ds.sizes["time"])

    oco3_ds = load_granule(OCO3_FIXTURE)
    oco2_ds = load_granule(OCO2_FIXTURE)

    plume_variants = _build_plume_variants(config, wind_ds)

    domain = config.data_source.domain
    overlay_actors = [
        a for a in [
            build_oco_overlay_actor(
                oco3_ds, domain.origin_lat, domain.origin_lon, config.grid.dx, config.grid.dy,
            ),
            build_oco_overlay_actor(
                oco2_ds, domain.origin_lat, domain.origin_lon, config.grid.dx, config.grid.dy,
            ),
        ] if a is not None
    ]
    log.info("OCO overlay actors", count=len(overlay_actors))

    grid = config.grid
    cx, cy = grid.nx * grid.dx / 2.0, grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    # Scale camera distance to grid extent so plume is visible
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    camera_state = FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.5),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)

    n_rendered = _render_all_presets(config, plume_variants, camera_state)
    log.info("gallery complete", total_renders=n_rendered, output_dir=str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
