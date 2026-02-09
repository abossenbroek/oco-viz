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
    "ambientColor = vec3(0.95, 0.88, 0.75);\n"
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


def _empty_dissolution_actor() -> vtk.vtkActor:
    """Return an actor with no geometry (fallback when no boundary found)."""
    polydata = vtk.vtkPolyData()
    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor
