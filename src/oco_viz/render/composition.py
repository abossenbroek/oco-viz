"""Automatic camera composition from plume geometry."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import CompositionConfig


def plume_bounding_box(
    concentration: NDArray[np.floating],
    threshold_fraction: float,
    spacing: tuple[float, float, float],
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    """Compute centroid, bbox_min, bbox_max from concentration field.

    Input array is (z, y, x). Output coordinates are (x, y, z) for camera space.
    Falls back to volume center when field is all-zero.
    """
    # spacing is (dz, dy, dx) matching (z, y, x) array axes
    dz, dy, dx = spacing
    nz, ny, nx = concentration.shape

    max_val = float(concentration.max())
    threshold = max_val * threshold_fraction

    if max_val <= 0:
        # Fallback: volume center
        cx = (nx - 1) * dx / 2.0
        cy = (ny - 1) * dy / 2.0
        cz = (nz - 1) * dz / 2.0
        bmin = (0.0, 0.0, 0.0)
        bmax = ((nx - 1) * dx, (ny - 1) * dy, (nz - 1) * dz)
        return (cx, cy, cz), bmin, bmax

    mask = concentration > threshold
    coords = np.argwhere(mask)  # shape (N, 3) with (z, y, x) indices

    # Convert to physical coords: (x, y, z)
    x_phys = coords[:, 2].astype(np.float64) * dx
    y_phys = coords[:, 1].astype(np.float64) * dy
    z_phys = coords[:, 0].astype(np.float64) * dz

    weights = concentration[mask].astype(np.float64)
    total = weights.sum()

    cx = float(np.sum(x_phys * weights) / total)
    cy = float(np.sum(y_phys * weights) / total)
    cz = float(np.sum(z_phys * weights) / total)

    bmin = (float(x_phys.min()), float(y_phys.min()), float(z_phys.min()))
    bmax = (float(x_phys.max()), float(y_phys.max()), float(z_phys.max()))

    return (cx, cy, cz), bmin, bmax


def compute_camera_distance(
    plume_bounds: tuple[tuple[float, float, float], tuple[float, float, float]],
    frame_fill_target: float,
    fov_degrees: float,
) -> float:
    """Compute camera distance to frame the plume at desired fill fraction."""
    bmin, bmax = plume_bounds
    extents = [mx - mn for mx, mn in zip(bmax, bmin, strict=True)]
    max_extent = max(extents)
    half_fov = math.radians(fov_degrees / 2.0)
    tan_half = math.tan(half_fov)
    if tan_half == 0 or frame_fill_target == 0:
        return 1.0
    distance = (max_extent / 2.0 / frame_fill_target) / tan_half
    return max(1.0, distance)


def compute_focal_point(
    centroid: tuple[float, float, float],
    asymmetric_offset: tuple[float, float],
) -> tuple[float, float, float]:
    """Offset centroid for asymmetric framing.

    offset[0] shifts x, offset[1] shifts z.
    """
    return (
        centroid[0] + asymmetric_offset[0],
        centroid[1],
        centroid[2] + asymmetric_offset[1],
    )


def compute_elevation_bias(
    base_elevation: float,
    *,
    vertical_emphasis: bool,
    bias_degrees: float = 10.0,
) -> float:
    """Add elevation bias when vertical emphasis is enabled. Clamp to [0, 89]."""
    elevation = base_elevation
    if vertical_emphasis:
        elevation += bias_degrees
    return max(0.0, min(89.0, elevation))


def compose_camera_from_plume(
    concentration: NDArray[np.floating],
    config: CompositionConfig,
    grid_spacing: tuple[float, float, float],
    base_elevation: float = 30.0,
    fov_degrees: float = 30.0,
) -> tuple[tuple[float, float, float], float, float]:
    """Top-level composition: returns (focal_point, distance, elevation)."""
    centroid, bmin, bmax = plume_bounding_box(
        concentration,
        config.threshold_fraction,
        grid_spacing,
    )
    fill_target = (config.frame_fill[0] + config.frame_fill[1]) / 2.0
    distance = compute_camera_distance((bmin, bmax), fill_target, fov_degrees)
    focal = compute_focal_point(centroid, config.asymmetric_offset)
    elevation = compute_elevation_bias(
        base_elevation,
        vertical_emphasis=config.vertical_emphasis,
    )
    return focal, distance, elevation
