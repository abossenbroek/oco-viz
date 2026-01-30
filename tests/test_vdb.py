import numpy as np

from oco_viz.sequencer.vdb_export import export_vdb, read_vdb


def test_vdb_file_written(tmp_path):
    arr = np.random.default_rng(42).random((10, 10, 10)).astype(np.float32)
    out = tmp_path / "test.vdb"
    result = export_vdb(arr, out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_grid_name_is_density(tmp_path):
    arr = np.ones((5, 5, 5), dtype=np.float32)
    path = export_vdb(arr, tmp_path / "test.vdb")
    _, name = read_vdb(path)
    assert name == "density"


def test_sparse_active_count(tmp_path):
    arr = np.zeros((20, 20, 20), dtype=np.float32)
    # Only a small region has non-zero values
    arr[5:8, 5:8, 5:8] = 1.0
    path = export_vdb(arr, tmp_path / "sparse.vdb")

    recovered, _ = read_vdb(path)
    # Sparse: most of the volume is zero, only 3x3x3=27 voxels active
    assert recovered.size < 20 * 20 * 20


def test_round_trip_above_threshold(tmp_path):
    rng = np.random.default_rng(7)
    arr = np.zeros((10, 10, 10), dtype=np.float32)
    # Fill entire array so bounding box matches shape
    arr[:] = rng.random((10, 10, 10)).astype(np.float32)
    arr[arr < 0.3] = 0.0
    # Ensure corners are non-zero so bounding box spans full array
    arr[0, 0, 0] = 1.0
    arr[9, 9, 9] = 1.0

    path = export_vdb(arr, tmp_path / "rt.vdb", threshold=0.0)
    recovered, _ = read_vdb(path)

    assert recovered.shape == arr.shape
    # Non-zero values should match
    mask = arr > 0.0
    np.testing.assert_allclose(recovered[mask], arr[mask], atol=1e-6)
