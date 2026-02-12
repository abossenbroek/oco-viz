"""Wave-2 gallery: data pipeline diagnostic images — clinical register.

Demonstrates the data pipeline layer:
- Full pipeline Gaussian plume rendered via VTK (study tier)
- ERA5 wind field visualization (synthetic, matplotlib quiver plot)
- OCO-3 sounding footprint geometry (matplotlib patches)
- Coordinate transform grid overlay (matplotlib)
- Highveld Industrial Corridor source inventory map (matplotlib)

"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import structlog

from oco_viz.config import load_config
from oco_viz.config.schema import AppConfig, RenderingConfig, TransferFunctionConfig
from oco_viz.data.transform import latlon_to_local_km, local_km_to_latlon
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState
from oco_viz.render.composition import compose_camera_from_plume
from oco_viz.render.renderer import VolumeRenderer
from scripts.gallery._common import save_rgb

matplotlib.use("Agg")

log = structlog.get_logger()

OUTPUT_DIR = Path("output/examples/wave2")

IMAGE_MANIFEST: list[str] = [
    "data_pipeline_gaussian.png",
    "era5_wind_profile.png",
    "oco3_footprints.png",
    "coordinate_transform.png",
    "corridor_source_inventory.png",
]


def _load_gallery_config(*, tier: str = "study") -> AppConfig:
    """Load config with small grid for gallery renders."""
    return load_config(
        "dev_mac",
        overrides={
            "grid": {"nx": 48, "ny": 48, "nz": 32},
            "plume": {"source_x": 33.0, "source_y": 21.0, "source_z": 3.0},
            "scattering": {"shade": False, "sample_distance": 250.0},
            "output": {"width": 960, "height": 540},
        },
        tier=tier,
    )


def render_data_pipeline_gaussian(config: AppConfig, output_dir: Path) -> None:
    """Render full pipeline Gaussian plume output using VTK."""
    log.info("=== Data pipeline: Gaussian plume ===")

    conc = generate_timestep(config.plume, config.grid, time_index=0)
    log.info("gaussian plume generated", max_conc=round(float(conc.max()), 6))

    grid = config.grid
    comp_cfg = config.composition.model_copy(
        update={"enabled": True, "frame_fill": (0.4, 0.6)},
    )
    focal, distance, elevation = compose_camera_from_plume(
        conc, comp_cfg, (grid.dz, grid.dy, grid.dx),
    )
    elev_rad = math.radians(elevation)
    az_rad = math.radians(30.0)
    pos = (
        focal[0] + distance * math.cos(elev_rad) * math.cos(az_rad),
        focal[1] + distance * math.cos(elev_rad) * math.sin(az_rad),
        focal[2] + distance * math.sin(elev_rad),
    )
    camera_state = CameraState(position=pos, focal_point=focal)

    render_config = config.model_copy(
        update={
            "transfer_function": TransferFunctionConfig(preset="soot"),
            "rendering": RenderingConfig(mode="max", opacity_gamma=2.0),
        },
    )
    renderer = VolumeRenderer(render_config)
    renderer.configure()
    try:
        rgb = renderer.render_frame_postprocessed(conc, camera_state, pre_normalized=False)
        save_rgb(rgb, output_dir / "data_pipeline_gaussian.png")
    finally:
        renderer.finalize()


def render_era5_wind_profile(config: AppConfig, output_dir: Path) -> None:
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
    out_path = output_dir / "era5_wind_profile.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_oco3_footprints(config: AppConfig, output_dir: Path) -> None:
    """Render OCO-3 sounding footprint geometry as matplotlib patches."""
    log.info("=== Data pipeline: OCO-3 footprints ===")

    domain = config.data_source.domain
    grid = config.grid

    # Synthetic OCO-3 footprints: 10 along-track x 10 across-track (wider for corridor)
    n_along, n_across = 10, 10
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
            dist = math.sqrt((x - domain_x_km / 2) ** 2 + (y - domain_y_km / 2) ** 2)
            xco2 = 415.0 + 8.0 * np.exp(-(dist**2) / (2 * 10.0**2))
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
    norm = plt.Normalize(vmin=xco2_arr.min(), vmax=xco2_arr.max())  # type: ignore[attr-defined]
    cmap = plt.cm.RdYlBu_r  # type: ignore[attr-defined]

    for patch, val in zip(patches_list, xco2_values):
        patch.set_facecolor(cmap(norm(val)))
        patch.set_alpha(0.8)
        ax.add_patch(patch)

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)  # type: ignore[attr-defined]
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, label="XCO2 (ppm)")
    cbar.ax.tick_params(labelsize=9)

    # Mark Sasol and Joburg positions
    for src in config.data_source.sources:
        if src.name in ("Sasol Synfuels", "Johannesburg"):
            sx, sy = latlon_to_local_km(
                src.lat,
                src.lon,
                origin_lat=domain.origin_lat,
                origin_lon=domain.origin_lon,
            )
            sx = float(sx)
            sy = float(sy)
            if 0 <= sx <= domain_x_km and 0 <= sy <= domain_y_km:
                ax.plot(sx, sy, "*", color="black", markersize=10, zorder=10)
                ax.annotate(
                    src.name,
                    (sx, sy),
                    fontsize=8,
                    fontweight="bold",
                    xytext=(5, 5),
                    textcoords="offset points",
                )

    ax.set_xlim(0, domain_x_km)
    ax.set_ylim(0, domain_y_km)
    ax.set_xlabel("East-West (km)", fontsize=11)
    ax.set_ylabel("North-South (km)", fontsize=11)
    ax.set_title("OCO-3 Sounding Footprint Geometry", fontsize=13, fontweight="bold")
    ax.set_aspect("equal")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    out_path = output_dir / "oco3_footprints.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_coordinate_transform(config: AppConfig, output_dir: Path) -> None:
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

    # Mark Sasol and Joburg landmarks
    for src in config.data_source.sources:
        if src.name in ("Sasol Synfuels", "Johannesburg"):
            sx, sy = latlon_to_local_km(
                src.lat,
                src.lon,
                origin_lat=domain.origin_lat,
                origin_lon=domain.origin_lon,
            )
            sx = float(sx)
            sy = float(sy)
            marker = "^" if src.source_type == "industrial" else "D"
            color = "orangered" if src.source_type == "industrial" else "royalblue"
            ax.plot(sx, sy, marker, color=color, markersize=9, zorder=10, label=src.name)
            ax.annotate(
                f"{src.name}\n({src.lat:.2f}, {src.lon:.2f})",
                (sx, sy),
                fontsize=7,
                fontweight="bold",
                color=color,
                xytext=(8, 5),
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
    out_path = output_dir / "coordinate_transform.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_corridor_source_inventory(config: AppConfig, output_dir: Path) -> None:
    """Render Highveld Industrial Corridor source inventory map."""
    log.info("=== Data pipeline: Corridor source inventory ===")

    domain = config.data_source.domain
    sources = config.data_source.sources

    if not sources:
        log.warning("No sources defined in config — skipping corridor inventory")
        return

    bbox = domain.bbox()
    lon_min, lat_min, lon_max, lat_max = bbox

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_facecolor("#f5f5f0")

    # Domain bounding box outline
    rect = mpatches.Rectangle(
        (lon_min, lat_min),
        lon_max - lon_min,
        lat_max - lat_min,
        linewidth=2,
        edgecolor="steelblue",
        facecolor="none",
        linestyle="--",
        label="Domain extent (300x300 km)",
    )
    ax.add_patch(rect)

    # Lat/lon grid
    for lon_tick in np.arange(math.floor(lon_min), math.ceil(lon_max) + 1, 0.5):
        ax.axvline(lon_tick, color="gray", alpha=0.15, linewidth=0.5)
    for lat_tick in np.arange(math.floor(lat_min), math.ceil(lat_max) + 1, 0.5):
        ax.axhline(lat_tick, color="gray", alpha=0.15, linewidth=0.5)

    # Source markers color-coded by type
    color_map = {"industrial": "orangered", "urban": "royalblue", "point": "darkgreen"}
    marker_map = {"industrial": "^", "urban": "D", "point": "o"}
    size_map = {"industrial": 120, "urban": 100, "point": 60}

    sasol_pos = None
    joburg_pos = None

    for src in sources:
        c = color_map.get(src.source_type, "gray")
        m = marker_map.get(src.source_type, "o")
        s = size_map.get(src.source_type, 60)
        ax.scatter(src.lon, src.lat, c=c, marker=m, s=s, zorder=5, edgecolors="black",
                   linewidths=0.5)
        ax.annotate(
            src.name,
            (src.lon, src.lat),
            fontsize=7,
            fontweight="bold",
            color=c,
            xytext=(6, 4),
            textcoords="offset points",
        )
        if src.name == "Sasol Synfuels":
            sasol_pos = (src.lon, src.lat)
        elif src.name == "Johannesburg":
            joburg_pos = (src.lon, src.lat)

    # Corridor axis line
    if sasol_pos and joburg_pos:
        ax.plot(
            [sasol_pos[0], joburg_pos[0]],
            [sasol_pos[1], joburg_pos[1]],
            "--",
            color="purple",
            linewidth=1.5,
            alpha=0.6,
            label="Sasol-Joburg corridor axis",
        )

    # Domain center marker
    ax.plot(domain.origin_lon, domain.origin_lat, "+", color="black", markersize=12,
            markeredgewidth=2, zorder=10, label="Domain center")

    # Scale bar (50 km)
    km_per_deg_lon = 111.32 * math.cos(math.radians(domain.origin_lat))
    bar_deg = 50.0 / km_per_deg_lon
    bar_y = lat_min + 0.15 * (lat_max - lat_min)
    bar_x = lon_min + 0.05 * (lon_max - lon_min)
    ax.plot([bar_x, bar_x + bar_deg], [bar_y, bar_y], "-", color="black", linewidth=3)
    ax.annotate("50 km", (bar_x + bar_deg / 2, bar_y), fontsize=8, ha="center",
                va="bottom", xytext=(0, 3), textcoords="offset points")

    # Legend entries for source types
    from matplotlib.lines import Line2D  # noqa: PLC0415

    legend_elements = [
        Line2D([0], [0], marker="^", color="w", markerfacecolor="orangered",
               markersize=10, label="Industrial"),
        Line2D([0], [0], marker="D", color="w", markerfacecolor="royalblue",
               markersize=8, label="Urban"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="darkgreen",
               markersize=8, label="Power station"),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=9, framealpha=0.9)

    ax.set_xlabel("Longitude (E)", fontsize=11)
    ax.set_ylabel("Latitude (S)", fontsize=11)
    ax.set_title(
        "Highveld Industrial Corridor — Source Inventory",
        fontsize=13,
        fontweight="bold",
    )
    margin = 0.1
    ax.set_xlim(lon_min - margin, lon_max + margin)
    ax.set_ylim(lat_min - margin, lat_max + margin)
    ax.set_aspect(1.0 / math.cos(math.radians(domain.origin_lat)))
    fig.tight_layout()
    out_path = output_dir / "corridor_source_inventory.png"
    fig.savefig(str(out_path), dpi=150)
    plt.close(fig)
    log.info("saved", path=str(out_path))


def render_wave(
    *,
    tier_override: str | None = None,
    progress: object | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    """Public entry point for unified gallery orchestration."""
    if progress is not None and hasattr(progress, "begin_wave"):
        progress.begin_wave("2")

    out = output_dir if output_dir is not None else OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    effective_tier = tier_override or "study"
    config = _load_gallery_config(tier=effective_tier)

    render_data_pipeline_gaussian(config, out)
    render_era5_wind_profile(config, out)
    render_oco3_footprints(config, out)
    render_coordinate_transform(config, out)
    render_corridor_source_inventory(config, out)

    rendered = [out / name for name in IMAGE_MANIFEST]

    if progress is not None and hasattr(progress, "image_done"):
        for p in rendered:
            progress.image_done(p.name)

    return rendered
