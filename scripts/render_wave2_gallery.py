"""Wave-2 gallery: data pipeline diagnostic images — clinical register.

Demonstrates the data pipeline layer:
- Full pipeline Gaussian plume rendered via VTK (study tier)
- ERA5 wind field visualization (synthetic, matplotlib quiver plot)
- OCO-3 sounding footprint geometry (matplotlib patches)
- Coordinate transform grid overlay (matplotlib)

Usage:
    python scripts/render_wave2_gallery.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import structlog
import yaml
from PIL import Image

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, RenderingConfig, TransferFunctionConfig
from oco_viz.data.transform import latlon_to_local_km, local_km_to_latlon
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState, FixedCamera
from oco_viz.render.renderer import VolumeRenderer

matplotlib.use("Agg")

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave2")


def _load_gallery_config() -> AppConfig:
    """Load config with small grid for gallery renders (study tier)."""
    return load_config(
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "plume": {"source_x": 38.0, "source_y": 38.0, "source_z": 3.0},
            "scattering": {"shade": False, "sample_distance": 250.0},
            "output": {"width": 960, "height": 540},
        },
        tier="study",
    )


def _save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file."""
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def render_data_pipeline_gaussian(config: AppConfig) -> None:
    """Render full pipeline Gaussian plume output using VTK."""
    log.info("=== Data pipeline: Gaussian plume ===")

    conc = generate_timestep(config.plume, config.grid, time_index=0)
    log.info("gaussian plume generated", max_conc=round(float(conc.max()), 6))

    grid = config.grid
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)

    camera_state = FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)

    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max"),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        _save_rgb(rgb, OUTPUT_DIR / "data_pipeline_gaussian.png")
    finally:
        renderer.finalize()


