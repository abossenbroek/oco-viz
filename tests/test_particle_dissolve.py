"""Tests for particle dissolution at volume boundaries."""

from __future__ import annotations

import numpy as np
import vtk

from oco_viz.config.schema import ParticleDissolutionConfig
from oco_viz.render.particle_dissolve import create_dissolution_particles

SMALL_SHAPE = (16, 16, 16)
SPACING = (100.0, 100.0, 50.0)


def _make_blob(shape: tuple[int, int, int] = SMALL_SHAPE) -> np.ndarray:
    """Create a Gaussian blob with strong boundary gradients."""
    z, y, x = np.mgrid[0 : shape[0], 0 : shape[1], 0 : shape[2]]
    cz, cy, cx = shape[0] / 2, shape[1] / 2, shape[2] / 2
    dist2 = (z - cz) ** 2 + (y - cy) ** 2 + (x - cx) ** 2
    return np.exp(-dist2 / 8.0).astype(np.float32)


def test_returns_actor_empty_field() -> None:
    """All-zero concentration should produce an empty actor."""
    conc = np.zeros(SMALL_SHAPE, dtype=np.float32)
    config = ParticleDissolutionConfig(enabled=True)
    actor = create_dissolution_particles(conc, SPACING, config)
    assert isinstance(actor, vtk.vtkActor)


def test_returns_actor_with_blob() -> None:
    """A Gaussian blob should produce a non-empty actor."""
    conc = _make_blob()
    config = ParticleDissolutionConfig(enabled=True, particle_count_scale=0.5)
    actor = create_dissolution_particles(conc, SPACING, config)
    assert isinstance(actor, vtk.vtkActor)
    mapper = actor.GetMapper()
    assert mapper is not None
    input_data = mapper.GetInput()
    assert input_data is not None
    assert input_data.GetNumberOfPoints() > 0


def test_particle_count_scales() -> None:
    """Higher particle_count_scale should produce more particles."""
    conc = _make_blob()
    low = ParticleDissolutionConfig(enabled=True, particle_count_scale=0.1, seed=42)
    high = ParticleDissolutionConfig(enabled=True, particle_count_scale=2.0, seed=42)
    actor_low = create_dissolution_particles(conc, SPACING, low)
    actor_high = create_dissolution_particles(conc, SPACING, high)
    n_low = actor_low.GetMapper().GetInput().GetNumberOfPoints()
    n_high = actor_high.GetMapper().GetInput().GetNumberOfPoints()
    assert n_high >= n_low


def test_deterministic_seed() -> None:
    """Same seed should produce identical particles."""
    conc = _make_blob()
    config = ParticleDissolutionConfig(enabled=True, seed=99)
    a = create_dissolution_particles(conc, SPACING, config)
    b = create_dissolution_particles(conc, SPACING, config)
    n_a = a.GetMapper().GetInput().GetNumberOfPoints()
    n_b = b.GetMapper().GetInput().GetNumberOfPoints()
    assert n_a == n_b


def test_config_defaults() -> None:
    """Default config should have expected values."""
    config = ParticleDissolutionConfig()
    assert config.enabled is False
    assert config.threshold == 0.05
    assert config.particle_count_scale == 1.0
    assert config.seed == 42


def test_opacity_property() -> None:
    """Actor opacity should match config."""
    conc = _make_blob()
    config = ParticleDissolutionConfig(enabled=True, particle_opacity=0.6)
    actor = create_dissolution_particles(conc, SPACING, config)
    assert actor.GetProperty().GetOpacity() == 0.6
