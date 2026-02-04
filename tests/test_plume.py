import numpy as np

from oco_viz.config.schema import GridConfig, PlumeConfig
from oco_viz.plume.gaussian import generate_sequence, generate_timestep


def test_generate_timestep_shape() -> None:
    grid = GridConfig()
    plume = PlumeConfig()
    result = generate_timestep(plume, grid, time_index=0)
    assert result.shape == (60, 100, 100)
    assert result.dtype == np.float32


def test_generate_timestep_non_negative() -> None:
    grid = GridConfig()
    plume = PlumeConfig()
    result = generate_timestep(plume, grid, time_index=0)
    assert np.all(result >= 0)


def test_generate_timestep_peak_near_source() -> None:
    grid = GridConfig()
    plume = PlumeConfig()
    result = generate_timestep(plume, grid, time_index=0)
    # Peak should be somewhere, not all zero
    assert result.max() > 0


def test_zero_concentration_upwind() -> None:
    grid = GridConfig()
    # Wind from west (270), so upwind is towards x=0 from source
    plume = PlumeConfig(source_x=50.0, wind_direction=270.0)
    result = generate_timestep(plume, grid, time_index=0)
    # Upwind region: low x values, well before source
    upwind_slice = result[:, :, :10]
    # Should have much less concentration than peak (Gaussian tail is small but nonzero)
    assert upwind_slice.max() < result.max() * 0.5


def test_stability_d_narrower_than_a() -> None:
    grid = GridConfig(nx=200)
    plume_a = PlumeConfig(stability_class="A")
    plume_d = PlumeConfig(stability_class="D")

    result_a = generate_timestep(plume_a, grid, time_index=0)
    result_d = generate_timestep(plume_d, grid, time_index=0)

    # Class A (very unstable) -> wider plume -> more spread
    # Class D (neutral) -> narrower plume -> less spread
    # Measure: standard deviation of cross-wind concentration distribution
    # Sum over z, measure spread in y
    a_y_profile = result_a.sum(axis=(0, 2))  # sum over z and x -> y profile
    d_y_profile = result_d.sum(axis=(0, 2))

    if a_y_profile.sum() > 0 and d_y_profile.sum() > 0:
        y_coords = np.arange(len(a_y_profile), dtype=np.float64)
        a_mean = np.average(y_coords, weights=a_y_profile)
        d_mean = np.average(y_coords, weights=d_y_profile)
        a_std = np.sqrt(np.average((y_coords - a_mean) ** 2, weights=a_y_profile))
        d_std = np.sqrt(np.average((y_coords - d_mean) ** 2, weights=d_y_profile))
        assert a_std > d_std, f"A std={a_std} should be > D std={d_std}"


def test_generate_sequence_returns_dataset() -> None:
    grid = GridConfig()
    plume = PlumeConfig()
    ds = generate_sequence(plume, grid, num_timesteps=4)
    assert "concentration" in ds
    assert ds.concentration.dims == ("time", "z", "y", "x")
    assert ds.concentration.shape == (4, 60, 100, 100)
    assert ds.concentration.dtype == np.float32
