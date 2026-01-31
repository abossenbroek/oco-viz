import time

import pytest

from oco_viz.config import load_config
from oco_viz.data.zarr_store import write_zarr
from oco_viz.plume.gaussian import generate_sequence
from oco_viz.sequencer.controller import render_sequence


@pytest.mark.skipci
def test_render_sequence_produces_frames(tmp_path):
    config = load_config(
        "dev_mac",
        overrides={
            "output": {
                "width": 64,
                "height": 64,
                "frames_dir": str(tmp_path / "frames"),
            }
        },
    )

    zarr_path = tmp_path / "plume.zarr"
    ds = generate_sequence(config.plume, config.grid, num_timesteps=3)
    write_zarr(ds, zarr_path)

    paths = render_sequence(config, zarr_path, num_frames=3)
    assert len(paths) == 3
    for p in paths:
        assert p.exists()
        assert p.stat().st_size > 0


@pytest.mark.skipci
def test_resume_skips_existing(tmp_path):
    config = load_config(
        "dev_mac",
        overrides={
            "output": {
                "width": 64,
                "height": 64,
                "frames_dir": str(tmp_path / "frames"),
            }
        },
    )

    zarr_path = tmp_path / "plume.zarr"
    ds = generate_sequence(config.plume, config.grid, num_timesteps=2)
    write_zarr(ds, zarr_path)

    paths1 = render_sequence(config, zarr_path, num_frames=2)
    mtimes1 = [p.stat().st_mtime for p in paths1]

    time.sleep(0.1)
    paths2 = render_sequence(config, zarr_path, num_frames=2)
    mtimes2 = [p.stat().st_mtime for p in paths2]

    for m1, m2 in zip(mtimes1, mtimes2, strict=True):
        assert m1 == m2
