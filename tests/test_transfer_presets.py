"""Tests for retuned cinematic transfer function presets."""

from __future__ import annotations

from pathlib import Path

from oco_viz.render.transfer import TransferFunction

CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs" / "transfer_functions"


def _max_opacity(tf: TransferFunction) -> float:
    return max(cp.opacity for cp in tf.opacity_points)


def test_storm_peak_opacity() -> None:
    tf = TransferFunction.cinematic_storm()
    assert _max_opacity(tf) < 0.15


def test_ember_peak_opacity() -> None:
    tf = TransferFunction.cinematic_ember()
    assert _max_opacity(tf) <= 0.15


def test_atmospheric_peak_opacity() -> None:
    tf = TransferFunction.cinematic_atmospheric()
    assert _max_opacity(tf) <= 0.10


def test_default_plume_peak_opacity() -> None:
    tf = TransferFunction.default_plume()
    assert _max_opacity(tf) <= 0.15


def test_all_presets_to_vtk() -> None:
    for factory in [
        TransferFunction.cinematic_storm,
        TransferFunction.cinematic_ember,
        TransferFunction.cinematic_atmospheric,
        TransferFunction.default_plume,
    ]:
        tf = factory()
        color_tf, opacity_tf = tf.to_vtk()
        assert color_tf.GetSize() > 0
        assert opacity_tf.GetSize() > 0


def test_all_presets_json_roundtrip() -> None:
    for factory in [
        TransferFunction.cinematic_storm,
        TransferFunction.cinematic_ember,
        TransferFunction.cinematic_atmospheric,
        TransferFunction.default_plume,
    ]:
        tf = factory()
        json_str = tf.to_json()
        tf2 = TransferFunction.from_json(json_str)
        assert len(tf2.color_points) == len(tf.color_points)
        assert len(tf2.opacity_points) == len(tf.opacity_points)
        for a, b in zip(tf.opacity_points, tf2.opacity_points, strict=True):
            assert a == b


def test_storm_json_matches_classmethod() -> None:
    from_file = TransferFunction.from_json_file(CONFIGS_DIR / "storm.json")
    from_cls = TransferFunction.cinematic_storm()
    assert len(from_file.opacity_points) == len(from_cls.opacity_points)
    for a, b in zip(from_file.opacity_points, from_cls.opacity_points, strict=True):
        assert a == b


def test_ember_json_matches_classmethod() -> None:
    from_file = TransferFunction.from_json_file(CONFIGS_DIR / "ember.json")
    from_cls = TransferFunction.cinematic_ember()
    assert len(from_file.opacity_points) == len(from_cls.opacity_points)
    for a, b in zip(from_file.opacity_points, from_cls.opacity_points, strict=True):
        assert a == b


def test_atmospheric_json_matches_classmethod() -> None:
    from_file = TransferFunction.from_json_file(CONFIGS_DIR / "atmospheric.json")
    from_cls = TransferFunction.cinematic_atmospheric()
    assert len(from_file.opacity_points) == len(from_cls.opacity_points)
    for a, b in zip(from_file.opacity_points, from_cls.opacity_points, strict=True):
        assert a == b


def test_default_plume_json_matches_classmethod() -> None:
    from_file = TransferFunction.from_json_file(CONFIGS_DIR / "default_plume.json")
    from_cls = TransferFunction.default_plume()
    assert len(from_file.opacity_points) == len(from_cls.opacity_points)
    for a, b in zip(from_file.opacity_points, from_cls.opacity_points, strict=True):
        assert a == b


def test_storm_warm_highlight() -> None:
    """Storm should have warm highlight at scalar 0.15."""
    tf = TransferFunction.cinematic_storm()
    s15 = [cp for cp in tf.color_points if cp.scalar == 0.15]
    assert len(s15) == 1
    cp = s15[0]
    # Warm means r > b
    assert cp.r > cp.b
