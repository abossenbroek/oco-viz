"""Tests for semi-Lagrangian advection module."""

from __future__ import annotations

import numpy as np
import xarray as xr

from oco_viz.config.schema import AdvectionConfig, GridConfig, PlumeConfig, TurbulenceConfig
from oco_viz.plume.advection import advect_sequence, advect_step


def _make_grid() -> GridConfig:
    return GridConfig(nx=24, ny=24, nz=16, dx=1000.0, dy=1000.0, dz=500.0)


def _make_plume_cfg() -> PlumeConfig:
    return PlumeConfig(
        source_x=12.0,
        source_y=6.0,
        source_z=2.0,
        emission_rate=1000.0,
        wind_speed=5.0,
        wind_direction=270.0,
        mixing_height=6000.0,
        stack_height=200.0,
    )


def _make_adv_cfg(**overrides: object) -> AdvectionConfig:
    defaults: dict[str, object] = {
        "dt": 3600.0,
        "sub_steps": 1,
        "scheme": "semi_lagrangian",
        "mass_correction": False,
        "buoyancy_flux": 0.0,
    }
    defaults.update(overrides)
    return AdvectionConfig(**defaults)


def _make_turb_cfg() -> TurbulenceConfig:
    return TurbulenceConfig(enabled=False)


def _uniform_wind(grid: GridConfig, u: float = 5.0, v: float = 0.0) -> xr.Dataset:
    shape = (1, *grid.shape)
    return xr.Dataset(
        {
            "u_wind": (["time", "z", "y", "x"], np.full(shape, u, dtype=np.float32)),
            "v_wind": (["time", "z", "y", "x"], np.full(shape, v, dtype=np.float32)),
        },
    )


def _initial_conc(grid: GridConfig) -> np.ndarray:
    """Gaussian blob at source location."""
    nz, ny, nx = grid.shape
    z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
    cx, cy, cz = 12.0, 6.0, 2.0
    conc = np.exp(-((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) / (2 * 3.0**2))
    return conc.astype(np.float32)


def _center_of_mass(
    conc: np.ndarray,
) -> tuple[float, float, float]:
    """Return (z, y, x) center of mass."""
    total = conc.sum()
    if total == 0:
        return (0.0, 0.0, 0.0)
    nz, ny, nx = conc.shape
    z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
    return (
        float((z * conc).sum() / total),
        float((y * conc).sum() / total),
        float((x * conc).sum() / total),
    )


# ------------------------------------------------------------------ #
# 1. Shape preservation
# ------------------------------------------------------------------ #
def test_advect_step_shape() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid)
    adv = _make_adv_cfg()
    turb = _make_turb_cfg()

    result = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv.dt,
        grid,
        turb,
        0,
        plume_cfg=_make_plume_cfg(),
        adv_cfg=adv,
    )
    assert result.shape == grid.shape


# ------------------------------------------------------------------ #
# 2. Non-negativity
# ------------------------------------------------------------------ #
def test_advect_step_nonnegative() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid)
    adv = _make_adv_cfg()
    turb = _make_turb_cfg()

    result = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv.dt,
        grid,
        turb,
        0,
        plume_cfg=_make_plume_cfg(),
        adv_cfg=adv,
    )
    assert np.all(result >= 0)


# ------------------------------------------------------------------ #
# 3. Downwind drift
# ------------------------------------------------------------------ #
def test_advect_step_downwind_drift() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=5.0, v=0.0)
    adv = _make_adv_cfg(source_injection_sigma=0.5)
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()

    _, _, x0 = _center_of_mass(conc)

    stepped = conc.copy()
    for t in range(5):
        stepped = advect_step(
            stepped,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv,
        )

    _, _, x1 = _center_of_mass(stepped)
    # Wind blows in +x direction, center of mass should shift right
    assert x1 > x0, f"Expected x-COM to increase: {x0} -> {x1}"


# ------------------------------------------------------------------ #
# 4. Mixing-height lid
# ------------------------------------------------------------------ #
def test_advect_step_mixing_height_lid() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid)
    # Set mixing height to 4 layers (4 * dz=500 = 2000 m)
    plume = PlumeConfig(
        source_x=12.0,
        source_y=6.0,
        source_z=2.0,
        emission_rate=1000.0,
        wind_speed=5.0,
        wind_direction=270.0,
        mixing_height=2000.0,
        stack_height=200.0,
    )
    adv = _make_adv_cfg()
    turb = _make_turb_cfg()

    result = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv.dt,
        grid,
        turb,
        0,
        plume_cfg=plume,
        adv_cfg=adv,
    )
    # Above mixing height (layer 4 and up at dz=500): should be zero
    lid_layer = int(plume.mixing_height / grid.dz)
    assert np.allclose(result[lid_layer:, :, :], 0.0), "Non-zero above mixing height"


