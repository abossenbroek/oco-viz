"""Tests for automatic camera composition from plume geometry."""

from __future__ import annotations

import numpy as np
import pytest

from oco_viz.config.schema import CompositionConfig
from oco_viz.render.composition import (
    compose_camera_from_plume,
    compute_camera_distance,
    compute_elevation_bias,
    compute_focal_point,
    plume_bounding_box,
)


class TestPlumeBoundingBox:
    def test_centroid_at_center_of_uniform_field(self) -> None:
        field = np.ones((10, 20, 30), dtype=np.float32)
        spacing = (500.0, 1000.0, 1000.0)
        centroid, _bbox_min, _bbox_max = plume_bounding_box(field, 0.01, spacing)
        # Input is (z, y, x), reordered to (x, y, z) for camera coords
        # x-extent: 30 * 1000 = 30000, center ~ 14500
        # y-extent: 20 * 1000 = 20000, center ~ 9500
        # z-extent: 10 * 500  = 5000,  center ~ 2250
        assert centroid[0] == pytest.approx(14500.0, rel=0.1)
        assert centroid[1] == pytest.approx(9500.0, rel=0.1)
        assert centroid[2] == pytest.approx(2250.0, rel=0.1)

    def test_spacing_scales_bbox(self) -> None:
        field = np.ones((5, 5, 5), dtype=np.float32)
        s1 = (100.0, 100.0, 100.0)
        s2 = (200.0, 200.0, 200.0)
        _, bmin1, bmax1 = plume_bounding_box(field, 0.01, s1)
        _, bmin2, bmax2 = plume_bounding_box(field, 0.01, s2)
        extent1 = tuple(mx - mn for mx, mn in zip(bmax1, bmin1, strict=True))
        extent2 = tuple(mx - mn for mx, mn in zip(bmax2, bmin2, strict=True))
        for e1, e2 in zip(extent1, extent2, strict=True):
            assert e2 == pytest.approx(e1 * 2.0, rel=0.01)

    def test_empty_field_fallback_to_center(self) -> None:
        field = np.zeros((10, 20, 30), dtype=np.float32)
        spacing = (500.0, 1000.0, 1000.0)
        centroid, bbox_min, bbox_max = plume_bounding_box(field, 0.01, spacing)
        # Falls back to volume center
        expected_x = (30 - 1) * 1000.0 / 2.0
        expected_y = (20 - 1) * 1000.0 / 2.0
        expected_z = (10 - 1) * 500.0 / 2.0
        assert centroid[0] == pytest.approx(expected_x, rel=0.01)
        assert centroid[1] == pytest.approx(expected_y, rel=0.01)
        assert centroid[2] == pytest.approx(expected_z, rel=0.01)
        # bbox covers full volume
        assert all(mn <= mx for mn, mx in zip(bbox_min, bbox_max, strict=True))

    def test_localized_plume_centroid(self) -> None:
        field = np.zeros((10, 20, 30), dtype=np.float32)
        # Place plume in corner (z=0:3, y=0:3, x=0:3)
        field[0:3, 0:3, 0:3] = 1.0
        spacing = (500.0, 1000.0, 1000.0)
        centroid, _, _ = plume_bounding_box(field, 0.01, spacing)
        # Centroid should be near origin corner in (x, y, z) coords
        assert centroid[0] < 3000.0  # x
        assert centroid[1] < 3000.0  # y
        assert centroid[2] < 1500.0  # z


class TestComputeCameraDistance:
    def test_distance_inversely_proportional_to_fill(self) -> None:
        bounds = ((0.0, 0.0, 0.0), (100.0, 100.0, 100.0))
        d1 = compute_camera_distance(bounds, 0.4, 30.0)
        d2 = compute_camera_distance(bounds, 0.8, 30.0)
        assert d1 > d2

    def test_distance_floor_at_one(self) -> None:
        bounds = ((0.0, 0.0, 0.0), (0.001, 0.001, 0.001))
        d = compute_camera_distance(bounds, 0.8, 30.0)
        assert d >= 1.0

    def test_larger_plume_needs_more_distance(self) -> None:
        small_bounds = ((0.0, 0.0, 0.0), (50.0, 50.0, 50.0))
        large_bounds = ((0.0, 0.0, 0.0), (200.0, 200.0, 200.0))
        d_small = compute_camera_distance(small_bounds, 0.6, 30.0)
        d_large = compute_camera_distance(large_bounds, 0.6, 30.0)
        assert d_large > d_small


class TestComputeFocalPoint:
    def test_zero_offset_preserves_centroid(self) -> None:
        centroid = (100.0, 200.0, 300.0)
        result = compute_focal_point(centroid, (0.0, 0.0))
        assert result == pytest.approx(centroid)

    def test_offset_shifts_x_and_z(self) -> None:
        centroid = (100.0, 200.0, 300.0)
        result = compute_focal_point(centroid, (10.0, 5.0))
        assert result[0] != centroid[0]
        assert result[1] == centroid[1]
        assert result[2] != centroid[2]


class TestComputeElevationBias:
    def test_no_emphasis_returns_base(self) -> None:
        result = compute_elevation_bias(30.0, vertical_emphasis=False)
        assert result == pytest.approx(30.0)

    def test_emphasis_adds_bias(self) -> None:
        result = compute_elevation_bias(30.0, vertical_emphasis=True, bias_degrees=10.0)
        assert result == pytest.approx(40.0)

    def test_clamp_to_89(self) -> None:
        result = compute_elevation_bias(85.0, vertical_emphasis=True, bias_degrees=10.0)
        assert result <= 89.0

    def test_clamp_to_zero(self) -> None:
        result = compute_elevation_bias(-5.0, vertical_emphasis=False)
        assert result >= 0.0


class TestComposeCameraFromPlume:
    def test_full_pipeline_returns_valid_tuple(self) -> None:
        field = np.ones((10, 10, 10), dtype=np.float32)
        config = CompositionConfig(enabled=True)
        focal, distance, elevation = compose_camera_from_plume(
            field,
            config,
            (500.0, 1000.0, 1000.0),
        )
        assert len(focal) == 3
        assert distance > 0
        assert 0 <= elevation <= 89

    def test_vertical_emphasis_increases_elevation(self) -> None:
        field = np.ones((10, 10, 10), dtype=np.float32)
        config_no = CompositionConfig(enabled=True, vertical_emphasis=False)
        config_yes = CompositionConfig(enabled=True, vertical_emphasis=True)
        _, _, elev_no = compose_camera_from_plume(field, config_no, (500.0, 1000.0, 1000.0))
        _, _, elev_yes = compose_camera_from_plume(field, config_yes, (500.0, 1000.0, 1000.0))
        assert elev_yes > elev_no

    def test_offset_changes_focal(self) -> None:
        field = np.ones((10, 10, 10), dtype=np.float32)
        config_zero = CompositionConfig(enabled=True, asymmetric_offset=(0.0, 0.0))
        config_off = CompositionConfig(enabled=True, asymmetric_offset=(0.1, 0.05))
        f_zero, _, _ = compose_camera_from_plume(field, config_zero, (500.0, 1000.0, 1000.0))
        f_off, _, _ = compose_camera_from_plume(field, config_off, (500.0, 1000.0, 1000.0))
        assert f_zero != f_off
