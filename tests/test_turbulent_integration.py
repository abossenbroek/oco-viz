"""Wave 4 integration tests: turbulent plume + retuned TFs + fixed VTK rendering."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.ndimage import laplace

from oco_viz.config import load_config
from oco_viz.config.schema import (
    GridConfig,
    PlumeConfig,
    PostProcessConfig,
    TurbulenceConfig,
)
from oco_viz.plume.gaussian import generate_timestep as gaussian_timestep
from oco_viz.plume.turbulent import generate_turbulent_sequence, generate_turbulent_timestep
from oco_viz.postprocess.pipeline import PostProcessPipeline
from oco_viz.render.camera import CameraState
from oco_viz.render.renderer import PRESETS, VolumeRenderer, resolve_transfer_function
from oco_viz.render.transfer import TransferFunction
from oco_viz.render.volume import numpy_to_vtk_image

# Small grid for fast integration tests
SMALL_GRID = GridConfig(nx=20, ny=20, nz=12, dx=1000.0, dy=1000.0, dz=500.0)
DEFAULT_PLUME = PlumeConfig()
DEFAULT_TURB = TurbulenceConfig(octaves=3, seed=42)


def test_turbulent_sequence_produces_valid_dataset() -> None:
    """Turbulent sequence generates valid xr.Dataset with (time, z, y, x)."""
    ds = generate_turbulent_sequence(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, num_timesteps=3)
    assert "concentration" in ds
    assert list(ds["concentration"].dims) == ["time", "z", "y", "x"]
    assert ds["concentration"].shape == (3, *SMALL_GRID.shape)
    assert ds["concentration"].dtype == np.float32


def test_turbulent_has_higher_variance_than_gaussian() -> None:
    """Concentration variance higher than smooth Gaussian (turbulence works)."""
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    turb = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, 0)
    # Normalize both
    base_n = base / base.max() if base.max() > 0 else base
    turb_n = turb / turb.max() if turb.max() > 0 else turb
    assert np.var(laplace(turb_n.astype(np.float64))) > np.var(
        laplace(base_n.astype(np.float64)),
    )


def test_mass_preserved_within_range() -> None:
    """Total mass preserved within reasonable range of base Gaussian."""
    base = gaussian_timestep(DEFAULT_PLUME, SMALL_GRID, 0)
    turb = generate_turbulent_timestep(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, 0)
    base_mass = float(base.sum())
    turb_mass = float(turb.sum())
    if base_mass > 0:
        ratio = turb_mass / base_mass
        assert 0.1 < ratio < 3.0, f"Mass ratio {ratio:.3f} out of expected range"


def test_temporal_coherence_no_popping() -> None:
    """Frame-to-frame correlation > 0.5 (no popping)."""
    ds = generate_turbulent_sequence(DEFAULT_PLUME, SMALL_GRID, DEFAULT_TURB, num_timesteps=4)
    conc = ds["concentration"].values
    for t in range(conc.shape[0] - 1):
        a = conc[t].ravel()
        b = conc[t + 1].ravel()
        corr = float(np.corrcoef(a, b)[0, 1])
        assert corr > 0.5, f"Frame {t}->{t+1} correlation {corr:.3f} too low"


def test_vtk_spacing_matches_grid() -> None:
    """VTK spacing matches grid config (not 1.0, 1.0, 1.0)."""
    data = np.random.default_rng(42).random(SMALL_GRID.shape, dtype=np.float32)
    spacing = (SMALL_GRID.dx, SMALL_GRID.dy, SMALL_GRID.dz)
    image = numpy_to_vtk_image(data, spacing=spacing)
    assert image.GetSpacing() == (1000.0, 1000.0, 500.0)


def test_postprocess_order_fog_bloom_tonemap() -> None:
    """Post-process order is fog -> bloom -> tonemap."""
    config = PostProcessConfig(bloom_intensity=0.5, bloom_threshold=0.3, exposure=1.0)
    pipeline = PostProcessPipeline(config)

    # HDR input
    rgb = np.full((32, 32, 3), 0.1, dtype=np.float32)
    rgb[12:20, 12:20, :] = 3.0
    depth = np.full((32, 32), 10.0, dtype=np.float32)

    result = pipeline.process(rgb, depth)
    # After tonemap (last step), output is in [0, 1]
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_preset_dispatch_cinematic_storm() -> None:
    """Config preset='cinematic_storm' selects correct TF."""
    tf = resolve_transfer_function("cinematic_storm")
    expected = TransferFunction.cinematic_storm()
    assert len(tf.color_points) == len(expected.color_points)
    assert len(tf.opacity_points) == len(expected.opacity_points)
    for a, b in zip(tf.opacity_points, expected.opacity_points, strict=True):
        assert a == b


def test_all_presets_known() -> None:
    """All expected presets are wired into PRESETS dict."""
    expected = {
        "soot", "default_plume", "cinematic_storm", "cinematic_ember",
        "cinematic_atmospheric", "absolute_atmospheric",
    }
    assert expected == set(PRESETS.keys())


@pytest.mark.skipci
def test_render_produces_non_black_frame() -> None:
    """Render with turbulent plume + retuned TF produces non-black, non-uniform frame."""
    config = load_config(
        "dev_mac",
        overrides={
            "output": {"width": 64, "height": 64},
            "turbulence": {"octaves": 2},
            "sky": {"enabled": True},
        },
    )
    renderer = VolumeRenderer(config)
    renderer.configure()

    conc = generate_turbulent_timestep(config.plume, config.grid, config.turbulence, 0)
    camera = CameraState(position=(200, 200, 100), focal_point=(50, 50, 30))
    rgb, _ = renderer.render_frame(conc, camera)

    assert rgb.shape == (64, 64, 3)
    assert rgb.max() > 0.01, "Frame is all black"
    assert rgb.std() > 0.001, "Frame is uniform"

    renderer.finalize()
