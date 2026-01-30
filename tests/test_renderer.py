import os

import numpy as np
import pytest

from oco_viz.config import load_config
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.camera import CameraState
from oco_viz.render.renderer import VolumeRenderer

_skip_ci = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="VTK EGL segfaults on headless CI",
)


@_skip_ci
def test_configure_and_render():
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


@_skip_ci
def test_second_render_works():
    config = load_config("dev_mac", overrides={"output": {"width": 64, "height": 64}})
    renderer = VolumeRenderer(config)
    renderer.configure()

    conc1 = generate_timestep(config.plume, config.grid, time_index=0)
    conc2 = generate_timestep(config.plume, config.grid, time_index=5)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))

    rgb1, _ = renderer.render_frame(conc1, camera)
    rgb2, _ = renderer.render_frame(conc2, camera)

    assert rgb1.shape == (64, 64, 3)
    assert rgb2.shape == (64, 64, 3)

    renderer.finalize()


@_skip_ci
def test_render_with_postprocessing():
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
