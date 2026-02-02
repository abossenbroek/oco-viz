import math

import numpy as np

from oco_viz.data.era5 import (
    build_cds_request,
    wind_components_from_direction,
)


def test_build_cds_request_date_parsing() -> None:
    req = build_cds_request("2024-03-15")
    assert req["year"] == "2024"
    assert req["month"] == "03"
    assert req["day"] == "15"
    assert "u_component_of_wind" in req["variable"]
    assert "v_component_of_wind" in req["variable"]
    assert len(req["time"]) == 24


def test_build_cds_request_pressure_levels() -> None:
    req = build_cds_request("2024-01-01", pressure_levels=[850, 500])
    assert req["pressure_level"] == ["850", "500"]


def test_wind_components_north_wind() -> None:
    # Wind from the north (0 deg) blowing southward -> u=0, v<0
    u, v = wind_components_from_direction(10.0, 0.0)
    assert abs(u) < 1e-10
    assert v < 0
    assert abs(v - (-10.0)) < 1e-10


def test_wind_components_west_wind() -> None:
    # Wind from the west (270 deg) blowing eastward -> u>0, v~0
    u, v = wind_components_from_direction(10.0, 270.0)
    assert u > 0
    assert abs(u - 10.0) < 1e-6
    assert abs(v) < 1e-6


def test_wind_components_round_trip() -> None:
    speed = 8.5
    direction = 135.0
    u, v = wind_components_from_direction(speed, direction)
    recovered_speed = math.sqrt(u**2 + v**2)
    np.testing.assert_allclose(recovered_speed, speed, atol=1e-10)
