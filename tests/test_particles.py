"""Tests for ash particle overlay."""

from __future__ import annotations

import numpy as np
import vtk

from oco_viz.render.particles import create_ash_particles

SMALL_SHAPE = (16, 16, 16)
SPACING = (100.0, 100.0, 50.0)


def test_create_ash_particles_returns_actor() -> None:
    """Function should return a vtkActor regardless of input."""
    conc = np.zeros(SMALL_SHAPE, dtype=np.float32)
    actor = create_ash_particles(conc, SPACING)
    assert isinstance(actor, vtk.vtkActor)


def test_create_ash_particles_empty_field() -> None:
    """All-zero concentration should produce an empty actor."""
    conc = np.zeros(SMALL_SHAPE, dtype=np.float32)
    actor = create_ash_particles(conc, SPACING)
    assert isinstance(actor, vtk.vtkActor)
    # Empty actor should have a mapper with no input points
    mapper = actor.GetMapper()
    assert mapper is not None


def test_create_ash_particles_with_blob() -> None:
    """A Gaussian blob should produce a non-empty actor with particles."""
    conc = np.zeros(SMALL_SHAPE, dtype=np.float32)
    # Create a blob in the center
    z, y, x = np.mgrid[0:SMALL_SHAPE[0], 0:SMALL_SHAPE[1], 0:SMALL_SHAPE[2]]
    cz, cy, cx = SMALL_SHAPE[0] / 2, SMALL_SHAPE[1] / 2, SMALL_SHAPE[2] / 2
    dist2 = (z - cz) ** 2 + (y - cy) ** 2 + (x - cx) ** 2
    conc = np.exp(-dist2 / 8.0).astype(np.float32)

    actor = create_ash_particles(conc, SPACING, threshold=0.05, num_points=100)
    assert isinstance(actor, vtk.vtkActor)
    # The mapper should have input data with points
    mapper = actor.GetMapper()
    assert mapper is not None
    input_data = mapper.GetInput()
    assert input_data is not None
    assert input_data.GetNumberOfPoints() > 0
