"""Tests for Highveld Industrial Corridor configuration."""

from __future__ import annotations

import math

from oco_viz.config.schema import DomainConfig, PointSource, load_config


def test_corridor_bbox_contains_secunda() -> None:
    """Sasol Secunda (-26.52, 29.17) must be within the default domain bbox."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    assert lat_min < -26.52 < lat_max
    assert lon_min < 29.17 < lon_max


def test_corridor_bbox_contains_joburg() -> None:
    """Johannesburg (-26.20, 28.04) must be within the default domain bbox."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    assert lat_min < -26.20 < lat_max
    assert lon_min < 28.04 < lon_max


def test_corridor_source_inventory_populated() -> None:
    """base.yaml must define at least 3 emission sources."""
    config = load_config()
    assert len(config.data_source.sources) >= 3


def test_corridor_both_cities_30km_margin() -> None:
    """Both Sasol and Joburg must be >= 30 km from domain edge."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(domain.origin_lat))

    for name, lat, lon in [("Sasol", -26.52, 29.17), ("Joburg", -26.20, 28.04)]:
        margin_south = (lat - lat_min) * km_per_deg_lat
        margin_north = (lat_max - lat) * km_per_deg_lat
        margin_west = (lon - lon_min) * km_per_deg_lon
        margin_east = (lon_max - lon) * km_per_deg_lon
        min_margin = min(margin_south, margin_north, margin_west, margin_east)
        assert min_margin >= 30.0, f"{name} only {min_margin:.1f} km from edge"


def test_corridor_annotation_labels() -> None:
    """Annotation facility_name must reference Highveld."""
    config = load_config()
    assert "Highveld" in config.annotations.facility_name


def test_point_source_model() -> None:
    """PointSource model creates valid instances."""
    src = PointSource(name="Test", lat=-26.0, lon=28.0, source_type="point")
    assert src.name == "Test"
    assert src.source_type == "point"


def test_annotation_region_name() -> None:
    """region_name field is populated from base.yaml."""
    config = load_config()
    assert config.annotations.region_name is not None
    assert "Mpumalanga" in config.annotations.region_name
