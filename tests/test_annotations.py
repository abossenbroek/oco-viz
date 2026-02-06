"""Tests for text annotations on rendered frames."""

from __future__ import annotations

import numpy as np

from oco_viz.config.schema import AnnotationConfig
from oco_viz.render.annotations import apply_annotations


def _make_annotation_cfg(**overrides: object) -> AnnotationConfig:
    defaults: dict[str, object] = {}
    defaults.update(overrides)
    return AnnotationConfig(**defaults)


def _mock_frame(h: int = 256, w: int = 384) -> np.ndarray:
    return np.full((h, w, 3), 0.2, dtype=np.float32)


def _mock_meta() -> dict[str, object]:
    return {
        "timestamp": "2024-01-15 14:00 UTC",
        "frame_index": 0,
        "total_frames": 48,
        "grid_dx_m": 1000.0,
    }


def test_shape_preserved() -> None:
    frame = _mock_frame()
    cfg = _make_annotation_cfg()
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    assert result.shape == frame.shape


def test_dtype_float32() -> None:
    frame = _mock_frame()
    cfg = _make_annotation_cfg()
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    assert result.dtype == np.float32


def test_all_disabled_identity() -> None:
    frame = _mock_frame()
    cfg = _make_annotation_cfg(
        show_timestamp=False,
        show_facility=False,
        show_credits=False,
        show_scale_bar=False,
    )
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    np.testing.assert_allclose(result, frame, atol=1e-6)


def test_modifies_pixels() -> None:
    frame = _mock_frame()
    cfg = _make_annotation_cfg(show_timestamp=True)
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    assert not np.allclose(result, frame)


def test_panel_opacity() -> None:
    frame = _mock_frame(h=256, w=384)
    cfg = _make_annotation_cfg(panel_opacity=0.6)
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    # Panel should darken some pixels compared to original
    # (dark panel on a 0.2 gray background)
    darker = result < frame
    assert darker.any()


def test_scale_bar_length() -> None:
    frame = _mock_frame(h=256, w=384)
    cfg = _make_annotation_cfg(
        show_scale_bar=True,
        show_timestamp=False,
        show_facility=False,
        show_credits=False,
    )
    meta = _mock_meta()
    result = apply_annotations(frame, cfg, meta)
    # Scale bar renders in the bottom region, so bottom rows should differ
    bottom_region = result[-60:, :, :]
    original_bottom = frame[-60:, :, :]
    assert not np.allclose(bottom_region, original_bottom)
