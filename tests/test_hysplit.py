from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from oco_viz.config import load_config
from oco_viz.data.hysplit import (
    generate_control_file,
    hysplit_or_gaussian,
    parse_cdump_to_dataset,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_control_file_generated(tmp_path: Path) -> None:
    ctrl = generate_control_file(
        tmp_path / "CONTROL",
        start_year=24,
        start_month=1,
        start_day=15,
    )
    assert ctrl.exists()
    text = ctrl.read_text()
    assert "-26.5200" in text
    assert "29.1700" in text
    assert "CO2" in text


def test_parse_cdump_to_dataset(tmp_path: Path) -> None:
    shape = (5, 10, 10)
    n_timesteps = 3
    data = np.random.default_rng(0).random(n_timesteps * np.prod(shape)).astype(np.float32)
    cdump = tmp_path / "cdump"
    data.tofile(str(cdump))

    ds = parse_cdump_to_dataset(cdump, shape)
    assert isinstance(ds, xr.Dataset)
    assert "concentration" in ds
    assert ds["concentration"].shape == (n_timesteps, *shape)


def test_hysplit_or_gaussian_falls_back() -> None:
    """When HYSPLIT is not available, should fall back to Gaussian."""
    config = load_config("dev_mac")
    ds = hysplit_or_gaussian(config, num_timesteps=2)
    assert "concentration" in ds
    assert ds["concentration"].shape[0] == 2
    assert np.all(ds["concentration"].values >= 0)
