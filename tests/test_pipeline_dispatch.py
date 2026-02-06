"""Regression tests for pipeline mode dispatch."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import numpy as np
import pytest
import xarray as xr

from oco_viz.config import load_config
from oco_viz.data.pipeline import run_data_pipeline

if TYPE_CHECKING:
    from oco_viz.config.schema import AppConfig, GridConfig


def _make_config() -> AppConfig:
    return load_config("dev_mac", overrides={"grid": {"nx": 8, "ny": 8, "nz": 4}})


def _dummy_ds(grid: GridConfig) -> xr.Dataset:
    nz, ny, nx = grid.shape
    return xr.Dataset(
        {
            "concentration": (
                ["time", "z", "y", "x"],
                np.zeros((1, nz, ny, nx), dtype=np.float32),
            ),
        },
        coords={
            "time": [0],
            "z": np.arange(nz) * grid.dz,
            "y": np.arange(ny) * grid.dy,
            "x": np.arange(nx) * grid.dx,
        },
    )


def test_gaussian_mode_not_swallowed_by_era5_path() -> None:
    """Regression: gaussian mode must not dispatch to wind when era5_path is set."""
    config = _make_config()

    with patch("oco_viz.data.pipeline.generate_sequence") as mock_gauss:
        mock_gauss.return_value = _dummy_ds(config.grid)
        run_data_pipeline(config, mode="gaussian", era5_path=Path("/fake/era5.nc"))
        mock_gauss.assert_called_once()


def test_wind_mode_requires_era5_path() -> None:
    """mode='wind' without era5_path must raise ValueError."""
    config = _make_config()
    with pytest.raises(ValueError, match="mode='wind' requires era5_path"):
        run_data_pipeline(config, mode="wind", era5_path=None)


def test_wind_mode_dispatches_correctly() -> None:
    """mode='wind' with era5_path should call build_wind_driven_plume."""
    config = _make_config()

    with patch("oco_viz.data.pipeline.build_wind_driven_plume") as mock_wind:
        mock_wind.return_value = _dummy_ds(config.grid)
        run_data_pipeline(config, mode="wind", era5_path=Path("/fake/era5.nc"))
        mock_wind.assert_called_once()