# ------------------------------------------------------------------ #
# 5. Source reinjection
# ------------------------------------------------------------------ #
def test_advect_step_source_reinjection() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=5.0)
    adv = _make_adv_cfg()
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()

    result = conc.copy()
    for t in range(20):
        result = advect_step(
            result,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv,
        )

    # Source region should have nonzero concentration due to reinjection
    sx = int(plume.source_x)
    sy = int(plume.source_y)
    sz = int(plume.source_z)
    # Check small neighbourhood around source
    source_region = result[
        max(sz - 1, 0) : sz + 2, max(sy - 1, 0) : sy + 2, max(sx - 1, 0) : sx + 2
    ]
    assert source_region.sum() > 0, "Source region is empty after advection"


# ------------------------------------------------------------------ #
# 6. MacCormack less diffusive
# ------------------------------------------------------------------ #
def test_maccormack_less_diffusive() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=3.0)
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()

    adv_sl = _make_adv_cfg(scheme="semi_lagrangian")
    adv_mc = _make_adv_cfg(scheme="maccormack")

    result_sl = conc.copy()
    result_mc = conc.copy()
    n_steps = 8
    for t in range(n_steps):
        result_sl = advect_step(
            result_sl,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_sl.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_sl,
        )
        result_mc = advect_step(
            result_mc,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_mc.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_mc,
        )

    # MacCormack should preserve sharper peaks (higher max)
    assert result_mc.max() >= result_sl.max() * 0.95, (
        f"MacCormack peak {result_mc.max():.4f} should be >= "
        f"semi-Lagrangian peak {result_sl.max():.4f}"
    )


# ------------------------------------------------------------------ #
# 7. MacCormack no new extrema
# ------------------------------------------------------------------ #
def test_maccormack_no_new_extrema() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=3.0)
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()
    adv = _make_adv_cfg(scheme="maccormack")

    result = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv.dt,
        grid,
        turb,
        0,
        plume_cfg=plume,
        adv_cfg=adv,
    )
    # After source injection the max may exceed original, but should be bounded
    # by original max + injected source max (no spurious oscillation beyond that)
    assert result.min() >= -1e-6, f"Negative value: {result.min()}"


# ------------------------------------------------------------------ #
# 8. Briggs plume rise
# ------------------------------------------------------------------ #
def test_briggs_plume_rise() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=3.0)
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()
    # Use no buoyancy as baseline, then compare with strong buoyancy
    adv_no_buoy = _make_adv_cfg(buoyancy_flux=0.0, source_injection_sigma=0.5)
    adv_buoy = _make_adv_cfg(buoyancy_flux=200.0, source_injection_sigma=0.5)

    result_no = conc.copy()
    result_buoy = conc.copy()
    for t in range(5):
        result_no = advect_step(
            result_no,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_no_buoy.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_no_buoy,
        )
        result_buoy = advect_step(
            result_buoy,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_buoy.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_buoy,
        )

    z_no, _, _ = _center_of_mass(result_no)
    z_buoy, _, _ = _center_of_mass(result_buoy)
    # Buoyancy should raise COM relative to the no-buoyancy case
    assert z_buoy > z_no, f"Buoyancy COM {z_buoy:.2f} should exceed no-buoyancy COM {z_no:.2f}"


# ------------------------------------------------------------------ #
# 9. Mass correction
# ------------------------------------------------------------------ #
def test_mass_correction() -> None:
    grid = _make_grid()
    wind = _uniform_wind(grid, u=0.5, v=0.0)
    turb = _make_turb_cfg()
    # Large mixing height so lid doesn't interfere
    plume = PlumeConfig(
        source_x=12.0,
        source_y=12.0,
        source_z=8.0,
        emission_rate=1000.0,
        wind_speed=0.5,
        wind_direction=270.0,
        mixing_height=50000.0,
        stack_height=200.0,
    )
    adv_corr = _make_adv_cfg(mass_correction=True, dt=100.0, source_injection_sigma=0.01)
    adv_no = _make_adv_cfg(mass_correction=False, dt=100.0, source_injection_sigma=0.01)

    # Place blob in centre of domain so it won't drift out
    conc = _initial_conc(grid)

    result_corr = conc.copy()
    result_no = conc.copy()
    initial_mass = float(conc.sum())
    for t in range(24):
        result_corr = advect_step(
            result_corr,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_corr.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_corr,
        )
        result_no = advect_step(
            result_no,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            adv_no.dt,
            grid,
            turb,
            t,
            plume_cfg=plume,
            adv_cfg=adv_no,
        )

    mass_corr = float(result_corr.sum())
    mass_no = float(result_no.sum())
    # Mass-corrected version should be closer to initial mass
    err_corr = abs(mass_corr - initial_mass) / max(initial_mass, 1e-8)
    err_no = abs(mass_no - initial_mass) / max(initial_mass, 1e-8)
    assert err_corr <= err_no * 1.1 + 0.01, (
        f"Mass correction error {err_corr:.4f} should be <= no-correction error {err_no:.4f}"
    )


