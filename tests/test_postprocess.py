import numpy as np

from oco_viz.config.schema import PostProcessConfig
from oco_viz.postprocess.bloom import apply_bloom
from oco_viz.postprocess.fog import apply_depth_fog
from oco_viz.postprocess.pipeline import PostProcessPipeline, default_pipeline
from oco_viz.postprocess.tonemap import aces_tonemap


def _make_rgb(h: int = 64, w: int = 64) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.random((h, w, 3), dtype=np.float32)


def _make_depth(h: int = 64, w: int = 64) -> np.ndarray:
    return np.linspace(0, 100, h * w, dtype=np.float32).reshape(h, w)


def test_fog_shifts_toward_fog_color():
    rgb = _make_rgb()
    depth = _make_depth()
    fog_color = (0.7, 0.75, 0.85)
    result = apply_depth_fog(rgb, depth, density=0.05, fog_color=fog_color)
    # Far pixels (high depth) should be closer to fog color
    far_mean = result[-1, :, :].mean(axis=0)
    near_mean = result[0, :, :].mean(axis=0)
    fog_arr = np.array(fog_color)
    far_dist = np.linalg.norm(far_mean - fog_arr)
    near_dist = np.linalg.norm(near_mean - fog_arr)
    assert far_dist < near_dist


def test_tonemap_output_in_range():
    rgb = _make_rgb() * 5.0  # HDR input
    result = aces_tonemap(rgb)
    assert result.min() >= 0.0
    assert result.max() <= 1.0
    assert result.dtype == np.float32


def test_bloom_increases_brightness():
    rgb = _make_rgb()
    rgb[30:35, 30:35, :] = 1.0  # bright spot
    result = apply_bloom(rgb, threshold=0.8, intensity=0.5, passes=3)
    # Mean brightness should increase slightly
    assert result.mean() >= rgb.mean()


def test_pipeline_composes_stages():
    config = PostProcessConfig()
    pipeline = PostProcessPipeline(config)
    rgb = _make_rgb()
    depth = _make_depth()
    result = pipeline.process(rgb, depth)
    assert result.shape == rgb.shape
    assert result.dtype == np.float32


def test_default_pipeline():
    pipeline = default_pipeline()
    rgb = _make_rgb()
    depth = _make_depth()
    result = pipeline.process(rgb, depth)
    assert result.shape == rgb.shape


def test_quantize():
    pipeline = default_pipeline()
    rgb = np.full((10, 10, 3), 0.5, dtype=np.float32)
    q = pipeline.quantize(rgb)
    assert q.dtype == np.uint8
    assert q.max() == 128 or q.max() == 127  # rounding
