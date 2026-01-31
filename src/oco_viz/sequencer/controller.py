"""Frame sequencer: Zarr -> render loop with resume support."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from oco_viz.data.zarr_store import read_zarr
from oco_viz.render.camera import OrbitCamera
from oco_viz.render.frame_sidecar import write_sidecar
from oco_viz.render.frame_writer import save_frame_8bit, save_frame_16bit
from oco_viz.render.renderer import VolumeRenderer

if TYPE_CHECKING:
    from oco_viz.config.schema import AppConfig

logger = logging.getLogger(__name__)


def render_sequence(
    config: AppConfig,
    zarr_path: Path,
    *,
    num_frames: int | None = None,
) -> list[Path]:
    """Render all timesteps from a Zarr store to PNG frames.

    Supports resume: skips frames that already exist.
    Uses 16-bit or 8-bit PNG output based on ``config.output.bit_depth``.
    Writes a YAML sidecar file per frame with metadata.
    """
    ds = read_zarr(zarr_path)
    total_timesteps = ds.sizes["time"]
    n = min(num_frames, total_timesteps) if num_frames else total_timesteps

    frames_dir = Path(config.output.frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    camera_rig = OrbitCamera(
        focal_point=config.camera.focal_point,
        distance=config.camera.distance,
        elevation=config.camera.elevation,
        azimuth_start=config.camera.azimuth_start,
        azimuth_end=config.camera.azimuth_end,
    )

    renderer = VolumeRenderer(config)
    renderer.configure()

    use_16bit = config.output.bit_depth == 16
    save_frame = save_frame_16bit if use_16bit else save_frame_8bit

    output_paths: list[Path] = []

    for i in range(n):
        frame_path = frames_dir / f"frame_{i:06d}.png"
        output_paths.append(frame_path)

        if frame_path.exists():
            logger.info("Skipping existing frame %s", frame_path)
            continue

        t = i / max(n - 1, 1)
        camera_state = camera_rig.evaluate(t)

        concentration = ds["concentration"].isel(time=i).values.astype(np.float32)
        rgb_pp = renderer.render_frame_postprocessed(concentration, camera_state)

        save_frame(rgb_pp, frame_path)

        # Write sidecar YAML with concentration statistics
        sidecar_path = frame_path.with_suffix(".yaml")
        write_sidecar(
            sidecar_path,
            frame_index=i,
            timestamp=float(i) / max(n - 1, 1),
            camera_state=camera_state,
            concentration_stats={
                "min": float(concentration.min()),
                "max": float(concentration.max()),
                "mean": float(concentration.mean()),
            },
        )

        logger.info("Rendered frame %d/%d -> %s", i + 1, n, frame_path)

    renderer.finalize()
    return output_paths
