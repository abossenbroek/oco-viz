from __future__ import annotations

import logging

import pytest

from oco_viz.config import AppConfig, GridConfig, load_config
from oco_viz.config.schema import ScatteringConfig


def test_grid_shape() -> None:
    g = GridConfig()
    assert g.shape == (60, 100, 100)


def test_load_config_defaults() -> None:
    cfg = load_config()
    assert cfg.grid.shape == (60, 100, 100)
    assert cfg.output.width == 1920


def test_load_config_dev_mac() -> None:
    cfg = load_config("dev_mac")
    assert cfg.output.width == 512
    assert cfg.output.height == 512
    # base values still present
    assert cfg.grid.nx == 100
    # overlay applied
    assert cfg.scattering.jittering is False


def test_load_config_merges_overlay() -> None:
    cfg = load_config("dev_mac")
    # fog_density from base should survive overlay
    assert cfg.postprocess.fog_density == pytest.approx(0.02)


def test_validation_rejects_negative_resolution() -> None:
    with pytest.raises(ValueError, match="greater than"):
        AppConfig(output={"width": -1, "height": 100})


def test_validation_rejects_invalid_stability() -> None:
    with pytest.raises(ValueError, match="Stability class must be A-F"):
        AppConfig(plume={"stability_class": "Z"})


def test_overrides() -> None:
    cfg = load_config(overrides={"output": {"width": 256}})
    assert cfg.output.width == 256


def test_extreme_anisotropy_warns(caplog: pytest.LogCaptureFixture) -> None:
    """Extreme anisotropy values should produce a warning."""
    with caplog.at_level(logging.WARNING):
        cfg = ScatteringConfig(anisotropy=0.95)
    assert cfg.anisotropy == 0.95
    assert any("anisotropy" in r.message.lower() for r in caplog.records)
