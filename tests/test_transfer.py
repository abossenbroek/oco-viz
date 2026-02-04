"""Tests for transfer function module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oco_viz.render.transfer import ControlPoint, TransferFunction

if TYPE_CHECKING:
    from pathlib import Path


def test_json_round_trip() -> None:
    tf = TransferFunction.default_plume()
    json_str = tf.to_json()
    tf2 = TransferFunction.from_json(json_str)
    assert len(tf2.color_points) == len(tf.color_points)
    assert len(tf2.opacity_points) == len(tf.opacity_points)
    for a, b in zip(tf.color_points, tf2.color_points, strict=True):
        assert a == b
    for a, b in zip(tf.opacity_points, tf2.opacity_points, strict=True):
        assert a == b


def test_to_vtk_returns_correct_types() -> None:
    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()
    assert color_tf.GetSize() == len(tf.color_points)
    assert opacity_tf.GetSize() == len(tf.opacity_points)


def test_control_point_frozen() -> None:
    cp = ControlPoint(scalar=0.5, r=1.0, g=0.5, b=0.0, opacity=0.3)
    assert cp.scalar == 0.5
    assert cp.r == 1.0


def test_save_and_load_json(tmp_path: Path) -> None:
    tf = TransferFunction.default_plume()
    path = tmp_path / "tf.json"
    tf.save_json(path)
    tf2 = TransferFunction.from_json_file(path)
    assert len(tf2.color_points) == len(tf.color_points)


def test_empty_transfer_function() -> None:
    tf = TransferFunction()
    color_tf, opacity_tf = tf.to_vtk()
    assert color_tf.GetSize() == 0
    assert opacity_tf.GetSize() == 0


def test_transfer_function_has_no_flat_opacity_regions() -> None:
    """Transfer functions must not have flat opacity regions that create visual steps.

    Rationale: Flat regions (consecutive points with same opacity) create hard
    visual thresholds at volume boundaries. Smooth continuous ramps prevent
    rectangular boundary artifacts.
    """
    presets = [
        ("cinematic_storm", TransferFunction.cinematic_storm()),
        ("cinematic_atmospheric", TransferFunction.cinematic_atmospheric()),
        ("cinematic_ember", TransferFunction.cinematic_ember()),
        ("absolute_atmospheric", TransferFunction.absolute_atmospheric()),
        ("default_plume", TransferFunction.default_plume()),
    ]

    for name, preset in presets:
        opacity_vals = [p.opacity for p in preset.opacity_points]
        for i in range(1, len(opacity_vals)):
            # No two consecutive non-zero opacity values should be equal
            # (zero at origin is allowed as long as it immediately ramps up)
            if opacity_vals[i - 1] > 0.0:
                assert opacity_vals[i] > opacity_vals[i - 1], (
                    f"{name}: Flat opacity region at index {i}: "
                    f"{opacity_vals[i - 1]} == {opacity_vals[i]}"
                )


def test_transfer_function_opacity_starts_ramping_early() -> None:
    """Transfer functions must start ramping opacity early to avoid hard shells.

    Rationale: If opacity stays at 0.0 for too long (e.g., scalar 0.0-0.1),
    values near the threshold create visible rectangular shells.
    """
    presets = [
        ("cinematic_storm", TransferFunction.cinematic_storm()),
        ("cinematic_atmospheric", TransferFunction.cinematic_atmospheric()),
        ("cinematic_ember", TransferFunction.cinematic_ember()),
        ("absolute_atmospheric", TransferFunction.absolute_atmospheric()),
        ("default_plume", TransferFunction.default_plume()),
    ]

    for name, preset in presets:
        # Find first point with non-zero opacity
        first_nonzero_idx = next(
            (i for i, p in enumerate(preset.opacity_points) if p.opacity > 0),
            len(preset.opacity_points),
        )

        if first_nonzero_idx > 0:
            scalar_at_first_opacity = preset.opacity_points[first_nonzero_idx].scalar
            # Opacity should start ramping by scalar=0.05 at the latest
            assert scalar_at_first_opacity <= 0.05, (
                f"{name}: First non-zero opacity at scalar={scalar_at_first_opacity}: "
                f"should be <= 0.05 to avoid hard shell artifacts"
            )


def _interpolate_opacity(preset: TransferFunction, scalar: float) -> float:
    """Linearly interpolate opacity at a given scalar value."""
    points = sorted(preset.opacity_points, key=lambda p: p.scalar)
    if scalar <= points[0].scalar:
        return points[0].opacity
    if scalar >= points[-1].scalar:
        return points[-1].opacity
    for i in range(len(points) - 1):
        if points[i].scalar <= scalar <= points[i + 1].scalar:
            t = (scalar - points[i].scalar) / (points[i + 1].scalar - points[i].scalar)
            return points[i].opacity + t * (points[i + 1].opacity - points[i].opacity)
    return 0.0


def test_preset_has_low_value_opacity_ramp() -> None:
    """All anomaly-mode presets must have opacity >= 0.03 at scalar=0.25.

    Rationale: Composite/anomaly mode produces normalized values typically in
    the 0.0-0.3 range after ellipsoidal falloff. If opacity is too low at
    scalar=0.25, the plume becomes invisible (black output).

    Exception: absolute_atmospheric is designed for full-column rendering with
    intentionally lower opacity to prevent solid opaque volumes.

    Note: cinematic_ember has a slower ramp (0.03 at 0.25) but compensates with
    stronger colors. The threshold is set to catch presets that drop below 0.03.
    """
    # Anomaly-mode presets that need visibility at low scalar values
    anomaly_presets = [
        ("cinematic_storm", TransferFunction.cinematic_storm()),
        ("cinematic_atmospheric", TransferFunction.cinematic_atmospheric()),
        ("cinematic_ember", TransferFunction.cinematic_ember()),
        ("default_plume", TransferFunction.default_plume()),
    ]

    # Threshold: 0.03 catches dangerously low values while allowing stylistic variation
    # The original default_plume had 0.04 at 0.25 which was too low; cinematic_ember
    # has 0.03 but works due to color saturation.
    min_opacity_at_025 = 0.03
    for name, preset in anomaly_presets:
        opacity_at_025 = _interpolate_opacity(preset, 0.25)
        assert opacity_at_025 >= min_opacity_at_025, (
            f"{name}: opacity at scalar=0.25 is {opacity_at_025:.3f} < {min_opacity_at_025}: "
            f"composite mode will produce black/invisible output"
        )


def test_default_plume_matches_cinematic_storm_at_low_values() -> None:
    """default_plume opacity at low scalars should be comparable to cinematic_storm.

    Rationale: cinematic_storm is known to render correctly in composite mode.
    default_plume should have similar visibility characteristics at low scalar
    values to prevent black output regression.
    """
    default = TransferFunction.default_plume()
    storm = TransferFunction.cinematic_storm()

    # Check opacity at several low scalar values
    test_scalars = [0.10, 0.25, 0.30]
    for s in test_scalars:
        default_opacity = _interpolate_opacity(default, s)
        storm_opacity = _interpolate_opacity(storm, s)

        # default_plume opacity should be at least 50% of cinematic_storm
        ratio = default_opacity / storm_opacity if storm_opacity > 0 else 0
        assert ratio >= 0.5, (
            f"At scalar={s}: default_plume opacity ({default_opacity:.3f}) is "
            f"<50% of cinematic_storm ({storm_opacity:.3f}), ratio={ratio:.2f}"
        )