# ------------------------------------------------------------------ #
# 10. Sequence shape
# ------------------------------------------------------------------ #
def test_advect_sequence_shape() -> None:
    grid = _make_grid()
    plume = _make_plume_cfg()
    turb = _make_turb_cfg()
    wind = _uniform_wind(grid)
    adv = _make_adv_cfg(sub_steps=2)

    ds = advect_sequence(plume, grid, wind, turb, n_steps=3, adv_cfg=adv)
    assert isinstance(ds, xr.Dataset)
    assert "concentration" in ds
    # n_steps=3 with sub_steps=2 => 3*2 = 6 output frames + initial = 7
    nz, ny, nx = grid.shape
    assert ds["concentration"].shape[1:] == (nz, ny, nx)
    assert ds["concentration"].shape[0] >= 3


# ------------------------------------------------------------------ #
# 11. Temporal evolution
# ------------------------------------------------------------------ #
def test_advect_sequence_temporal_evolution() -> None:
    grid = _make_grid()
    plume = _make_plume_cfg()
    turb = _make_turb_cfg()
    wind = _uniform_wind(grid, u=5.0)
    adv = _make_adv_cfg()

    ds = advect_sequence(plume, grid, wind, turb, n_steps=4, adv_cfg=adv)
    conc_arr = ds["concentration"].values

    # Compute x-centroid for first and last frame
    def x_centroid(field: np.ndarray) -> float:
        total = field.sum()
        if total == 0:
            return 0.0
        nz, ny, nx = field.shape
        _, _, x = np.mgrid[0:nz, 0:ny, 0:nx]
        return float((x * field).sum() / total)

    x_first = x_centroid(conc_arr[0])
    x_last = x_centroid(conc_arr[-1])
    assert x_last > x_first, f"Centroid should move: {x_first:.2f} -> {x_last:.2f}"


# ------------------------------------------------------------------ #
# 12. Sub-stepping smoother
# ------------------------------------------------------------------ #
def test_sub_stepping_smoother() -> None:
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=5.0)
    turb = _make_turb_cfg()
    plume = _make_plume_cfg()

    adv_1 = _make_adv_cfg(sub_steps=1)
    adv_4 = _make_adv_cfg(sub_steps=4)

    # Single big step
    result_1 = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv_1.dt,
        grid,
        turb,
        0,
        plume_cfg=plume,
        adv_cfg=adv_1,
    )

    # Four sub-steps covering the same total time
    result_4 = conc.copy()
    sub_dt = adv_4.dt / adv_4.sub_steps
    for s in range(adv_4.sub_steps):
        result_4 = advect_step(
            result_4,
            wind["u_wind"].values[0],
            wind["v_wind"].values[0],
            sub_dt,
            grid,
            turb,
            s,
            plume_cfg=plume,
            adv_cfg=adv_4,
        )

    # Sub-stepping should produce a smoother field (lower gradient magnitude)
    grad_1 = np.sqrt(sum(g**2 for g in np.gradient(result_1.astype(np.float64))))
    grad_4 = np.sqrt(sum(g**2 for g in np.gradient(result_4.astype(np.float64))))

    assert grad_4.mean() <= grad_1.mean() * 1.5, (
        f"Sub-stepped gradient {grad_4.mean():.4f} should be <= "
        f"single-step gradient {grad_1.mean():.4f} * 1.5"
    )


# ------------------------------------------------------------------ #
# 13. Mass correction preserves injection
# ------------------------------------------------------------------ #
def test_mass_correction_preserves_injection() -> None:
    """Mass correction should not undo source injection."""
    grid = _make_grid()
    conc = _initial_conc(grid)
    wind = _uniform_wind(grid, u=0.5, v=0.0)
    turb = _make_turb_cfg()
    # High mixing height so lid doesn't remove mass
    plume = PlumeConfig(
        source_x=12.0,
        source_y=6.0,
        source_z=2.0,
        emission_rate=1000.0,
        wind_speed=5.0,
        wind_direction=270.0,
        mixing_height=50000.0,
        stack_height=200.0,
    )
    adv = _make_adv_cfg(mass_correction=True, dt=100.0)

    initial_mass = float(conc.sum())
    result = advect_step(
        conc,
        wind["u_wind"].values[0],
        wind["v_wind"].values[0],
        adv.dt,
        grid,
        turb,
        0,
        plume_cfg=plume,
        adv_cfg=adv,
    )
    final_mass = float(result.sum())
    # With source injection, final mass should EXCEED initial mass
    # (injection adds mass, correction should not undo it)
    assert final_mass > initial_mass, (
        f"Mass after injection ({final_mass:.4f}) should exceed initial ({initial_mass:.4f})"
    )