def render_era5_wind_profile(config: AppConfig) -> None:
    """Render synthetic ERA5 wind field as a matplotlib quiver plot."""
    log.info("=== Data pipeline: ERA5 wind profile ===")

    grid = config.grid
    nx, ny = 12, 12
    x_km = np.linspace(0, grid.nx * grid.dx / 1000.0, nx)
    y_km = np.linspace(0, grid.ny * grid.dy / 1000.0, ny)
    xx, yy = np.meshgrid(x_km, y_km)

    # Synthetic wind: westerly with slight convergence toward center
    u_wind = 5.0 + 1.5 * np.sin(2 * np.pi * yy / y_km[-1])
    v_wind = 1.0 + 0.8 * np.cos(2 * np.pi * xx / x_km[-1])
    speed = np.sqrt(u_wind**2 + v_wind**2)

    fig, ax = plt.subplots(figsize=(8, 7))
    q = ax.quiver(xx, yy, u_wind, v_wind, speed, cmap="coolwarm", scale=80, width=0.004)
    ax.set_xlabel("East-West (km)", fontsize=11)
    ax.set_ylabel("North-South (km)", fontsize=11)
    ax.set_title("Synthetic ERA5 Wind Field (surface level)", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    cbar = fig.colorbar(q, ax=ax, label="Wind speed (m/s)")
    cbar.ax.tick_params(labelsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "era5_wind_profile.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_oco3_footprints(config: AppConfig) -> None:
    """Render OCO-3 sounding footprint geometry as matplotlib patches."""
    log.info("=== Data pipeline: OCO-3 footprints ===")

    domain = config.data_source.domain
    grid = config.grid

    # Synthetic OCO-3 footprints: 8 along-track x 8 across-track
    n_along, n_across = 8, 8
    footprint_size_km = 2.0
    gap_km = 1.0

    # Center the swath in the domain
    total_across_km = n_across * (footprint_size_km + gap_km)
    total_along_km = n_along * (footprint_size_km + gap_km)
    domain_x_km = grid.nx * grid.dx / 1000.0
    domain_y_km = grid.ny * grid.dy / 1000.0
    x_start = (domain_x_km - total_across_km) / 2.0
    y_start = (domain_y_km - total_along_km) / 2.0

    fig, ax = plt.subplots(figsize=(8, 7))

    # Draw ground plane
    ax.set_facecolor("#f0f0f0")

    # Synthetic XCO2 values: enhancement near center
    xco2_values = []
    patches_list = []
    for i in range(n_along):
        for j in range(n_across):
            x = x_start + j * (footprint_size_km + gap_km)
            y = y_start + i * (footprint_size_km + gap_km)
            dist = math.sqrt(
                (x - domain_x_km / 2) ** 2 + (y - domain_y_km / 2) ** 2
            )
            xco2 = 415.0 + 8.0 * np.exp(-dist**2 / (2 * 10.0**2))
            xco2_values.append(xco2)
            rect = mpatches.FancyBboxPatch(
                (x, y),
                footprint_size_km,
                footprint_size_km,
                boxstyle="round,pad=0.1",
                linewidth=0.5,
                edgecolor="gray",
            )
            patches_list.append(rect)

    xco2_arr = np.array(xco2_values)
    norm = plt.Normalize(vmin=xco2_arr.min(), vmax=xco2_arr.max())
    cmap = plt.cm.RdYlBu_r

    for patch, val in zip(patches_list, xco2_values):
        patch.set_facecolor(cmap(norm(val)))
        patch.set_alpha(0.8)
        ax.add_patch(patch)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, label="XCO2 (ppm)")
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlim(0, domain_x_km)
    ax.set_ylim(0, domain_y_km)
    ax.set_xlabel("East-West (km)", fontsize=11)
    ax.set_ylabel("North-South (km)", fontsize=11)
    ax.set_title("OCO-3 Sounding Footprint Geometry", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "oco3_footprints.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_coordinate_transform(config: AppConfig) -> None:
    """Render lat/lon grid overlaid on local coordinate system."""
    log.info("=== Data pipeline: Coordinate transform ===")

    domain = config.data_source.domain
    grid = config.grid

    domain_x_km = grid.nx * grid.dx / 1000.0
    domain_y_km = grid.ny * grid.dy / 1000.0

    fig, ax = plt.subplots(figsize=(8, 7))

    # Draw local coordinate grid
    ax.set_facecolor("#fafafa")
    for x in np.linspace(0, domain_x_km, 6):
        ax.axvline(x, color="steelblue", alpha=0.3, linewidth=0.8)
    for y in np.linspace(0, domain_y_km, 6):
        ax.axhline(y, color="steelblue", alpha=0.3, linewidth=0.8)

    # Overlay lat/lon labels at grid intersections
    x_ticks = np.linspace(0, domain_x_km, 6)
    y_ticks = np.linspace(0, domain_y_km, 6)

    for x_km in x_ticks:
        for y_km in y_ticks:
            lat, lon = local_km_to_latlon(
                x_km, y_km, origin_lat=domain.origin_lat, origin_lon=domain.origin_lon
            )
            ax.plot(x_km, y_km, "o", color="darkred", markersize=4, zorder=5)
            ax.annotate(
                f"{float(lat):.2f}N\n{float(lon):.2f}E",
                (x_km, y_km),
                fontsize=6,
                ha="left",
                va="bottom",
                xytext=(2, 2),
                textcoords="offset points",
                color="darkred",
            )

    # Mark origin
    ax.plot(0, 0, "s", color="black", markersize=8, zorder=10, label="Domain origin")
    ax.annotate(
        f"Origin: {domain.origin_lat:.2f}N, {domain.origin_lon:.2f}E",
        (0, 0),
        fontsize=9,
        fontweight="bold",
        xytext=(10, -15),
        textcoords="offset points",
    )

    # Draw domain bounding box
    bbox = domain.bbox()
    ax.set_xlabel("East-West (km) — local coordinates", fontsize=11)
    ax.set_ylabel("North-South (km) — local coordinates", fontsize=11)
    ax.set_title(
        f"Coordinate Transform: Local Grid ↔ Geographic\n"
        f"BBox: [{bbox[0]:.2f}E, {bbox[1]:.2f}N] to [{bbox[2]:.2f}E, {bbox[3]:.2f}N]",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlim(-2, domain_x_km + 2)
    ax.set_ylim(-2, domain_y_km + 2)
    ax.set_aspect("equal")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    out_path = OUTPUT_DIR / "coordinate_transform.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def main() -> None:
    """Generate Wave 2 gallery images."""

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

    log.info("wave-2 gallery starting")

    config = _load_gallery_config()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_data_pipeline_gaussian(config)
    render_era5_wind_profile(config)
    render_oco3_footprints(config)
    render_coordinate_transform(config)

    n_files = len(list(OUTPUT_DIR.glob("*.png")))
    log.info("wave-2 gallery complete", total_images=n_files, output_dir=str(OUTPUT_DIR))


if __name__ == "__main__":
    main()
