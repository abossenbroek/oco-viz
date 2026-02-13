"""Particle dissolution at volume boundaries using gradient-based boundary detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from oco_viz.config.schema import ParticleDissolutionConfig


_DISSOLUTION_SHADER = (
    "//VTK::Color::Impl\n"
    "float dist2 = dot(offsetVCVSOutput.xy, offsetVCVSOutput.xy);\n"
    "if (dist2 > 1.0) { discard; }\n"
    "float alpha = exp(-dist2 * 0.5);\n"
    "ambientColor = vec3(0.75, 0.75, 0.75);\n"
    "diffuseColor = vec3(0.0);\n"
    "opacity = opacity * alpha;\n"
)

_CLUMP_SHADER = (
    "//VTK::Color::Impl\n"
    "float dist2 = dot(offsetVCVSOutput.xy, offsetVCVSOutput.xy);\n"
    "if (dist2 > 1.0) { discard; }\n"
    "float alpha = exp(-dist2 * 1.0);\n"
    "ambientColor = vec3(0.65, 0.65, 0.65);\n"
    "diffuseColor = vec3(0.0);\n"
    "opacity = opacity * alpha;\n"
)

_FILAMENT_SHADER = (
    "//VTK::Color::Impl\n"
    "float dist2 = dot(offsetVCVSOutput.xy, offsetVCVSOutput.xy);\n"
    "if (dist2 > 1.0) { discard; }\n"
    "float alpha = exp(-dist2 * 1.5);\n"
    "ambientColor = vec3(0.55, 0.55, 0.55);\n"
    "diffuseColor = vec3(0.0);\n"
    "opacity = opacity * alpha;\n"
)

_DUST_SHADER = (
    "//VTK::Color::Impl\n"
    "float dist2 = dot(offsetVCVSOutput.xy, offsetVCVSOutput.xy);\n"
    "if (dist2 > 1.0) { discard; }\n"
    "float alpha = exp(-dist2 * 3.0);\n"
    "ambientColor = vec3(0.45, 0.45, 0.45);\n"
    "diffuseColor = vec3(0.0);\n"
    "opacity = opacity * alpha;\n"
)


def _gradient_magnitude(conc: NDArray[np.float32]) -> NDArray[np.float32]:
    """Compute gradient magnitude of a 3D concentration field."""
    gz, gy, gx = np.gradient(conc.astype(np.float64))
    result: NDArray[np.float32] = np.sqrt(gz**2 + gy**2 + gx**2).astype(np.float32)
    return result


def _sample_boundary_points(
    conc: NDArray[np.float32],
    grad_mag: NDArray[np.float32],
    threshold: float,
    num_points: int,
    spacing: tuple[float, float, float],
    seed: int,
) -> tuple[NDArray[np.float64], NDArray[np.float32]]:
    """Sample points from boundary region identified by gradient thresholding.

    Returns (positions, opacity_scalars) arrays.
    """
    rng = np.random.default_rng(seed)

    # Boundary mask: high gradient AND above concentration threshold
    grad_norm = grad_mag / max(float(grad_mag.max()), 1e-8)
    boundary_mask = (grad_norm > 0.05) & (conc > threshold) & (conc < 0.7)

    candidates = np.argwhere(boundary_mask)
    if len(candidates) == 0:
        return np.empty((0, 3), dtype=np.float64), np.empty(0, dtype=np.float32)

    n_sample = min(num_points, len(candidates))
    indices = rng.choice(len(candidates), size=n_sample, replace=False)
    selected = candidates[indices]

    # Convert grid indices to world coordinates
    positions = np.zeros((n_sample, 3), dtype=np.float64)
    positions[:, 0] = selected[:, 2] * spacing[0]  # x
    positions[:, 1] = selected[:, 1] * spacing[1]  # y
    positions[:, 2] = selected[:, 0] * spacing[2]  # z

    # Jitter positions slightly to avoid grid artifacts
    jitter = rng.standard_normal((n_sample, 3)) * np.array(spacing) * 0.3
    positions += jitter

    # Opacity proportional to gradient strength (stronger edges = more visible particles)
    opacities = grad_norm[selected[:, 0], selected[:, 1], selected[:, 2]]
    opacities = np.clip(opacities, 0.2, 1.0).astype(np.float32)

    return positions, opacities


def _apply_drift_gravity(
    positions: NDArray[np.float64],
    drift_speed: float,
    gravity: float,
    spacing: tuple[float, float, float],
    seed: int,
) -> NDArray[np.float64]:
    """Apply random drift and downward gravity displacement to particles."""
    rng = np.random.default_rng(seed + 7)
    n = len(positions)
    if n == 0:
        return positions

    mean_spacing = float(np.mean(spacing))
    result = positions.copy()

    # Random horizontal drift
    drift = rng.standard_normal((n, 3)) * drift_speed * mean_spacing
    drift[:, 2] = 0.0  # no z drift from random component
    result += drift

    # Gravity pulls particles downward (negative z)
    result[:, 2] -= gravity * mean_spacing

    return result


def _build_particle_polydata(
    positions: NDArray[np.float64],
    opacities: NDArray[np.float32],
) -> vtk.vtkPolyData:
    """Build VTK polydata with vertex cells and opacity scalars."""
    n = len(positions)

    vtk_points = vtk.vtkPoints()
    for pt in positions:
        vtk_points.InsertNextPoint(pt[0], pt[1], pt[2])

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)

    verts = vtk.vtkCellArray()
    for i in range(n):
        verts.InsertNextCell(1)
        verts.InsertCellPoint(i)
    polydata.SetVerts(verts)

    vtk_scalars = numpy_to_vtk(
        np.ascontiguousarray(opacities), deep=True, array_type=vtk.VTK_FLOAT
    )
    vtk_scalars.SetName("opacity")
    polydata.GetPointData().SetScalars(vtk_scalars)

    return polydata


def create_dissolution_particles(
    conc: NDArray[np.float32],
    spacing: tuple[float, float, float],
    config: ParticleDissolutionConfig,
) -> vtk.vtkActor:
    """Create dissolution particle actor from volume boundary gradients.

    Uses gradient magnitude to detect volume boundaries, samples points along
    high-gradient regions, applies drift/gravity displacement, and renders via
    vtkPointGaussianMapper with a custom dissolution shader.

    Parameters
    ----------
    conc
        3D concentration field (z, y, x) in [0, 1].
    spacing
        Physical spacing (dx, dy, dz).
    config
        Particle dissolution configuration.

    Returns
    -------
    vtk.vtkActor
        Actor with dissolution particles, or an empty actor if no boundary found.

    """
    grad_mag = _gradient_magnitude(conc)
    base_points = int(5000 * config.particle_count_scale)

    positions, opacities = _sample_boundary_points(
        conc,
        grad_mag,
        threshold=config.threshold,
        num_points=base_points,
        spacing=spacing,
        seed=config.seed,
    )

    if len(positions) == 0:
        return _empty_dissolution_actor()

    positions = _apply_drift_gravity(
        positions,
        drift_speed=config.drift_speed,
        gravity=config.gravity,
        spacing=spacing,
        seed=config.seed,
    )

    polydata = _build_particle_polydata(positions, opacities)

    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    mapper.SetScaleFactor(config.particle_scale)
    mapper.EmissiveOn()
    mapper.SetSplatShaderCode(_DISSOLUTION_SHADER)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(config.particle_opacity)
    return actor


def _clamp_to_bbox(
    positions: NDArray[np.float64],
    bbox: tuple[float, float, float, float, float, float],
) -> NDArray[np.bool_]:
    """Return boolean mask of positions within bbox + 10% margin."""
    x_min, x_max, y_min, y_max, z_min, z_max = bbox
    margin_x = (x_max - x_min) * 0.1
    margin_y = (y_max - y_min) * 0.1
    margin_z = (z_max - z_min) * 0.1
    keep: NDArray[np.bool_] = (
        (positions[:, 0] >= x_min - margin_x)
        & (positions[:, 0] <= x_max + margin_x)
        & (positions[:, 1] >= y_min - margin_y)
        & (positions[:, 1] <= y_max + margin_y)
        & (positions[:, 2] >= z_min - margin_z)
        & (positions[:, 2] <= z_max + margin_z)
    )
    return keep


def _compute_plume_bbox(
    conc: NDArray[np.float32],
    spacing: tuple[float, float, float],
) -> tuple[float, float, float, float, float, float] | None:
    """Compute world-space bounding box of lit voxels (conc > 0.01)."""
    coords = np.argwhere(conc > 0.01)
    if len(coords) == 0:
        return None
    z_min_i, y_min_i, x_min_i = coords.min(axis=0)
    z_max_i, y_max_i, x_max_i = coords.max(axis=0)
    return (
        float(x_min_i * spacing[0]),
        float(x_max_i * spacing[0]),
        float(y_min_i * spacing[1]),
        float(y_max_i * spacing[1]),
        float(z_min_i * spacing[2]),
        float(z_max_i * spacing[2]),
    )


def _build_layer_actor(
    conc: NDArray[np.float32],
    grad_mag: NDArray[np.float32],
    spacing: tuple[float, float, float],
    bbox: tuple[float, float, float, float, float, float],
    config: ParticleDissolutionConfig,
    layer_index: int,
    conc_lo: float,
    conc_hi: float,
    grad_thresh: float,
    scale: float,
    count_base: int,
    opacity: float,
    shader: str,
) -> vtk.vtkActor:
    """Build a single particle layer actor for a concentration band."""
    layer_mask = (conc >= conc_lo) & (conc <= conc_hi)
    if grad_thresh > 0:
        grad_norm = grad_mag / max(float(grad_mag.max()), 1e-8)
        layer_mask &= grad_norm > grad_thresh

    candidates = np.argwhere(layer_mask)
    if len(candidates) == 0:
        return _empty_dissolution_actor()

    rng = np.random.default_rng(config.seed + layer_index * 100)
    n_sample = min(int(count_base * config.particle_count_scale), len(candidates))
    indices = rng.choice(len(candidates), size=n_sample, replace=False)
    selected = candidates[indices]

    # Convert to world coordinates with jitter
    positions = np.zeros((n_sample, 3), dtype=np.float64)
    positions[:, 0] = selected[:, 2] * spacing[0]
    positions[:, 1] = selected[:, 1] * spacing[1]
    positions[:, 2] = selected[:, 0] * spacing[2]
    positions += rng.standard_normal((n_sample, 3)) * np.array(spacing) * 0.3

    # Opacities from gradient strength
    grad_norm_full = grad_mag / max(float(grad_mag.max()), 1e-8)
    opacities = grad_norm_full[selected[:, 0], selected[:, 1], selected[:, 2]]
    opacities = np.clip(opacities, 0.2, 1.0).astype(np.float32)

    # Apply drift/gravity and clamp to bbox
    positions = _apply_drift_gravity(
        positions,
        drift_speed=config.drift_speed,
        gravity=config.gravity,
        spacing=spacing,
        seed=config.seed + layer_index * 100,
    )
    keep = _clamp_to_bbox(positions, bbox)
    positions = positions[keep]
    opacities = opacities[: len(positions)]

    if len(positions) == 0:
        return _empty_dissolution_actor()

    polydata = _build_particle_polydata(positions, opacities)
    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    mapper.SetScaleFactor(scale)
    mapper.EmissiveOn()
    mapper.SetSplatShaderCode(shader)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(opacity)
    return actor


def create_multilayer_dissolution_particles(
    conc: NDArray[np.float32],
    spacing: tuple[float, float, float],
    config: ParticleDissolutionConfig,
) -> list[vtk.vtkActor]:
    """Create three-layer dissolution particles for exhibition-tier rendering.

    Returns actors for clump, filament, and dust layers with different
    scales, opacities, and shader programs.

    Parameters
    ----------
    conc
        3D concentration field (z, y, x) in [0, 1].
    spacing
        Physical spacing (dx, dy, dz).
    config
        Particle dissolution configuration.

    Returns
    -------
    list[vtk.vtkActor]
        List of actors (clump, filament, dust), or empty list if no boundary found.

    """
    grad_mag = _gradient_magnitude(conc)
    bbox = _compute_plume_bbox(conc, spacing)
    if bbox is None:
        return [_empty_dissolution_actor()]

    # Layer definitions: (conc_lo, conc_hi, grad_thresh, scale, count, opacity, shader)
    layers = [
        (0.15, 0.40, 0.03, 350.0, 5000, 0.7, _CLUMP_SHADER),
        (0.05, 0.15, 0.02, 150.0, 15000, 0.5, _FILAMENT_SHADER),
        (0.01, 0.05, 0.0, 50.0, 25000, 0.3, _DUST_SHADER),
    ]

    return [
        _build_layer_actor(
            conc,
            grad_mag,
            spacing,
            bbox,
            config,
            i,
            conc_lo,
            conc_hi,
            grad_thresh,
            scale,
            count_base,
            opacity,
            shader,
        )
        for i, (conc_lo, conc_hi, grad_thresh, scale, count_base, opacity, shader) in enumerate(
            layers,
        )
    ]


def _empty_dissolution_actor() -> vtk.vtkActor:
    """Return an actor with no geometry (fallback when no boundary found)."""
    polydata = vtk.vtkPolyData()
    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor
