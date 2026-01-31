import numpy as np
import pytest
import xarray as xr

from oco_viz.data.zarr_store import read_zarr, write_zarr


def _make_dataset(nt: int = 4, nz: int = 10, ny: int = 20, nx: int = 20) -> xr.Dataset:
    rng = np.random.default_rng(42)
    data = rng.random((nt, nz, ny, nx), dtype=np.float32)
    return xr.Dataset(
        {"concentration": (["time", "z", "y", "x"], data)},
        coords={
            "time": np.arange(nt),
            "z": np.arange(nz, dtype=np.float64),
            "y": np.arange(ny, dtype=np.float64),
            "x": np.arange(nx, dtype=np.float64),
        },
    )


def test_write_and_read_zarr(tmp_path):
    ds = _make_dataset(nt=24, nz=10, ny=20, nx=20)
    zarr_path = tmp_path / "test.zarr"
    write_zarr(ds, zarr_path)
    assert zarr_path.exists()

    ds_read = read_zarr(zarr_path)
    assert "concentration" in ds_read
    assert ds_read.concentration.shape == (24, 10, 20, 20)


def test_round_trip_preserves_data(tmp_path):
    ds = _make_dataset()
    zarr_path = tmp_path / "test.zarr"
    write_zarr(ds, zarr_path)
    ds_read = read_zarr(zarr_path)
    np.testing.assert_allclose(ds.concentration.values, ds_read.concentration.values, rtol=1e-6)


def test_validation_rejects_missing_var(tmp_path):
    ds = xr.Dataset({"other": (["time", "z", "y", "x"], np.zeros((2, 3, 4, 5)))})
    zarr_path = tmp_path / "bad.zarr"
    with pytest.raises(ValueError, match="Missing variable"):
        write_zarr(ds, zarr_path)


def test_validation_rejects_missing_dim(tmp_path):
    ds = xr.Dataset({"concentration": (["time", "level"], np.zeros((2, 3), dtype=np.float32))})
    zarr_path = tmp_path / "bad.zarr"
    with pytest.raises(ValueError, match="Missing dimension"):
        write_zarr(ds, zarr_path)
