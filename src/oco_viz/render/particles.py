"""Ash particle overlay for exhibition-tier edge dissolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _conc_to_image(
    conc: NDArray[np.float32],
    spacing: tuple[float, float, float],
) -> vtk.vtkImageData:
    """Build vtkImageData from a 3D concentration array."""
    image = vtk.vtkImageData()
    nz, ny, nx = conc.shape
    image.SetDimensions(nx, ny, nz)
    image.SetSpacing(spacing[0], spacing[1], spacing[2])
    image.SetOrigin(0.0, 0.0, 0.0)

    flat = np.ascontiguousarray(conc.ravel(order="C"))
    vtk_arr = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_FLOAT)
    vtk_arr.SetName("concentration")
    image.GetPointData().SetScalars(vtk_arr)
    return image


def _extract_boundary_surface(
    image: vtk.vtkImageData,
    threshold: float,
) -> vtk.vtkPolyData:
    """Extract an isosurface at the given threshold."""
    contour = vtk.vtkFlyingEdges3D()
    contour.SetInputData(image)
    contour.SetValue(0, threshold)
    contour.Update()
    return contour.GetOutput()


def _sample_and_scatter(
    surface: vtk.vtkPolyData,
    num_points: int,
    scatter_distance: float,
    mean_spacing: float,
    seed: int,
) -> vtk.vtkPolyData:
    """Sample points from surface, jitter outward, return polydata with scalars."""
    rng = np.random.default_rng(seed)
    n_surface_pts = surface.GetNumberOfPoints()
    n_sample = min(num_points, n_surface_pts)
    indices = rng.choice(n_surface_pts, size=n_sample, replace=False)

    # Extract point coordinates
    pts_array = np.zeros((n_sample, 3), dtype=np.float64)
    for i, idx in enumerate(indices):
        surface.GetPoint(int(idx), pts_array[i])

    # Compute normals for scatter direction
    normals_array = _compute_normals(surface, indices, n_sample, rng)

    # Scatter points outward along normals with random jitter
    jitter_dist = rng.uniform(0.5, scatter_distance, size=(n_sample, 1))
    jitter_lateral = rng.standard_normal((n_sample, 3)) * scatter_distance * 0.3
    pts_scattered = (
        pts_array + normals_array * jitter_dist * mean_spacing + jitter_lateral * mean_spacing
    )

    return _build_polydata(pts_scattered, n_sample, rng)


def _compute_normals(
    surface: vtk.vtkPolyData,
    indices: NDArray[np.intp],
    n_sample: int,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Compute outward normals at sampled surface points."""
    normals_filter = vtk.vtkPolyDataNormals()
    normals_filter.SetInputData(surface)
    normals_filter.ComputePointNormalsOn()
    normals_filter.Update()

    normals_data = normals_filter.GetOutput().GetPointData().GetNormals()
    normals_array = np.zeros((n_sample, 3), dtype=np.float64)

    if normals_data is not None:
        for i, idx in enumerate(indices):
            normals_data.GetTuple(int(idx), normals_array[i])
    else:
        normals_array = rng.standard_normal((n_sample, 3))
        norms = np.linalg.norm(normals_array, axis=1, keepdims=True)
        norms[norms < 1e-8] = 1.0
        normals_array /= norms

    return normals_array


def _build_polydata(
    pts: NDArray[np.float64],
    n_sample: int,
    rng: np.random.Generator,
) -> vtk.vtkPolyData:
    """Build VTK polydata with vertex cells and opacity scalars."""
    vtk_points = vtk.vtkPoints()
    for pt in pts:
        vtk_points.InsertNextPoint(pt[0], pt[1], pt[2])

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(vtk_points)

    verts = vtk.vtkCellArray()
    for i in range(n_sample):
        verts.InsertNextCell(1)
        verts.InsertCellPoint(i)
    polydata.SetVerts(verts)

    scalars = rng.uniform(0.3, 1.0, size=n_sample).astype(np.float32)
    vtk_scalars = numpy_to_vtk(np.ascontiguousarray(scalars), deep=True, array_type=vtk.VTK_FLOAT)
    vtk_scalars.SetName("opacity")
    polydata.GetPointData().SetScalars(vtk_scalars)

    return polydata


_SOOT_SHADER = (
    "//VTK::Color::Impl\n"
    "float dist2 = dot(offsetVCVSOutput.xy, offsetVCVSOutput.xy);\n"
    "if (dist2 > 1.0) { discard; }\n"
    "float alpha = exp(-dist2 * 3.0);\n"
    "ambientColor = vec3(0.42, 0.42, 0.42);\n"
    "diffuseColor = vec3(0.0);\n"
    "opacity = opacity * alpha;\n"
)


def create_ash_particles(
    conc: NDArray[np.float32],
    spacing: tuple[float, float, float],
    *,
    threshold: float = 0.05,
    num_points: int = 3000,
    scatter_distance: float = 2.0,
    particle_scale: float = 150.0,
    particle_opacity: float = 0.4,
    seed: int = 42,
) -> vtk.vtkActor:
    """Create ash particle actor from volume boundary.

    Extracts an isosurface at the given threshold, samples points on it,
    jitters them outward, and returns a vtkActor using vtkPointGaussianMapper.

    Parameters
    ----------
    conc
        3D concentration field (z, y, x) in [0, 1].
    spacing
        Physical spacing (dx, dy, dz).
    threshold
        Isosurface value for boundary extraction.
    num_points
        Maximum number of ash particles.
    scatter_distance
        How far particles scatter outward (in grid cells).
    particle_scale
        Size of each particle gaussian.
    particle_opacity
        Base opacity of particles.
    seed
        Random seed for reproducibility.

    """
    image = _conc_to_image(conc, spacing)
    surface = _extract_boundary_surface(image, threshold)

    if surface.GetNumberOfPoints() == 0:
        return _empty_particle_actor()

    mean_spacing = float(np.mean(spacing))
    polydata = _sample_and_scatter(surface, num_points, scatter_distance, mean_spacing, seed)

    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    mapper.SetScaleFactor(particle_scale)
    mapper.EmissiveOff()
    mapper.SetSplatShaderCode(_SOOT_SHADER)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(particle_opacity)
    return actor


def _empty_particle_actor() -> vtk.vtkActor:
    """Return an actor with no geometry (fallback when no boundary found)."""
    polydata = vtk.vtkPolyData()
    mapper = vtk.vtkPointGaussianMapper()
    mapper.SetInputData(polydata)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor
