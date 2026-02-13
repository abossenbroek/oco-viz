"""Tests for ECD data ingestion and turbulence coupling."""

from __future__ import annotations

import numpy as np
import xarray as xr

from oco_viz.config.schema import (
    DomainConfig,
    ECDConfig,
    GridConfig,
    PlumeConfig,
    TurbulenceConfig,
)
from oco_viz.data.ecd import (
    attach_ecd_anomaly,
    compute_amplitude_modulator,
    compute_ecd_anomaly,
    regrid_ecd_to_domain,
)
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.plume.turbulent import apply_turbulence

SMALL_GRID = GridConfig(nx=24, ny=24, nz=16, dx=1000.0, dy=1000.0, dz=500.0)
DEFAULT_DOMAIN = DomainConfig()


def _make_ecd_dataset(n_soundings: int = 50) -> xr.Dataset:
    """Create a synthetic ECD dataset for testing."""
    rng = np.random.default_rng(42)
    lats = rng.uniform(-27.0, -26.0, n_soundings)
    lons = rng.uniform(28.5, 29.5, n_soundings)
    xco2 = rng.uniform(415.0, 425.0, n_soundings).astype(np.float32)

    return xr.Dataset(
        {
            "ecd_xco2": ("sounding", xco2),
            "latitude": ("sounding", lats),
            "longitude": ("sounding", lons),
        },
    )


def test_compute_ecd_anomaly() -> None:
    """Anomaly should be positive delta from background."""
    ds = _make_ecd_dataset()
    anomaly = compute_ecd_anomaly(ds, background_ppm=415.0)
    assert anomaly.dtype == np.float32
    assert np.all(anomaly >= 0.0)
    # Some values should be positive (since xco2 > 415)
    assert np.any(anomaly > 0.0)


def test_compute_ecd_anomaly_all_below_background() -> None:
    """When all xco2 < background, anomaly should be zero."""
    ds = xr.Dataset(
        {
            "ecd_xco2": ("sounding", np.array([410.0, 412.0, 414.0], dtype=np.float32)),
            "latitude": ("sounding", np.array([-26.5, -26.5, -26.5])),
            "longitude": ("sounding", np.array([29.2, 29.2, 29.2])),
        },
    )
    anomaly = compute_ecd_anomaly(ds, background_ppm=415.0)
    np.testing.assert_array_equal(anomaly, 0.0)


def test_regrid_ecd_to_domain_shape() -> None:
    """Regridded output should have (ny, nx) shape."""
    ds = _make_ecd_dataset()
    anomaly = compute_ecd_anomaly(ds)
    gridded = regrid_ecd_to_domain(ds, anomaly, DEFAULT_DOMAIN, SMALL_GRID)
    assert gridded.shape == (SMALL_GRID.ny, SMALL_GRID.nx)
    assert gridded.dtype == np.float32


def test_compute_amplitude_modulator_default() -> None:
    """Zero ECD delta should return modulator of 1.0."""
    delta = np.zeros((10, 10), dtype=np.float32)
    assert compute_amplitude_modulator(delta) == 1.0


def test_compute_amplitude_modulator_positive() -> None:
    """Positive ECD delta should return modulator > 1.0."""
    delta = np.full((10, 10), 5.0, dtype=np.float32)
    mod = compute_amplitude_modulator(delta, anomaly_scale=1.0)
    assert mod > 1.0


def test_compute_amplitude_modulator_empty() -> None:
    """Empty array should return 1.0."""
    delta = np.empty(0, dtype=np.float32)
    assert compute_amplitude_modulator(delta) == 1.0


def test_apply_turbulence_with_modulator() -> None:
    """apply_turbulence should accept amplitude_modulator kwarg."""
    grid = SMALL_GRID
    plume = PlumeConfig(source_x=12.0, source_y=12.0)
    turb = TurbulenceConfig(octaves=3, seed=42)

    base = generate_timestep(plume, grid, 0)
    # Default modulator (backward compatible)
    result_default = apply_turbulence(base, turb, grid, 0)
    # Explicit modulator = 1.0 should be identical
    result_one = apply_turbulence(base, turb, grid, 0, amplitude_modulator=1.0)
    np.testing.assert_array_equal(result_default, result_one)


def test_apply_turbulence_modulator_changes_output() -> None:
    """Modulator != 1.0 should change turbulence output."""
    grid = SMALL_GRID
    plume = PlumeConfig(source_x=12.0, source_y=12.0)
    turb = TurbulenceConfig(octaves=3, seed=42)

    base = generate_timestep(plume, grid, 0)
    result_1 = apply_turbulence(base, turb, grid, 0, amplitude_modulator=1.0)
    result_2 = apply_turbulence(base, turb, grid, 0, amplitude_modulator=2.0)
    # Outputs should differ
    assert not np.array_equal(result_1, result_2)


def test_attach_ecd_anomaly_empty_paths() -> None:
    """No paths should return dataset unchanged."""
    ds = xr.Dataset({"concentration": (["time", "z", "y", "x"], np.zeros((1, 4, 4, 4)))})
    result = attach_ecd_anomaly(ds, [], DEFAULT_DOMAIN, SMALL_GRID)
    assert "ecd_delta" not in result


def test_ecd_config_defaults() -> None:
    """ECDConfig should have expected defaults."""
    cfg = ECDConfig()
    assert cfg.enabled is False
    assert cfg.cache_dir == "data/ecd"
    assert cfg.anomaly_scale == 1.0
    assert cfg.date_range == ("2024-01-01", "2024-01-31")
