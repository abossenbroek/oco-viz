"""Tests for DataSource config schema additions (ticket 2-2)."""

from __future__ import annotations

import pytest

from oco_viz.config.schema import (
    AppConfig,
    DataSourceConfig,
    DomainConfig,
    ERA5Config,
    OCO3Config,
    load_config,
)


def test_domain_config_defaults():
    d = DomainConfig()
    assert d.origin_lat == pytest.approx(-26.52)
    assert d.origin_lon == pytest.approx(29.17)
    assert d.extent_x_km == pytest.approx(100.0)
    assert d.extent_y_km == pytest.approx(100.0)
    assert d.extent_z_km == pytest.approx(15.0)


def test_era5_config_defaults():
    e = ERA5Config()
    assert 1000 in e.pressure_levels
    assert 500 in e.pressure_levels
    assert "u_component_of_wind" in e.variables
    assert "v_component_of_wind" in e.variables


def test_oco3_config_defaults():
    o = OCO3Config()
    assert o.quality_threshold == 0
    assert o.collection_id


def test_datasource_config_defaults():
    ds = DataSourceConfig()
    assert ds.domain is not None
    assert ds.era5 is not None
    assert ds.oco3 is not None


def test_app_config_has_datasource():
    cfg = AppConfig()
    assert hasattr(cfg, "data_source")
    assert isinstance(cfg.data_source, DataSourceConfig)


def test_load_config_preserves_existing_fields():
    """Adding data_source must not break existing config loading."""
    cfg = load_config()
    assert cfg.grid.nx == 100
    assert cfg.output.width == 1920
    assert cfg.plume.wind_speed == pytest.approx(5.0)


def test_load_config_has_datasource_section():
    cfg = load_config()
    assert cfg.data_source.domain.origin_lat == pytest.approx(-26.52)


def test_datasource_overrides():
    cfg = load_config(overrides={"data_source": {"domain": {"extent_x_km": 200.0}}})
    assert cfg.data_source.domain.extent_x_km == pytest.approx(200.0)
    # Other defaults preserved
    assert cfg.data_source.domain.origin_lat == pytest.approx(-26.52)
