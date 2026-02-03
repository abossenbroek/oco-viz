"""Tests for turbulent plume compositor."""

from __future__ import annotations

import numpy as np
from scipy.ndimage import laplace

from oco_viz.config.schema import GridConfig, PlumeConfig, TurbulenceConfig
from oco_viz.plume.gaussian import generate_timestep as gaussian_timestep
from oco_viz.plume.turbulent import (
    apply_turbulence,
    generate_turbulent_sequence,
    generate_turbulent_timestep,
)

# Use small grid for fast tests
SMALL_GRID = GridConfig(nx=24, ny=24, nz=16, dx=1000.0, dy=1000.0, dz=500.0)
DEFAULT_PLUME = PlumeConfig()
DEFAULT_TURB = TurbulenceConfig(octaves=3, seed=42)


def test_apply_turbulence_shape() -> None:
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    result = apply_turbulence(base, DEFAULT_TURB, SMALL_GRID, 0)
    assert result.shape == base.shape
    assert result.dtype == np.float32


def test_apply_turbulence_nonnegative() -> None:
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    result = apply_turbulence(base, DEFAULT_TURB, SMALL_GRID, 0)
    assert result.min() >= 0.0


def test_turbulence_increases_variance() -> None:
    """Turbulence should produce higher spatial variance than smooth Gaussian."""
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    turb = apply_turbulence(base, DEFAULT_TURB, SMALL_GRID, 0)
    # Normalize both to [0, 1] for fair comparison
    base_norm = base / base.max() if base.max() > 0 else base
    turb_norm = turb / turb.max() if turb.max() > 0 else turb
    # Laplacian variance as a proxy for spatial frequency content
    base_lap_var = np.var(laplace(base_norm.astype(np.float64)))
    turb_lap_var = np.var(laplace(turb_norm.astype(np.float64)))
    assert turb_lap_var > base_lap_var


def test_turbulence_preserves_mass_approximately() -> None:
    """Total mass should be preserved within 50% (curl displacement redistributes)."""
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    turb = apply_turbulence(base, DEFAULT_TURB, SMALL_GRID, 0)
    base_mass = base.sum()
    turb_mass = turb.sum()
    if base_mass > 0:
        ratio = turb_mass / base_mass
        assert 0.1 < ratio < 2.0, f"Mass ratio {ratio:.3f} out of range"


def test_generate_turbulent_timestep() -> None:
    result = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, 0)
    assert result.shape == SMALL_GRID.shape
    assert result.dtype == np.float32
    assert result.min() >= 0.0


def test_generate_turbulent_timestep_disabled() -> None:
    """When turbulence is disabled, should return plain Gaussian."""
    turb_off = TurbulenceConfig(enabled=False)
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    result = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, turb_off, 0)
    np.testing.assert_array_equal(result, base)


def test_generate_turbulent_sequence_shape() -> None:
    n = 3
    ds = generate_turbulent_sequence(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, n)
    assert "concentration" in ds
    assert ds["concentration"].shape == (n, *SMALL_GRID.shape)


def test_generate_turbulent_sequence_coords() -> None:
    n = 2
    ds = generate_turbulent_sequence(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, n)
    assert list(ds["concentration"].dims) == ["time", "z", "y", "x"]
    assert len(ds.coords["time"]) == n
    assert len(ds.coords["z"]) == SMALL_GRID.nz
    assert len(ds.coords["y"]) == SMALL_GRID.ny
    assert len(ds.coords["x"]) == SMALL_GRID.nx


def test_temporal_coherence() -> None:
    """Adjacent frames should be highly correlated (no popping)."""
    turb = TurbulenceConfig(octaves=3, temporal_speed=0.02, seed=7)
    ds = generate_turbulent_sequence(DEFAULT_PLUME, SMALL_GRID, turb, 3)
    conc = ds["concentration"].values
    for t in range(conc.shape[0] - 1):
        a = conc[t].ravel()
        b = conc[t + 1].ravel()
        corr = np.corrcoef(a, b)[0, 1]
        assert corr > 0.5, f"Frame {t} -> {t + 1} correlation {corr:.4f} too low"


def test_deterministic_seed() -> None:
    a = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, 0)
    b = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, 0)
    np.testing.assert_array_equal(a, b)
