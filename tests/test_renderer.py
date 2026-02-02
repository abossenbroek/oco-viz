"""Tests for VolumeRenderer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from oco_viz.config import load_config
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState
from oco_viz.render.renderer import PRESETS, VolumeRenderer, resolve_transfer_function
from oco_viz.render.transfer import TransferFunction

if TYPE_CHECKING:
    from pathlib import Path


def test_preset_dispatch_all_known() -> None:
    for name in PRESETS:
        tf = resolve_transfer_function(name)
        assert isinstance(tf, TransferFunction)
        color_tf, opacity_tf = tf.to_vtk()
        assert color_tf.GetSize() > 0
        assert opacity_tf.GetSize() > 0


def test_preset_dispatch_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown transfer function preset"):
        resolve_transfer_function("nonexistent")


def test_preset_dispatch_json_path(tmp_path: Path) -> None:
    tf = TransferFunction.default_plume()
    path = tmp_path / "custom.json"
    tf.save_json(path)
    loaded = resolve_transfer_function("ignored", json_path=str(path))
    assert len(loaded.color_points) == len(tf.color_points)


@pytest.mark.skipci
def test_configure_and_render() -> None:
    config = load_config("dev_mac", overrides={"output": {"width": 128, "height": 128}})
    renderer = VolumeRenderer(config)
    renderer.configure()

    concentration = generate_timestep(config.plume, config.grid, time_index=0)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))
    rgb, depth = renderer.render_frame(concentration, camera)

    assert rgb.shape == (128, 128, 3)
    assert rgb.dtype == np.float32
    assert rgb.min() >= 0.0
    assert rgb.max() <= 1.0
    assert depth.shape == (128, 128)
    assert depth.dtype == np.float32
    # Non-black
    assert rgb.max() > 0.01

    renderer.finalize()


@pytest.mark.skipci
def test_second_render_reuses_volume() -> None:
    config = load_config("dev_mac", overrides={"output": {"width": 64, "height": 64}})
    renderer = VolumeRenderer(config)
    renderer.configure()

    conc1 = generate_timestep(config.plume, config.grid, time_index=0)
    conc2 = generate_timestep(config.plume, config.grid, time_index=5)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))

    rgb1, _ = renderer.render_frame(conc1, camera)
    # After first frame, volume should exist
    assert renderer._volume is not None
    volume_id = id(renderer._volume)

    rgb2, _ = renderer.render_frame(conc2, camera)
    # Volume actor should be reused (not recreated)
    assert id(renderer._volume) == volume_id

    assert rgb1.shape == (64, 64, 3)
    assert rgb2.shape == (64, 64, 3)

    renderer.finalize()


@pytest.mark.skipci
def test_render_with_postprocessing() -> None:
    config = load_config("dev_mac", overrides={"output": {"width": 64, "height": 64}})
    renderer = VolumeRenderer(config)
    renderer.configure()

    concentration = generate_timestep(config.plume, config.grid, time_index=0)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))

    # Without post-processing
    rgb_raw, _ = renderer.render_frame(concentration, camera)

    # With post-processing
    rgb_pp = renderer.render_frame_postprocessed(concentration, camera)

    assert rgb_pp.shape == rgb_raw.shape
    # Post-processed output should be different from raw
    assert not np.allclose(rgb_pp, rgb_raw)

    renderer.finalize()
