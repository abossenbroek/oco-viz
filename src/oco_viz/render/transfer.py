"""Transfer function mapping scalar values to color and opacity."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import attr
import vtk

if TYPE_CHECKING:
    from pathlib import Path


@attr.s(auto_attribs=True, frozen=True, slots=True)
class ControlPoint:
    """A single point in the transfer function."""

    scalar: float
    r: float = 0.0
    g: float = 0.0
    b: float = 0.0
    opacity: float = 0.0


@attr.s(auto_attribs=True)
class TransferFunction:
    """Transfer function with color and opacity control points."""

    color_points: list[ControlPoint] = attr.Factory(list)
    opacity_points: list[ControlPoint] = attr.Factory(list)

    def to_vtk(self) -> tuple[vtk.vtkColorTransferFunction, vtk.vtkPiecewiseFunction]:
        """Convert to VTK transfer function objects."""
        color_tf = vtk.vtkColorTransferFunction()
        for cp in self.color_points:
            color_tf.AddRGBPoint(cp.scalar, cp.r, cp.g, cp.b)

        opacity_tf = vtk.vtkPiecewiseFunction()
        for cp in self.opacity_points:
            opacity_tf.AddPoint(cp.scalar, cp.opacity)

        return color_tf, opacity_tf

    def to_json(self) -> str:
        """Serialize to JSON string."""
        data = {
            "color_points": [attr.asdict(cp) for cp in self.color_points],
            "opacity_points": [attr.asdict(cp) for cp in self.opacity_points],
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> TransferFunction:
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls(
            color_points=[ControlPoint(**cp) for cp in data["color_points"]],
            opacity_points=[ControlPoint(**cp) for cp in data["opacity_points"]],
        )

    @classmethod
    def from_json_file(cls, path: Path) -> TransferFunction:
        """Load from a JSON file."""
        return cls.from_json(path.read_text())

    def save_json(self, path: Path) -> None:
        """Save to a JSON file."""
        path.write_text(self.to_json())

    @classmethod
    def cinematic_storm(cls) -> TransferFunction:
        """Dark, dramatic volumetric look with deep self-shadowing.

        Moody thunderhead palette — dense core is brightest (not darkest).
        Tuned for sample_distance=250 (half smallest voxel spacing).
        """
        return cls(
            color_points=[
                ControlPoint(scalar=0.0, r=0.0, g=0.0, b=0.0),
                ControlPoint(scalar=0.15, r=0.25, g=0.23, b=0.22),
                ControlPoint(scalar=0.35, r=0.35, g=0.38, b=0.45),
                ControlPoint(scalar=0.55, r=0.50, g=0.52, b=0.58),
                ControlPoint(scalar=0.75, r=0.65, g=0.63, b=0.60),
                ControlPoint(scalar=0.90, r=0.75, g=0.72, b=0.68),
                ControlPoint(scalar=1.0, r=0.80, g=0.78, b=0.75),
            ],
            opacity_points=[
                ControlPoint(scalar=0.0, opacity=0.0),
                ControlPoint(scalar=0.05, opacity=0.0),
                ControlPoint(scalar=0.10, opacity=0.02),
                ControlPoint(scalar=0.25, opacity=0.08),
                ControlPoint(scalar=0.50, opacity=0.20),
                ControlPoint(scalar=0.70, opacity=0.30),
                ControlPoint(scalar=0.85, opacity=0.38),
                ControlPoint(scalar=1.0, opacity=0.45),
            ],
        )

    @classmethod
    def cinematic_ember(cls) -> TransferFunction:
        """Hot emission look with deep reds to white-yellow.

        Volcanic emission palette — brighter reds/oranges.
        Tuned for sample_distance=250 (half smallest voxel spacing).
        """
        return cls(
            color_points=[
                ControlPoint(scalar=0.0, r=0.0, g=0.0, b=0.0),
                ControlPoint(scalar=0.2, r=0.30, g=0.05, b=0.0),
                ControlPoint(scalar=0.4, r=0.65, g=0.15, b=0.02),
                ControlPoint(scalar=0.6, r=0.90, g=0.35, b=0.05),
                ControlPoint(scalar=0.8, r=1.0, g=0.60, b=0.15),
                ControlPoint(scalar=1.0, r=1.0, g=0.90, b=0.50),
            ],
            opacity_points=[
                ControlPoint(scalar=0.0, opacity=0.0),
                ControlPoint(scalar=0.1, opacity=0.0),
                ControlPoint(scalar=0.25, opacity=0.03),
                ControlPoint(scalar=0.4, opacity=0.10),
                ControlPoint(scalar=0.6, opacity=0.22),
                ControlPoint(scalar=0.8, opacity=0.38),
                ControlPoint(scalar=1.0, opacity=0.50),
            ],
        )

    @classmethod
    def cinematic_atmospheric(cls) -> TransferFunction:
        """Realistic atmospheric scattering with Rayleigh blue-shift.

        Bright silvery palette for ethereal look.
        Tuned for sample_distance=250 (half smallest voxel spacing).
        """
        return cls(
            color_points=[
                ControlPoint(scalar=0.0, r=0.0, g=0.0, b=0.0),
                ControlPoint(scalar=0.15, r=0.45, g=0.50, b=0.65),
                ControlPoint(scalar=0.30, r=0.55, g=0.58, b=0.68),
                ControlPoint(scalar=0.50, r=0.70, g=0.72, b=0.75),
                ControlPoint(scalar=0.70, r=0.82, g=0.80, b=0.78),
                ControlPoint(scalar=0.85, r=0.90, g=0.87, b=0.84),
                ControlPoint(scalar=1.0, r=0.95, g=0.93, b=0.90),
            ],
            opacity_points=[
                ControlPoint(scalar=0.0, opacity=0.0),
                ControlPoint(scalar=0.05, opacity=0.0),
                ControlPoint(scalar=0.15, opacity=0.02),
                ControlPoint(scalar=0.30, opacity=0.08),
                ControlPoint(scalar=0.50, opacity=0.18),
                ControlPoint(scalar=0.70, opacity=0.30),
                ControlPoint(scalar=0.85, opacity=0.40),
                ControlPoint(scalar=1.0, opacity=0.50),
            ],
        )

    @classmethod
    def absolute_atmospheric(cls) -> TransferFunction:
        """Ultra-low opacity for full atmospheric column rendering.

        Designed for absolute-mode normalization where the entire 10 km column
        has non-zero values. Peak opacity 0.20 prevents the column from going
        solid opaque.
        """
        return cls(
            color_points=[
                ControlPoint(scalar=0.0, r=0.0, g=0.0, b=0.0),
                ControlPoint(scalar=0.10, r=0.30, g=0.35, b=0.50),
                ControlPoint(scalar=0.25, r=0.45, g=0.50, b=0.60),
                ControlPoint(scalar=0.40, r=0.55, g=0.58, b=0.65),
                ControlPoint(scalar=0.60, r=0.70, g=0.70, b=0.72),
                ControlPoint(scalar=0.80, r=0.82, g=0.80, b=0.78),
                ControlPoint(scalar=1.0, r=0.92, g=0.90, b=0.88),
            ],
            opacity_points=[
                ControlPoint(scalar=0.0, opacity=0.0),
                ControlPoint(scalar=0.05, opacity=0.0),
                ControlPoint(scalar=0.15, opacity=0.01),
                ControlPoint(scalar=0.30, opacity=0.04),
                ControlPoint(scalar=0.50, opacity=0.08),
                ControlPoint(scalar=0.70, opacity=0.14),
                ControlPoint(scalar=0.85, opacity=0.18),
                ControlPoint(scalar=1.0, opacity=0.20),
            ],
        )

    @classmethod
    def default_plume(cls) -> TransferFunction:
        """Default transfer function for CO2 plume visualization.

        Warm scientific palette — dense core is brightest.
        Tuned for sample_distance=250 (half smallest voxel spacing).
        """
        return cls(
            color_points=[
                ControlPoint(scalar=0.0, r=0.0, g=0.0, b=0.0),
                ControlPoint(scalar=0.2, r=0.1, g=0.1, b=0.4),
                ControlPoint(scalar=0.4, r=0.3, g=0.2, b=0.6),
                ControlPoint(scalar=0.6, r=0.7, g=0.3, b=0.2),
                ControlPoint(scalar=0.8, r=0.9, g=0.6, b=0.1),
                ControlPoint(scalar=1.0, r=1.0, g=0.9, b=0.8),
            ],
            opacity_points=[
                ControlPoint(scalar=0.0, opacity=0.0),
                ControlPoint(scalar=0.1, opacity=0.0),
                ControlPoint(scalar=0.25, opacity=0.04),
                ControlPoint(scalar=0.5, opacity=0.15),
                ControlPoint(scalar=0.8, opacity=0.35),
                ControlPoint(scalar=1.0, opacity=0.45),
            ],
        )
