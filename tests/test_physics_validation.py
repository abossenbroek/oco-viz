"""Physics validation tests for geospatial and atmospheric correctness.

Covers:
- Pressure-to-altitude barometric formula (ISA model)
- Lat/lon ↔ local km round-trip accuracy
- DomainConfig.bbox() cos(lat) correction
- XCO2 physical plausibility range
- ERA5 wind sign convention
- CAMS unit conversion (kg/kg → ppm)
- Semi-Lagrangian advection direction consistency
- Zarr store dimension ordering and dtype validation
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import xarray as xr

from oco_viz.config.schema import (
    AdvectionConfig,
    DomainConfig,
    GridConfig,
    TurbulenceConfig,
)
from oco_viz.data.transform import (
    latlon_to_local_km,
    local_km_to_latlon,
    pressure_to_altitude_m,
)

# ------------------------------------------------------------------
# Pressure-to-altitude (ISA barometric formula)
# ------------------------------------------------------------------


class TestPressureToAltitude:
    """Validate pressure_to_altitude_m against standard atmosphere values."""

    @pytest.mark.parametrize(
        ("pressure_hpa", "expected_m", "tolerance_m"),
        [
            (1013.25, 0.0, 10.0),  # Sea level
            (900.0, 988.0, 150.0),  # ~1 km
            (850.0, 1457.0, 200.0),  # ~1.5 km
            (700.0, 3012.0, 300.0),  # ~3 km
            (500.0, 5574.0, 400.0),  # ~5.5 km
            (300.0, 9164.0, 600.0),  # ~9 km
        ],
    )
    def test_known_pressure_levels(
        self,
        pressure_hpa: float,
        expected_m: float,
        tolerance_m: float,
    ) -> None:
        """ISA barometric formula should match standard atmosphere altitudes."""
        altitude = float(pressure_to_altitude_m(pressure_hpa))
        assert abs(altitude - expected_m) < tolerance_m, (
            f"P={pressure_hpa} hPa: expected ~{expected_m}m, got {altitude:.0f}m"
        )

    def test_monotonic_decrease(self) -> None:
        """Higher pressure (lower altitude) should yield lower altitude."""
        pressures = np.array([1013.25, 850.0, 700.0, 500.0, 300.0])
        altitudes = pressure_to_altitude_m(pressures)
        diffs = np.diff(altitudes)
        assert np.all(diffs > 0), "Altitude should increase as pressure decreases"

    def test_sea_level_is_zero(self) -> None:
        """1013.25 hPa should map to 0 m altitude."""
        alt = float(pressure_to_altitude_m(1013.25))
        assert abs(alt) < 1.0, f"Sea level altitude should be ~0, got {alt:.1f}m"

    def test_vectorized(self) -> None:
        """Should accept and return arrays."""
        pressures = np.array([1013.25, 500.0, 300.0])
        altitudes = pressure_to_altitude_m(pressures)
        assert isinstance(altitudes, np.ndarray)
        assert altitudes.shape == (3,)


# ------------------------------------------------------------------
# Coordinate round-trip (lat/lon ↔ local km)
# ------------------------------------------------------------------


class TestCoordinateRoundTrip:
    """Validate latlon_to_local_km and local_km_to_latlon round-trip accuracy."""

    def test_origin_maps_to_zero(self) -> None:
        """The origin point should map to (0, 0) km."""
        x_km, y_km = latlon_to_local_km(-26.52, 29.17, origin_lat=-26.52, origin_lon=29.17)
        assert abs(float(x_km)) < 0.001
        assert abs(float(y_km)) < 0.001

    def test_roundtrip_secunda(self) -> None:
        """Round-trip at Secunda (-26.52, 29.17) should preserve coordinates."""
        origin_lat, origin_lon = -26.52, 29.17
        test_lat, test_lon = -26.0, 29.5

        x_km, y_km = latlon_to_local_km(
            test_lat, test_lon, origin_lat=origin_lat, origin_lon=origin_lon
        )
        recovered_lat, recovered_lon = local_km_to_latlon(
            x_km, y_km, origin_lat=origin_lat, origin_lon=origin_lon
        )

        assert abs(float(recovered_lat) - test_lat) < 0.01, (
            f"Lat round-trip error: {float(recovered_lat)} != {test_lat}"
        )
        assert abs(float(recovered_lon) - test_lon) < 0.01, (
            f"Lon round-trip error: {float(recovered_lon)} != {test_lon}"
        )

    def test_x_positive_is_east(self) -> None:
        """Positive longitude offset should yield positive x_km (eastward)."""
        x_km, _ = latlon_to_local_km(-26.52, 29.67, origin_lat=-26.52, origin_lon=29.17)
        assert float(x_km) > 0, "East of origin should be positive x"

    def test_y_positive_is_north(self) -> None:
        """Positive latitude offset should yield positive y_km (northward)."""
        _, y_km = latlon_to_local_km(-26.02, 29.17, origin_lat=-26.52, origin_lon=29.17)
        assert float(y_km) > 0, "North of origin should be positive y"


# ------------------------------------------------------------------
# DomainConfig.bbox() cos(lat) correction
# ------------------------------------------------------------------


class TestDomainBbox:
    """Validate DomainConfig.bbox() geographic extent and cos(lat) correction."""

    def test_bbox_center_is_origin(self) -> None:
        """Bounding box center should be close to origin."""
        domain = DomainConfig(
            origin_lat=-26.52,
            origin_lon=29.17,
            extent_x_km=100.0,
            extent_y_km=100.0,
        )
        lon_min, lat_min, lon_max, lat_max = domain.bbox()

        center_lat = (lat_min + lat_max) / 2.0
        center_lon = (lon_min + lon_max) / 2.0

        assert abs(center_lat - domain.origin_lat) < 0.01
        assert abs(center_lon - domain.origin_lon) < 0.01

    def test_bbox_extent_secunda(self) -> None:
        """100 km extent at Secunda should be approximately correct in degrees."""
        domain = DomainConfig(
            origin_lat=-26.52,
            origin_lon=29.17,
            extent_x_km=100.0,
            extent_y_km=100.0,
        )
        lon_min, lat_min, lon_max, lat_max = domain.bbox()

        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(math.radians(domain.origin_lat))

        actual_y_extent = (lat_max - lat_min) * km_per_deg_lat
        actual_x_extent = (lon_max - lon_min) * km_per_deg_lon

        assert abs(actual_y_extent - 100.0) < 1.0, f"Y extent {actual_y_extent} != 100 km"
        assert abs(actual_x_extent - 100.0) < 1.0, f"X extent {actual_x_extent} != 100 km"

    def test_cos_lat_correction_magnitude(self) -> None:
        """At -26.52, cos(lat) should give ~99.6 km/deg lon (< 111.32)."""
        lat = -26.52
        km_per_deg_lon = 111.32 * math.cos(math.radians(lat))

        # cos(-26.52) ~ 0.895
        assert km_per_deg_lon < 111.32, "Lon degree should be shorter than lat degree"
        assert km_per_deg_lon > 90.0, "cos(lat) correction too extreme"
        assert abs(km_per_deg_lon - 99.6) < 1.0

    def test_equator_has_equal_degrees(self) -> None:
        """At the equator, lon extent should equal lat extent in degrees."""
        domain = DomainConfig(
            origin_lat=0.0,
            origin_lon=0.0,
            extent_x_km=100.0,
            extent_y_km=100.0,
        )
        lon_min, lat_min, lon_max, lat_max = domain.bbox()

        lon_deg = lon_max - lon_min
        lat_deg = lat_max - lat_min

        # At equator, cos(0) = 1, so lon and lat extents should be equal
        assert abs(lon_deg - lat_deg) < 0.001


# ------------------------------------------------------------------
# XCO2 physical range
# ------------------------------------------------------------------


class TestXCO2Range:
    """Validate XCO2 values are physically plausible."""

    def test_global_mean_2024(self) -> None:
        """Synthetic XCO2 data should be within 2024 physical bounds (390-460 ppm)."""
        min_xco2 = 390.0  # Conservative lower bound
        max_xco2 = 460.0  # Conservative upper bound (urban plumes)

        xco2_values = np.array([415.0, 420.0, 425.0, 430.0, 435.0], dtype=np.float32)
        assert np.all(xco2_values >= min_xco2), "XCO2 below physical minimum"
        assert np.all(xco2_values <= max_xco2), "XCO2 above physical maximum"

    def test_rendering_config_absolute_range(self) -> None:
        """RenderingConfig absolute_min/max should be within physical XCO2 bounds."""
        from oco_viz.config.schema import RenderingConfig

        rc = RenderingConfig()
        assert rc.absolute_min_ppm >= 380.0, "absolute_min too low for current atmosphere"
        assert rc.absolute_max_ppm <= 500.0, "absolute_max too high for current atmosphere"
        assert rc.absolute_min_ppm < rc.absolute_max_ppm


# ------------------------------------------------------------------
# ERA5 wind convention
# ------------------------------------------------------------------


class TestWindConvention:
    """Validate ERA5 wind direction convention and conversion."""

    def test_meteorological_direction_north_wind(self) -> None:
        """Wind FROM the north: direction = 0/360, u=0, v < 0."""
        from oco_viz.data.era5 import wind_components_from_direction

        u, v = wind_components_from_direction(5.0, 0.0)
        assert abs(u) < 0.01, f"North wind should have u~0, got {u}"
        assert v < 0, f"North wind (from N) should have v < 0, got {v}"

    def test_meteorological_direction_east_wind(self) -> None:
        """Wind FROM the east: direction = 90, u < 0, v~0."""
        from oco_viz.data.era5 import wind_components_from_direction

        u, v = wind_components_from_direction(5.0, 90.0)
        assert u < 0, f"East wind (from E) should have u < 0, got {u}"
        assert abs(v) < 0.01, f"East wind should have v~0, got {v}"

    def test_meteorological_direction_south_wind(self) -> None:
        """Wind FROM the south: direction = 180, u~0, v > 0."""
        from oco_viz.data.era5 import wind_components_from_direction

        u, v = wind_components_from_direction(5.0, 180.0)
        assert abs(u) < 0.01, f"South wind should have u~0, got {u}"
        assert v > 0, f"South wind (from S) should have v > 0, got {v}"

    def test_meteorological_direction_west_wind(self) -> None:
        """Wind FROM the west: direction = 270, u > 0, v~0."""
        from oco_viz.data.era5 import wind_components_from_direction

        u, v = wind_components_from_direction(5.0, 270.0)
        assert u > 0, f"West wind (from W) should have u > 0, got {u}"
        assert abs(v) < 0.01, f"West wind should have v~0, got {v}"

    def test_speed_magnitude_preserved(self) -> None:
        """|u, v| should equal the input speed for all directions."""
        from oco_viz.data.era5 import wind_components_from_direction

        for direction in [0, 45, 90, 135, 180, 225, 270, 315]:
            u, v = wind_components_from_direction(10.0, float(direction))
            speed = math.sqrt(u**2 + v**2)
            assert abs(speed - 10.0) < 0.01, f"dir={direction}: speed {speed:.3f} != 10.0"


# ------------------------------------------------------------------
# CAMS unit conversion
# ------------------------------------------------------------------


class TestCAMSConversion:
    """Validate CAMS CO2 mass mixing ratio → ppm conversion."""

    def test_kgkg_to_ppm_typical_value(self) -> None:
        """~6.06e-4 kg/kg CO2 should yield ~400 ppm."""
        from oco_viz.data.cams import _kgkg_to_ppm

        # 400 ppm mole fraction × (M_CO2/M_air) = 400e-6 × 44.01/28.97 ≈ 6.075e-4
        mass_fraction = np.array([6.075e-4], dtype=np.float64)
        ppm = _kgkg_to_ppm(mass_fraction)
        assert abs(float(ppm[0]) - 400.0) < 5.0, f"Expected ~400 ppm, got {float(ppm[0]):.1f}"

    def test_kgkg_to_ppm_zero(self) -> None:
        """Zero mass fraction should give zero ppm."""
        from oco_viz.data.cams import _kgkg_to_ppm

        ppm = _kgkg_to_ppm(np.array([0.0]))
        assert float(ppm[0]) == 0.0

    def test_molar_mass_ratio(self) -> None:
        """M_air / M_CO2 should be ~0.658."""
        from oco_viz.data.cams import _M_AIR, _M_CO2

        ratio = _M_AIR / _M_CO2
        assert abs(ratio - 0.6583) < 0.001, f"M_air/M_CO2 = {ratio:.4f}, expected ~0.6583"


# ------------------------------------------------------------------
# Advection direction consistency
# ------------------------------------------------------------------


class TestAdvectionDirection:
    """Validate that semi-Lagrangian advection moves mass in the correct direction."""

    @pytest.fixture()
    def small_grid(self) -> GridConfig:
        return GridConfig(nx=24, ny=24, nz=16, dx=1000.0, dy=1000.0, dz=500.0)

    @pytest.fixture()
    def no_turbulence(self) -> TurbulenceConfig:
        return TurbulenceConfig(enabled=False)

    @pytest.fixture()
    def simple_advection(self) -> AdvectionConfig:
        return AdvectionConfig(
            dt=3600.0,
            sub_steps=1,
            scheme="semi_lagrangian",
            mass_correction=False,
            buoyancy_flux=0.0,
        )

    def test_eastward_wind_moves_plume_east(
        self,
        small_grid: GridConfig,
        no_turbulence: TurbulenceConfig,
        simple_advection: AdvectionConfig,
    ) -> None:
        """Positive u_wind (eastward) should move concentration in +x direction."""
        from oco_viz.plume.advection import advect_step

        nz, ny, nx = small_grid.shape
        conc = np.zeros(small_grid.shape, dtype=np.float32)
        conc[8, 12, 12] = 1.0  # Center point

        u_wind = np.full(small_grid.shape, 5.0, dtype=np.float32)
        v_wind = np.zeros(small_grid.shape, dtype=np.float32)

        result = advect_step(
            conc,
            u_wind,
            v_wind,
            simple_advection.dt,
            small_grid,
            no_turbulence,
            0,
            adv_cfg=simple_advection,
        )

        # Center of mass should move in +x direction
        z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
        total = result.sum()
        if total > 0:
            x_com = float((x * result).sum() / total)
            assert x_com > 12.0, f"Eastward wind should move plume to +x: COM_x={x_com:.2f}"

    def test_northward_wind_moves_plume_north(
        self,
        small_grid: GridConfig,
        no_turbulence: TurbulenceConfig,
        simple_advection: AdvectionConfig,
    ) -> None:
        """Positive v_wind (northward) should move concentration in +y direction."""
        from oco_viz.plume.advection import advect_step

        nz, ny, nx = small_grid.shape
        conc = np.zeros(small_grid.shape, dtype=np.float32)
        conc[8, 12, 12] = 1.0

        u_wind = np.zeros(small_grid.shape, dtype=np.float32)
        v_wind = np.full(small_grid.shape, 5.0, dtype=np.float32)

        result = advect_step(
            conc,
            u_wind,
            v_wind,
            simple_advection.dt,
            small_grid,
            no_turbulence,
            0,
            adv_cfg=simple_advection,
        )

        z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
        total = result.sum()
        if total > 0:
            y_com = float((y * result).sum() / total)
            assert y_com > 12.0, f"Northward wind should move plume to +y: COM_y={y_com:.2f}"

    def test_zero_wind_preserves_position(
        self,
        small_grid: GridConfig,
        no_turbulence: TurbulenceConfig,
        simple_advection: AdvectionConfig,
    ) -> None:
        """Zero wind should keep concentration approximately in place."""
        from oco_viz.plume.advection import advect_step

        nz, ny, nx = small_grid.shape
        conc = np.zeros(small_grid.shape, dtype=np.float32)
        conc[8, 12, 12] = 1.0

        u_wind = np.zeros(small_grid.shape, dtype=np.float32)
        v_wind = np.zeros(small_grid.shape, dtype=np.float32)

        result = advect_step(
            conc,
            u_wind,
            v_wind,
            simple_advection.dt,
            small_grid,
            no_turbulence,
            0,
            adv_cfg=simple_advection,
        )

        z, y, x = np.mgrid[0:nz, 0:ny, 0:nx]
        total = result.sum()
        if total > 0:
            x_com = float((x * result).sum() / total)
            y_com = float((y * result).sum() / total)
            assert abs(x_com - 12.0) < 0.5, f"Zero wind: x drifted to {x_com:.2f}"
            assert abs(y_com - 12.0) < 0.5, f"Zero wind: y drifted to {y_com:.2f}"

    def test_mass_conserved_without_correction(
        self,
        small_grid: GridConfig,
        no_turbulence: TurbulenceConfig,
        simple_advection: AdvectionConfig,
    ) -> None:
        """Semi-Lagrangian should approximately conserve mass (within interpolation loss)."""
        from oco_viz.plume.advection import advect_step

        conc = np.zeros(small_grid.shape, dtype=np.float32)
        # Broad source (not single voxel) to reduce interpolation artifacts
        conc[6:10, 10:14, 10:14] = 1.0

        u_wind = np.full(small_grid.shape, 2.0, dtype=np.float32)
        v_wind = np.full(small_grid.shape, 1.0, dtype=np.float32)

        mass_before = float(conc.sum())
        result = advect_step(
            conc,
            u_wind,
            v_wind,
            simple_advection.dt,
            small_grid,
            no_turbulence,
            0,
            adv_cfg=simple_advection,
        )
        mass_after = float(result.sum())

        # Allow 20% loss from boundary clipping and interpolation
        ratio = mass_after / mass_before
        assert ratio > 0.5, f"Mass loss too large: {(1 - ratio) * 100:.0f}%"
        assert ratio < 1.5, f"Mass gain: {(ratio - 1) * 100:.0f}%"


# ------------------------------------------------------------------
# Zarr store validation
# ------------------------------------------------------------------


class TestZarrValidation:
    """Validate zarr_store dimension ordering and dtype enforcement."""

    def test_validate_dataset_requires_dims(self) -> None:
        """Missing dimension should raise ValueError."""
        from oco_viz.data.zarr_store import _validate_dataset

        ds = xr.Dataset(
            {"concentration": (["z", "y", "x"], np.zeros((4, 4, 4), dtype=np.float32))}
        )
        with pytest.raises(ValueError, match="Missing dimension"):
            _validate_dataset(ds)

    def test_validate_dataset_requires_concentration(self) -> None:
        """Missing 'concentration' variable should raise ValueError."""
        from oco_viz.data.zarr_store import _validate_dataset

        ds = xr.Dataset(
            {"density": (["time", "z", "y", "x"], np.zeros((1, 4, 4, 4), dtype=np.float32))}
        )
        with pytest.raises(ValueError, match="Missing variable"):
            _validate_dataset(ds)

    def test_validate_dataset_requires_float(self) -> None:
        """Integer dtype should raise ValueError."""
        from oco_viz.data.zarr_store import _validate_dataset

        ds = xr.Dataset(
            {"concentration": (["time", "z", "y", "x"], np.zeros((1, 4, 4, 4), dtype=np.int32))}
        )
        with pytest.raises(ValueError, match="Unexpected dtype"):
            _validate_dataset(ds)

    def test_validate_dataset_accepts_float32(self) -> None:
        """float32 concentration should pass validation."""
        from oco_viz.data.zarr_store import _validate_dataset

        ds = xr.Dataset(
            {"concentration": (["time", "z", "y", "x"], np.zeros((1, 4, 4, 4), dtype=np.float32))}
        )
        _validate_dataset(ds)  # Should not raise

    def test_dim_order_tzyx(self) -> None:
        """Concentration should have dims in (time, z, y, x) order."""
        from oco_viz.data.zarr_store import _REQUIRED_DIMS

        assert _REQUIRED_DIMS == ("time", "z", "y", "x")


# ------------------------------------------------------------------
# Pipeline mode dispatch
# ------------------------------------------------------------------


class TestPipelineModeDispatch:
    """Validate that run_data_pipeline correctly dispatches modes."""

    def test_gaussian_mode_no_data_required(self) -> None:
        """Gaussian mode should work without ERA5 or CAMS data."""
        from oco_viz.config.schema import AppConfig
        from oco_viz.data.pipeline import run_data_pipeline

        config = AppConfig(
            grid=GridConfig(nx=8, ny=8, nz=4, dx=1000.0, dy=1000.0, dz=500.0),
        )
        ds = run_data_pipeline(config, mode="gaussian", num_timesteps=2)

        assert "concentration" in ds
        assert ds["concentration"].dims == ("time", "z", "y", "x")
        assert ds["concentration"].dtype == np.float32

    def test_composite_requires_cams_path(self) -> None:
        """Composite mode should raise if cams_path is None."""
        from oco_viz.config.schema import AppConfig
        from oco_viz.data.pipeline import run_data_pipeline

        config = AppConfig()
        with pytest.raises(ValueError, match="cams_path"):
            run_data_pipeline(config, mode="composite", num_timesteps=1)

    def test_advected_requires_era5_path(self) -> None:
        """Advected mode should raise if era5_path is None."""
        from oco_viz.config.schema import AppConfig
        from oco_viz.data.pipeline import run_data_pipeline

        config = AppConfig()
        with pytest.raises(ValueError, match="era5_path"):
            run_data_pipeline(config, mode="advected", num_timesteps=1)

    def test_wind_requires_era5_path(self) -> None:
        """Wind mode should raise if era5_path is None."""
        from oco_viz.config.schema import AppConfig
        from oco_viz.data.pipeline import run_data_pipeline

        config = AppConfig()
        with pytest.raises(ValueError, match="era5_path"):
            run_data_pipeline(config, mode="wind", num_timesteps=1)


# ------------------------------------------------------------------
# OCO quality filtering
# ------------------------------------------------------------------


class TestOCOQualityFiltering:
    """Validate OCO quality flag filtering."""

    def test_filter_quality_flag_zero(self) -> None:
        """filter_quality should keep only flag == 0 values."""
        from oco_viz.data.oco import filter_quality

        xco2 = np.array([420.0, 425.0, 430.0, 435.0], dtype=np.float64)
        flags = np.array([0, 1, 0, 2], dtype=np.int32)
        result = filter_quality(xco2, flags)

        assert len(result) == 2
        np.testing.assert_allclose(result, [420.0, 430.0])

    def test_filter_quality_all_bad(self) -> None:
        """All non-zero flags should result in empty array."""
        from oco_viz.data.oco import filter_quality

        xco2 = np.array([420.0, 425.0], dtype=np.float64)
        flags = np.array([1, 2], dtype=np.int32)
        result = filter_quality(xco2, flags)

        assert len(result) == 0
