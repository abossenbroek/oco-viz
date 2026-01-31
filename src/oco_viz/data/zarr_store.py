"""Read/write concentration data to/from Zarr stores."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

if TYPE_CHECKING:
    from pathlib import Path


_REQUIRED_DIMS = ("time", "z", "y", "x")
_REQUIRED_VARS = ("concentration",)


def write_zarr(ds: xr.Dataset, path: Path) -> None:
    """Write an xr.Dataset to a Zarr store with appropriate chunking."""
    # Validate
    _validate_dataset(ds)
    # Write directly — chunking is determined by encoding
    nt = min(24, ds.sizes["time"])
    chunks = (nt, ds.sizes["z"], ds.sizes["y"], ds.sizes["x"])
    encoding = {"concentration": {"chunks": chunks}}
    ds.to_zarr(str(path), mode="w", encoding=encoding)


def read_zarr(path: Path) -> xr.Dataset:
    """Read a Zarr store as a lazy xr.Dataset."""
    ds: xr.Dataset = xr.open_zarr(str(path))
    _validate_dataset(ds)
    return ds


def _validate_dataset(ds: xr.Dataset) -> None:
    """Validate that the dataset has the required structure."""
    for var in _REQUIRED_VARS:
        if var not in ds:
            msg = f"Missing variable: {var}"
            raise ValueError(msg)

    conc = ds[_REQUIRED_VARS[0]]
    for dim in _REQUIRED_DIMS:
        if dim not in conc.dims:
            msg = f"Missing dimension: {dim}"
            raise ValueError(msg)

    if conc.dtype not in (np.float32, np.float64):
        msg = f"Unexpected dtype: {conc.dtype}, expected float32 or float64"
        raise ValueError(msg)
