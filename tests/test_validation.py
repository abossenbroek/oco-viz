"""Tests for XCO2 column validation module."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from oco_viz.config.schema import GridConfig, ValidationConfig
from oco_viz.data.validation import (
    ValidationResult,
    compare_modeled_observed,
    compute_column_xco2,
    generate_validation_report,
)


def _make_grid() -> GridConfig:
    return GridConfig(nx=10, ny=10, nz=8, dx=1000.0, dy=1000.0, dz=500.0)


def _make_val_cfg(**overrides: object) -> ValidationConfig:
    defaults: dict[str, object] = {}
    defaults.update(overrides)
    return ValidationConfig(**defaults)


def test_compute_column_xco2_shape() -> None:
    """3D input (nz, ny, nx) produces 2D output (ny, nx)."""
    grid = _make_grid()
    conc = np.random.default_rng(42).uniform(400, 430, size=(8, 10, 10)).astype(np.float32)
    result = compute_column_xco2(conc, grid, _make_val_cfg())
    assert result.shape == (10, 10)
    assert result.dtype == np.float32


def test_compute_column_xco2_uniform() -> None:
    """Uniform 3D field collapses to the same uniform 2D value."""
    grid = _make_grid()
    value = 420.0
    conc = np.full((8, 10, 10), value, dtype=np.float32)
    result = compute_column_xco2(conc, grid, _make_val_cfg())
    np.testing.assert_allclose(result, value, atol=1e-3)


def test_pressure_weighted_vs_simple() -> None:
    """Pressure-weighted average differs from simple mean when profile varies with z."""
    grid = _make_grid()
    rng = np.random.default_rng(99)
    # Create a concentration gradient: lower layers have higher values
    conc = np.zeros((8, 10, 10), dtype=np.float32)
    for k in range(8):
        conc[k] = 420.0 + (8 - k) * 2.0  # higher at bottom (k=0)

    weighted = compute_column_xco2(conc, grid, _make_val_cfg(pressure_weighted=True))
    simple = compute_column_xco2(conc, grid, _make_val_cfg(pressure_weighted=False))

    # Pressure-weighted should give MORE weight to lower layers (higher conc)
    # so the weighted average should be larger than the simple mean
    assert np.mean(weighted) > np.mean(simple)


def test_compare_perfect_match() -> None:
    """Identical modeled and observed gives RMSE~0, correlation~1, passed=True."""
    modeled = np.full((10, 10), 425.0, dtype=np.float32)
    observed = modeled.copy()
    cfg = _make_val_cfg()
    result = compare_modeled_observed(modeled, observed, cfg)
    assert result.rmse_ppm < 1e-6
    assert result.correlation > 0.999 or np.isnan(result.correlation)
    assert result.passed is True


def test_compare_with_bias() -> None:
    """Constant offset in modeled shows up in bias_ppm."""
    rng = np.random.default_rng(7)
    observed = rng.uniform(420, 430, size=(10, 10)).astype(np.float32)
    bias = 3.0
    modeled = observed + bias
    cfg = _make_val_cfg()
    result = compare_modeled_observed(modeled, observed, cfg)
    np.testing.assert_allclose(result.bias_ppm, bias, atol=1e-4)


def test_compare_ignores_nan() -> None:
    """NaN in observed excludes those points from the comparison."""
    modeled = np.full((10, 10), 425.0, dtype=np.float32)
    observed = np.full((10, 10), 425.0, dtype=np.float32)
    # Set half to NaN
    observed[:5, :] = np.nan
    cfg = _make_val_cfg()
    result = compare_modeled_observed(modeled, observed, cfg)
    assert result.n_observations == 50  # only the non-NaN half


def test_compare_too_few_observations() -> None:
    """Fewer than 3 valid observations yields NaN correlation."""
    modeled = np.full((10, 10), 420.0, dtype=np.float32)
    observed = np.full((10, 10), np.nan, dtype=np.float32)
    # Only 2 valid points
    observed[0, 0] = 420.0
    observed[0, 1] = 421.0
    cfg = _make_val_cfg()
    result = compare_modeled_observed(modeled, observed, cfg)
    assert result.n_observations == 2
    assert np.isnan(result.correlation)


def test_generate_report_writes_json(tmp_path: Path) -> None:
    """generate_validation_report writes a JSON file with correct keys."""
    result = ValidationResult(
        rmse_ppm=1.5,
        bias_ppm=0.3,
        correlation=0.95,
        fraction_within_threshold=0.8,
        n_observations=100,
        passed=True,
    )
    report_path = generate_validation_report(result, tmp_path)
    assert report_path.exists()
    data = json.loads(report_path.read_text())
    expected_keys = {
        "rmse_ppm",
        "bias_ppm",
        "correlation",
        "fraction_within_threshold",
        "n_observations",
        "passed",
    }
    assert set(data.keys()) == expected_keys
    assert data["rmse_ppm"] == 1.5
    assert data["passed"] is True
