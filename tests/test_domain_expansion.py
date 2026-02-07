"""Domain expansion tests: verify 300 km domain covers Sasol Secunda + Johannesburg."""

from __future__ import annotations

import math

import pytest

from oco_viz.config import DomainConfig, GridConfig, PlumeConfig

# Geographic coordinates
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


def test_bbox_centered_on_sasol() -> None:
    """BBox must be centered on Sasol Secunda."""
    domain = DomainConfig()
    lon_min, lat_min, lon_max, lat_max = domain.bbox()
    center_lon = (lon_min + lon_max) / 2
    center_lat = (lat_min + lat_max) / 2
    assert center_lon == pytest.approx(SASOL_LON, abs=0.01)
    assert center_lat == pytest.approx(SASOL_LAT, abs=0.01)


def test_bbox_east_of_secunda() -> None:
    """BBox east edge must be east of Secunda longitude."""
    domain = DomainConfig()
    _lon_min, _lat_min, lon_max, _lat_max = domain.bbox()
    assert lon_max > SASOL_LON, f"East edge {lon_max} not east of Secunda {SASOL_LON}"


def test_grid_physical_extent_matches_domain() -> None:
    """Grid nx*dx must equal domain extent_x_km * 1000 (meters)."""
    grid = GridConfig()
    domain = DomainConfig()
    assert grid.nx * grid.dx == pytest.approx(domain.extent_x_km * 1000)
    assert grid.ny * grid.dy == pytest.approx(domain.extent_y_km * 1000)


def test_plume_source_at_domain_center() -> None:
    """Plume source position (150, 150) maps to domain center in grid coordinates."""
    grid = GridConfig()
    plume = PlumeConfig()
    center_x = grid.nx / 2
    center_y = grid.ny / 2
    assert plume.source_x == pytest.approx(center_x)
    assert plume.source_y == pytest.approx(center_y)


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
    km_per_deg_lon = 111.32 * math.cos(math.radians(SASOL_LAT))
    margin_km = (JOBURG_LON - lon_min) * km_per_deg_lon
    assert margin_km > 20.0, f"Joburg only {margin_km:.1f} km from western edge"
