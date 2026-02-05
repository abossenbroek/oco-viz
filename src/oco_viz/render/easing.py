"""Easing functions for camera animation."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class EasingFunction(str, Enum):
    """Available easing curves for camera motion."""

    linear = "linear"
    smoothstep = "smoothstep"
    ease_in_cubic = "ease_in_cubic"
    ease_in_out_cubic = "ease_in_out_cubic"
    heavy_ease_in = "heavy_ease_in"


def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def _linear(t: float) -> float:
    return t


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def _ease_in_cubic(t: float) -> float:
    return t * t * t


def _ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def _heavy_ease_in(t: float) -> float:
    return t * t * t * t


_DISPATCH: dict[EasingFunction, Callable[[float], float]] = {
    EasingFunction.linear: _linear,
    EasingFunction.smoothstep: _smoothstep,
    EasingFunction.ease_in_cubic: _ease_in_cubic,
    EasingFunction.ease_in_out_cubic: _ease_in_out_cubic,
    EasingFunction.heavy_ease_in: _heavy_ease_in,
}


def apply_easing(t: float, easing: EasingFunction) -> float:
    """Apply an easing function to a normalized parameter t in [0, 1]."""
    t = _clamp01(t)
    fn = _DISPATCH[easing]
    return fn(t)
