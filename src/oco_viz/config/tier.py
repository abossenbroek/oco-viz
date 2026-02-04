"""Tier enum for rendering quality levels."""

from __future__ import annotations

from enum import Enum


class Tier(str, Enum):
    """Rendering quality tier.

    sketch: fast iteration, minimal rendering
    study: density/TF refinement, MVP quality
    exhibition: gallery-quality output (aspirational target)
    """

    sketch = "sketch"
    study = "study"
    exhibition = "exhibition"
