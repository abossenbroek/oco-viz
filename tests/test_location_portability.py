"""Tests for location portability — config-driven coordinates."""

from __future__ import annotations

import pytest

from oco_viz.config.schema import DomainConfig, load_config


def test_domain_bbox_corridor() -> None:
    """Default corridor domain bbox covers expected area."""
    domain = DomainConfig()
    bbox = domain.bbox()
    lon_min, lat_min, lon_max, lat_max = bbox
    # Corridor midpoint at -26.36, 28.61, 300km extent
    assert lat_min < -26.36 < lat_max
    assert lon_min < 28.61 < lon_max
    assert lon_max > lon_min
    assert lat_max > lat_min


def test_domain_bbox_seattle() -> None:
    """Seattle domain bbox covers expected area."""
    domain = DomainConfig(
        origin_lat=47.60,
        origin_lon=-122.33,
        extent_x_km=80.0,
        extent_y_km=80.0,
    )
    bbox = domain.bbox()
    lon_min, lat_min, lon_max, lat_max = bbox
    assert lat_min < 47.60 < lat_max
    assert lon_min < -122.33 < lon_max


def test_load_config_seattle() -> None:
    """Seattle config overlay loads and overrides domain."""
    config = load_config("seattle")
    assert config.data_source.domain.origin_lat == pytest.approx(47.60)
    assert config.data_source.domain.origin_lon == pytest.approx(-122.33)
    assert config.plume.emission_rate == pytest.approx(200.0)
    assert config.plume.stack_height == pytest.approx(50.0)


def test_load_config_corridor_default() -> None:
    """Default config uses Highveld corridor coordinates."""
    config = load_config()
    assert config.data_source.domain.origin_lat == pytest.approx(-26.36)
    assert config.data_source.domain.origin_lon == pytest.approx(28.61)


def test_domain_bbox_symmetric() -> None:
    """Bbox should be roughly symmetric around origin."""
    domain = DomainConfig(
        origin_lat=0.0,
        origin_lon=0.0,
        extent_x_km=100.0,
        extent_y_km=100.0,
    )
    bbox = domain.bbox()
    lon_min, lat_min, lon_max, lat_max = bbox
    # At equator, should be symmetric
    assert abs(lon_min + lon_max) < 0.01
    assert abs(lat_min + lat_max) < 0.01
