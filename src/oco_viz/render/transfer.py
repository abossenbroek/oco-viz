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
    def default_plume(cls) -> TransferFunction:
        """Default transfer function for CO2 plume visualization."""
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
                ControlPoint(scalar=0.3, opacity=0.1),
                ControlPoint(scalar=0.5, opacity=0.3),
                ControlPoint(scalar=0.8, opacity=0.6),
                ControlPoint(scalar=1.0, opacity=0.8),
            ],
        )
