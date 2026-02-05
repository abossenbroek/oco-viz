"""Frame sequencer: Zarr -> render loop with resume support."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from oco_viz.data.zarr_store import read_zarr
from oco_viz.render.annotations import apply_annotations
from oco_viz.render.camera import OrbitCamera
from oco_viz.render.frame_sidecar import write_sidecar
from oco_viz.render.frame_writer import save_frame_8bit, save_frame_16bit
from oco_viz.render.overlay import create_observation_overlay, has_observations
from oco_viz.render.renderer import VolumeRenderer

if TYPE_CHECKING:
    import xarray as xr

    from oco_viz.config.schema import AppConfig

logger = logging.getLogger(__name__)


def _interpolate_concentration(
    ds: xr.Dataset,
    frame_idx: int,
    num_frames: int,
) -> np.ndarray[Any, np.dtype[np.float32]]:
    """Interpolate concentration between dataset timesteps for smooth animation.

    When the dataset has more or fewer timesteps than requested frames,
    linearly maps frame indices to dataset time and interpolates between
    adjacent timesteps.

    Parameters
    ----------
    ds
        Dataset with ``concentration`` variable, dims ``(time, z, y, x)``.
    frame_idx
        Current frame index (0-based).
    num_frames
        Total number of output frames.

    Returns
    -------
    np.ndarray
        Interpolated concentration field of shape ``(z, y, x)`` as float32.
    """
    total_timesteps = ds.sizes["time"]

    # Map frame index to continuous time coordinate
    t_frac = frame_idx * (total_timesteps - 1) / max(num_frames - 1, 1)
    t_low = int(t_frac)
    t_high = min(t_low + 1, total_timesteps - 1)
    frac = t_frac - t_low

    conc_low = ds["concentration"].isel(time=t_low).values.astype(np.float32)

    if t_low == t_high or frac < 1e-8:
        return conc_low

    conc_high = ds["concentration"].isel(time=t_high).values.astype(np.float32)
    return ((1.0 - frac) * conc_low + frac * conc_high).astype(np.float32)


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

    Temporal interpolation: when the dataset has more or fewer timesteps than
    the requested frame count, smoothly interpolates concentration between
    adjacent timesteps (avoids slide-show jumps at low temporal resolution).

    Overlay: if the dataset contains ``xco2_observed`` and overlay is enabled,
    adds observation point markers to the VTK renderer.

    Annotations: if any annotation elements are enabled, applies text overlays
    (timestamp, facility, credits, scale bar) after post-processing.
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

    # Overlay: add observation markers if present and enabled
    overlay_active = config.overlay.enabled and has_observations(ds)
    overlay_actor = None
    if overlay_active:
        overlay_actor = create_observation_overlay(ds, config.grid, config.overlay)
        renderer.add_actor(overlay_actor)
        logger.info("Added observation overlay with %d points", ds.sizes.get("obs", 0))

    use_16bit = config.output.bit_depth == 16
    save_frame = save_frame_16bit if use_16bit else save_frame_8bit

    # Check if any annotation is enabled
    annotations_enabled = any(
        [
            config.annotations.show_timestamp,
            config.annotations.show_facility,
            config.annotations.show_credits,
            config.annotations.show_scale_bar,
        ]
    )

    output_paths: list[Path] = []

    for i in range(n):
        frame_path = frames_dir / f"frame_{i:06d}.png"
        output_paths.append(frame_path)

        if frame_path.exists():
            logger.info("Skipping existing frame %s", frame_path)
            continue

        t = i / max(n - 1, 1)
        camera_state = camera_rig.evaluate(t)

        # Temporal interpolation between dataset timesteps
        concentration = _interpolate_concentration(ds, i, n)

        rgb_pp = renderer.render_frame_postprocessed(concentration, camera_state)

        # Annotations: apply text overlays after post-processing
        if annotations_enabled:
            frame_meta: dict[str, Any] = {
                "timestamp": str(float(i) / max(n - 1, 1)),
                "frame_index": i,
                "total_frames": n,
                "grid_dx_m": config.grid.dx,
            }
            rgb_pp = apply_annotations(rgb_pp, config.annotations, frame_meta)

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

    # Clean up overlay actor
    if overlay_actor is not None:
        renderer.remove_actor(overlay_actor)

    renderer.finalize()
    return output_paths
