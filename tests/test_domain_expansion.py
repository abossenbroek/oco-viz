"""Domain expansion tests: verify 300 km domain covers Highveld corridor."""

from __future__ import annotations

import math

import pytest

from oco_viz.config import DomainConfig, GridConfig, PlumeConfig

# Geographic coordinates
CORRIDOR_LAT = -26.36
CORRIDOR_LON = 28.61
SASOL_LAT = -26.52
SASOL_LON = 29.17
JOBURG_LAT = -26.20
JOBURG_LON = 28.05


def test_bbox_contains_johannesburg() -> None:
    """BBox west edge must be west of Johannesburg longitude."""
    domain = DomainConfig()
    lon_min, _lat_min, _lon_max, _lat_max = domain.bbox()
    assert lon_min < JOBURG_LON, f"West edge {lon_min} is not west of Joburg {JOBURG_LON}"


def test_bbox_contains_johannesburg_latitude() -> None:
    """BBox must span Johannesburg's latitude."""
    domain = DomainConfig()
    _lon_min, lat_min, _lon_max, lat_max = domain.bbox()
    assert lat_min < JOBURG_LAT < lat_max, (
        f"Joburg lat {JOBURG_LAT} outside [{lat_min}, {lat_max}]"
    )


def test_bbox_centered_on_corridor() -> None:
    """BBox must be centered on corridor midpoint."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    center_lon = (lon_min + lon_max) / 2
    center_lat = (lat_min + lat_max) / 2
    assert center_lon == pytest.approx(CORRIDOR_LON, abs=0.01)
    assert center_lat == pytest.approx(CORRIDOR_LAT, abs=0.01)


def test_bbox_contains_secunda() -> None:
    """BBox must contain Sasol Secunda."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    assert lon_min < SASOL_LON < lon_max, f"Secunda lon {SASOL_LON} outside bbox"
    assert lat_min < SASOL_LAT < lat_max, f"Secunda lat {SASOL_LAT} outside bbox"


def test_grid_physical_extent_matches_domain() -> None:
    """Grid nx*dx must equal domain extent_x_km * 1000 (meters)."""
    grid = GridConfig()
    domain = DomainConfig()
    assert grid.nx * grid.dx == pytest.approx(domain.extent_x_km * 1000)
    assert grid.ny * grid.dy == pytest.approx(domain.extent_y_km * 1000)


def test_plume_source_at_sasol_position() -> None:
    """Plume source position maps to Sasol's location in grid coordinates."""
    plume = PlumeConfig()
    # Sasol is east of center, so source_x > 150
    assert plume.source_x > 150.0
    # Sasol is south of center, so source_y < 150
    assert plume.source_y < 150.0


def test_domain_extent_is_300km() -> None:
    """Domain extent must be 300 km in both horizontal directions."""
    domain = DomainConfig()
    assert domain.extent_x_km == pytest.approx(300.0)
    assert domain.extent_y_km == pytest.approx(300.0)


def test_joburg_margin_from_edge() -> None:
    """Johannesburg must be at least 20 km inside the western domain edge."""
    domain = DomainConfig()
    lon_min, _lat_min, _lon_max, _lat_max = domain.bbox()
    # Approximate km per degree longitude at this latitude
    km_per_deg_lon = 111.32 * math.cos(math.radians(CORRIDOR_LAT))
    margin_km = (JOBURG_LON - lon_min) * km_per_deg_lon
    assert margin_km > 20.0, f"Joburg only {margin_km:.1f} km from western edge"
