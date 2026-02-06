"""XCO2 column validation: compare modeled plume against OCO observations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import attrs
import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig, ValidationConfig


# Standard atmosphere constants
_P0 = 101325.0  # Pa
_L = 0.0065  # K/m
_T0 = 288.15  # K
_G = 9.80665  # m/s^2
_M = 0.0289644  # kg/mol
_R = 8.31447  # J/(mol*K)


@attrs.frozen
class ValidationResult:
    """Validation comparison metrics."""

    rmse_ppm: float
    bias_ppm: float
    correlation: float
    fraction_within_threshold: float
    n_observations: int
    passed: bool


def _standard_atmosphere_pressure(z_meters: NDArray[np.floating[Any]]) -> NDArray[np.float64]:
    """Compute standard atmosphere pressure at given altitudes.

    Uses the barometric formula: P(z) = P0 * (1 - L*z/T0)^(g*M/(R*L))

    Parameters
    ----------
    z_meters : NDArray
        Altitudes in meters above sea level.

    Returns
    -------
    NDArray[np.float64]
        Pressure in Pa at each altitude.

    """
    exponent = _G * _M / (_R * _L)
    return np.asarray(_P0 * (1.0 - _L * z_meters / _T0) ** exponent, dtype=np.float64)


def compute_column_xco2(
    conc_3d: NDArray[np.floating[Any]],
    grid: GridConfig,
    val_cfg: ValidationConfig,
) -> NDArray[np.float32]:
    """Compute column-averaged XCO2 from a 3D concentration field.

    Parameters
    ----------
    conc_3d : NDArray
        Concentration field of shape (nz, ny, nx) in ppm.
    grid : GridConfig
        Spatial grid configuration providing dz.
    val_cfg : ValidationConfig
        Validation configuration controlling pressure weighting.

    Returns
    -------
    NDArray[np.float32]
        2D column-averaged XCO2 of shape (ny, nx) in ppm.

    """
    nz = conc_3d.shape[0]

    if not val_cfg.pressure_weighted:
        # Simple mean along z axis
        return np.asarray(np.mean(conc_3d, axis=0), dtype=np.float32)

    # Pressure-weighted column average
    # Compute pressure at the center of each vertical layer
    z_centers = np.array([(k + 0.5) * grid.dz for k in range(nz)])
    pressures = _standard_atmosphere_pressure(z_centers)

    # Normalize weights
    weights = pressures / np.sum(pressures)

    # Apply weights along z axis: weights shape (nz,) broadcast over (nz, ny, nx)
    weighted_sum = np.sum(conc_3d * weights[:, np.newaxis, np.newaxis], axis=0)

    return np.asarray(weighted_sum, dtype=np.float32)


def compare_modeled_observed(
    modeled_column: NDArray[np.floating[Any]],
    observed_xco2: NDArray[np.floating[Any]],
    val_cfg: ValidationConfig,
) -> ValidationResult:
    """Compare modeled column XCO2 against observed values.

    Parameters
    ----------
    modeled_column : NDArray
        2D modeled column XCO2 of shape (ny, nx).
    observed_xco2 : NDArray
        2D observed XCO2 of shape (ny, nx). NaN where no observation.
    val_cfg : ValidationConfig
        Validation configuration providing thresholds.

    Returns
    -------
    ValidationResult
        Comparison metrics and pass/fail status.

    """
    # Mask out NaN observations
    valid_mask = ~np.isnan(observed_xco2)
    n_valid = int(np.sum(valid_mask))

    if n_valid < 3:
        return ValidationResult(
            rmse_ppm=0.0,
            bias_ppm=0.0,
            correlation=float("nan"),
            fraction_within_threshold=0.0,
            n_observations=n_valid,
            passed=False,
        )

    mod_flat = modeled_column[valid_mask].astype(np.float64)
    obs_flat = observed_xco2[valid_mask].astype(np.float64)

    # RMSE
    diff = mod_flat - obs_flat
    rmse = float(np.sqrt(np.mean(diff**2)))

    # Bias
    bias = float(np.mean(diff))

    # Correlation
    corr_matrix = np.corrcoef(mod_flat, obs_flat)
    correlation = float(corr_matrix[0, 1])

    # Fraction within threshold
    enhancement_obs = np.abs(obs_flat - val_cfg.background_ppm)
    # Avoid division by very small enhancements: use at least 1 ppm
    threshold = val_cfg.threshold_fraction * np.maximum(enhancement_obs, 1.0)
    within = np.abs(diff) <= threshold
    fraction_within = float(np.mean(within))

    # Pass/fail
    passed = fraction_within >= val_cfg.pass_criterion

    return ValidationResult(
        rmse_ppm=rmse,
        bias_ppm=bias,
        correlation=correlation,
        fraction_within_threshold=fraction_within,
        n_observations=n_valid,
        passed=passed,
    )


def generate_validation_report(
    result: ValidationResult,
    output_dir: Path,
) -> Path:
    """Write validation results to a JSON report file.

    Parameters
    ----------
    result : ValidationResult
        Validation comparison metrics.
    output_dir : Path
        Directory to write the report to.

    Returns
    -------
    Path
        Path to the generated JSON report file.

    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "validation_report.json"

    report_data: dict[str, object] = {
        "rmse_ppm": result.rmse_ppm,
        "bias_ppm": result.bias_ppm,
        "correlation": result.correlation,
        "fraction_within_threshold": result.fraction_within_threshold,
        "n_observations": result.n_observations,
        "passed": result.passed,
    }

    with report_path.open("w") as f:
        json.dump(report_data, f, indent=2)

    return report_path
