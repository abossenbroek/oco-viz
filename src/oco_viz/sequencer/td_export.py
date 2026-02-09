"""TouchDesigner VDB + point cloud export for downstream TD/Houdini pipelines."""

from __future__ import annotations

import json
import logging
import math
from typing import TYPE_CHECKING

import numpy as np
import openvdb

from oco_viz.export.vdb import (
    compute_dissolution_mask,
    compute_temperature_field,
    numpy_to_vdb,
    numpy_to_vec3f_grid,
)

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import AppConfig, GridConfig
    from oco_viz.render.camera_path import CameraPath
    from oco_viz.render.transfer import TransferFunction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# VDB transform helpers
# ---------------------------------------------------------------------------


def _create_vdb_transform(grid_cfg: GridConfig) -> object:
    """Build an OpenVDB linear transform honouring non-uniform voxel sizes.

    If dx == dy == dz the cheaper ``voxelSize`` path is used; otherwise a
    4x4 diagonal matrix encodes the per-axis spacing so that XY are not
    squashed when dz differs.
    """
    dx, dy, dz = float(grid_cfg.dx), float(grid_cfg.dy), float(grid_cfg.dz)
    if dx == dy == dz:
        return openvdb.createLinearTransform(voxelSize=dx)
    mat = [
        [dx, 0, 0, 0],
        [0, dy, 0, 0],
        [0, 0, dz, 0],
        [0, 0, 0, 1],
    ]
    return openvdb.createLinearTransform(matrix=mat)


# ---------------------------------------------------------------------------
# Transfer-function ramp converters
# ---------------------------------------------------------------------------


def _tf_to_color_ramp(tf: TransferFunction) -> list[dict[str, float]]:
    """Convert TF color control points to a sorted list of dicts."""
    return sorted(
        ({"pos": cp.scalar, "r": cp.r, "g": cp.g, "b": cp.b} for cp in tf.color_points),
        key=lambda d: d["pos"],
    )


def _tf_to_opacity_ramp(tf: TransferFunction) -> list[dict[str, float]]:
    """Convert TF opacity control points to a sorted list of dicts."""
    return sorted(
        ({"pos": cp.scalar, "opacity": cp.opacity} for cp in tf.opacity_points),
        key=lambda d: d["pos"],
    )


# ---------------------------------------------------------------------------
# Camera rotation helper
# ---------------------------------------------------------------------------


def _position_to_rotation(
    position: tuple[float, float, float],
    focal_point: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute Euler rotation (rx, ry, rz) in degrees from position looking at focal_point.

    Convention: Z-up, rz always 0 (no roll).
    rx = pitch (negative when looking down), ry = yaw/heading.
    """
    ddx = focal_point[0] - position[0]
    ddy = focal_point[1] - position[1]
    ddz = focal_point[2] - position[2]

    horiz = math.sqrt(ddx * ddx + ddy * ddy)
    if horiz < 1e-12 and abs(ddz) < 1e-12:
        return (0.0, 0.0, 0.0)

    rx = math.degrees(math.atan2(ddz, horiz))
    ry = math.degrees(math.atan2(ddy, ddx))
    return (rx, ry, 0.0)


# ---------------------------------------------------------------------------
# VDB frame / sequence export
# ---------------------------------------------------------------------------


def export_td_vdb_frame(
    concentration: NDArray[np.float32],
    velocity: (tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]] | None),
    output_dir: Path,
    frame: int,
    config: AppConfig,
    *,
    metadata: dict[str, str] | None = None,
) -> Path:
    """Export one VDB frame with density (and optional auxiliary grids).

    Uses ``copyFromArray`` for bulk copy and applies a non-uniform voxel
    transform when dx/dy/dz differ.
    """
    grid_cfg = config.grid
    threshold = 1e-6

    # --- density grid ---
    sparse_data = concentration.copy().astype(np.float32)
    sparse_data[np.abs(sparse_data) < threshold] = 0.0

    grid = openvdb.FloatGrid()
    grid.copyFromArray(sparse_data)
    grid.name = "density"
    grid.transform = _create_vdb_transform(grid_cfg)

    # Attach metadata
    meta: dict[str, str] = {
        "creator": "oco-viz",
        "frame": str(frame),
        "origin_lat": str(config.data_source.domain.origin_lat),
        "origin_lon": str(config.data_source.domain.origin_lon),
        "voxel_size_m": f"{grid_cfg.dx},{grid_cfg.dy},{grid_cfg.dz}",
        "pipeline_stage": "previz",
    }
    if metadata:
        meta.update(metadata)
    for key, value in meta.items():
        grid[key] = value

    grids: list[object] = [grid]

    # --- optional auxiliary grids (require velocity data) ---
    if velocity is not None:
        u, v, w = velocity
        vel_grid = numpy_to_vec3f_grid(u, v, w, grid_cfg, grid_name="vel")
        grids.append(vel_grid)

        temp = compute_temperature_field(concentration, grid_cfg)
        temp_grid = numpy_to_vdb(temp, grid_cfg, grid_name="temperature")
        grids.append(temp_grid)

        diss = compute_dissolution_mask(concentration)
        diss_grid = numpy_to_vdb(diss, grid_cfg, grid_name="dissolution_mask")
        grids.append(diss_grid)

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"plume_{frame:06d}.vdb"
    openvdb.write(str(path), grids=grids)
    logger.info("Wrote TD VDB frame %d: %s", frame, path)
    return path


def export_td_vdb_sequence(
    frames: list[NDArray[np.float32]],
    velocities: (
        list[
            tuple[
                NDArray[np.float32],
                NDArray[np.float32],
                NDArray[np.float32],
            ]
        ]
        | None
    ),
    config: AppConfig,
    output_dir: Path,
) -> list[Path]:
    """Export a numbered sequence of VDB frames."""
    paths: list[Path] = []
    for i, frame_data in enumerate(frames):
        vel = velocities[i] if velocities is not None else None
        path = export_td_vdb_frame(
            frame_data,
            vel,
            output_dir,
            frame=i,
            config=config,
        )
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Camera CHOP export
# ---------------------------------------------------------------------------


def export_td_camera_chop(
    camera_path: CameraPath,
    output_dir: Path,
    n_frames: int,
) -> Path:
    """Write camera data as a tab-separated CHOP file for TouchDesigner.

    Returns path to the written ``.tsv`` file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "camera.tsv"

    lines: list[str] = [
        "# coordinate_system: z_up",
        "# units: meters, degrees",
        "frame\ttx\tty\ttz\trx\try\trz",
    ]

    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)
        state = camera_path.evaluate(t)
        tx, ty, tz = state.position
        rx, ry, rz = _position_to_rotation(state.position, state.focal_point)
        lines.append(f"{i}\t{tx:.6f}\t{ty:.6f}\t{tz:.6f}\t{rx:.6f}\t{ry:.6f}\t{rz:.6f}")

    path.write_text("\n".join(lines) + "\n")
    logger.info("Wrote TD camera CHOP: %s (%d frames)", path, n_frames)
    return path


