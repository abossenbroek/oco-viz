"""Shared utilities for gallery rendering scripts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import numpy as np
import structlog
import yaml
from PIL import Image

log = structlog.get_logger()


def save_rgb(rgb: np.ndarray, out_path: Path) -> None:
    """Save a float32 [0,1] RGB array as a PNG file.

    Creates parent directories if they do not exist.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rgb_uint8 = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    img.save(str(out_path))
    log.info("saved", path=str(out_path))


def configure_gallery_logging() -> None:
    """Set up structlog with YAML renderer for gallery scripts."""

    def yaml_renderer(
        _logger: Any,
        _name: str,
        event_dict: dict[str, Any],
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


def build_standard_camera(config: object) -> object:
    """Build the standard gallery camera from config.grid geometry.

    Returns a ``CameraState`` suitable for most gallery renders.
    """
    from oco_viz.render.camera import FixedCamera  # noqa: PLC0415

    grid = config.grid  # type: ignore[attr-defined]
    cx = grid.nx * grid.dx / 2.0
    cy = grid.ny * grid.dy / 2.0
    cz = grid.nz * grid.dz / 3.0
    extent = max(grid.nx * grid.dx, grid.ny * grid.dy)
    return FixedCamera(
        position=(cx + extent * 1.2, cy - extent * 0.8, cz + extent * 0.3),
        focal_point=(cx, cy, cz),
    ).evaluate(0.0)
