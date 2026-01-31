"""YAML sidecar metadata writer for rendered frames."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from oco_viz.render.camera import CameraState


def write_sidecar(
    path: Path,
    *,
    frame_index: int,
    timestamp: float,
    camera_state: CameraState,
    concentration_stats: dict[str, float],
) -> Path:
    """Write a YAML sidecar file with per-frame metadata.

    Parameters
    ----------
    path:
        Output path for the YAML file (e.g. ``frame_000042.yaml``).
    frame_index:
        Zero-based frame index.
    timestamp:
        Simulation timestamp in seconds.
    camera_state:
        Camera position and orientation for this frame.
    concentration_stats:
        Dictionary with ``min``, ``max``, ``mean`` concentration values.

    Returns
    -------
    Path
        The written sidecar file path.

    """
    data: dict[str, Any] = {
        "frame_index": frame_index,
        "timestamp": timestamp,
        "camera": {
            "position": list(camera_state.position),
            "focal_point": list(camera_state.focal_point),
            "view_up": list(camera_state.view_up),
        },
        "concentration": {
            "min": concentration_stats["min"],
            "max": concentration_stats["max"],
            "mean": concentration_stats["mean"],
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    return path