# ---------------------------------------------------------------------------
# Manifest export
# ---------------------------------------------------------------------------


def export_td_manifest(
    config: AppConfig,
    output_dir: Path,
    frame_count: int,
    *,
    transfer_function: TransferFunction | None = None,
    camera_path: CameraPath | None = None,
) -> Path:
    """Write a JSON manifest describing the TD session."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "td_manifest.json"

    grid_cfg = config.grid
    manifest: dict[str, object] = {
        "frame_count": frame_count,
        "fps": config.output.fps,
        "vdb_pattern": "plume_{frame:06d}.vdb",
        "voxel_dims": [grid_cfg.dx, grid_cfg.dy, grid_cfg.dz],
        "world_scale": [
            grid_cfg.nx * grid_cfg.dx,
            grid_cfg.ny * grid_cfg.dy,
            grid_cfg.nz * grid_cfg.dz,
        ],
        "coordinate_system": "z_up",
        "visual_language": "volumetric_emission",
        "pipeline_stage": "previz",
        "creator": "oco-viz",
        "grid_names": ["density", "vel", "temperature", "dissolution_mask"],
        "origin_lat": config.data_source.domain.origin_lat,
        "origin_lon": config.data_source.domain.origin_lon,
    }

    if transfer_function is not None:
        manifest["color_ramp"] = _tf_to_color_ramp(transfer_function)
        manifest["opacity_ramp"] = _tf_to_opacity_ramp(transfer_function)

    if camera_path is not None:
        keyframes = []
        for i in range(frame_count):
            t = i / max(frame_count - 1, 1)
            state = camera_path.evaluate(t)
            keyframes.append(
                {
                    "frame": i,
                    "position": list(state.position),
                    "focal_point": list(state.focal_point),
                }
            )
        manifest["camera_keyframes"] = keyframes

    path.write_text(json.dumps(manifest, indent=2) + "\n")
    logger.info("Wrote TD manifest: %s", path)
    return path


# ---------------------------------------------------------------------------
# Point cloud export
# ---------------------------------------------------------------------------


def export_point_cloud(
    concentration: NDArray[np.float32],
    grid_cfg: GridConfig,
    output_path: Path,
    threshold: float = 0.01,
) -> Path:
    """Write voxels above *threshold* as a CSV point cloud (x, y, z, density)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    mask = concentration > threshold
    indices = np.argwhere(mask)

    with output_path.open("w") as fh:
        fh.write("x,y,z,density\n")
        for idx in indices:
            iz, iy, ix = int(idx[0]), int(idx[1]), int(idx[2])
            x = ix * grid_cfg.dx
            y = iy * grid_cfg.dy
            z = iz * grid_cfg.dz
            fh.write(
                f"{x},{y},{z},{float(concentration[iz, iy, ix])}\n",
            )

    logger.info(
        "Wrote point cloud: %s (%d points above threshold %.4f)",
        output_path,
        len(indices),
        threshold,
    )
    return output_path
