"""Pasquill-Gifford stability classes and dispersion coefficients."""

from __future__ import annotations

# Pasquill-Gifford dispersion parameters: sigma_y = a * x^b, sigma_z = c * x^d
# x in meters, sigma in meters
# Reference: Turner (1970), Workbook of Atmospheric Dispersion Estimates
_PG_PARAMS: dict[str, tuple[float, float, float, float]] = {
    "A": (0.3658, 0.9031, 0.192, 1.2235),
    "B": (0.2751, 0.9031, 0.156, 1.0857),
    "C": (0.2090, 0.9031, 0.116, 0.9585),
    "D": (0.1471, 0.9031, 0.079, 0.8607),
    "E": (0.1046, 0.9031, 0.063, 0.7633),
    "F": (0.0722, 0.9031, 0.053, 0.6794),
}

VALID_CLASSES = frozenset(_PG_PARAMS.keys())


def sigma_y(x: float, stability: str) -> float:
    """Horizontal dispersion coefficient (meters) at downwind distance x (meters)."""
    params = _PG_PARAMS[stability.upper()]
    a, b = params[0], params[1]
    return float(a * float(x) ** b)


def sigma_z(x: float, stability: str) -> float:
    """Vertical dispersion coefficient (meters) at downwind distance x (meters)."""
    params = _PG_PARAMS[stability.upper()]
    c, d = params[2], params[3]
    return float(c * float(x) ** d)
