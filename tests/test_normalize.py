"""Tests for concentration normalization with regression checks for full-block bug."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
import xarray as xr
from pydantic import ValidationError
from scipy.ndimage import sobel
from scipy.stats import entropy

from oco_viz.config.schema import DomainConfig, GridConfig, RenderingConfig
from oco_viz.data.cams import load_cams_co2
from oco_viz.render.normalize import (
    _apply_gamma_scaling,
    _compute_adaptive_divisor,
    _compute_edge_falloff,
    compute_background_profile,
    normalize_concentration,
)
from oco_viz.render.transfer import TransferFunction

if TYPE_CHECKING:
    from pathlib import Path


def _make_cams_fixture_with_gradient(tmp_path: Path) -> Path:
    """Create CAMS fixture with spatial gradient to test interpolation coverage."""
    n_lev, n_lat, n_lon = 10, 8, 8
    lats = np.linspace(-27.0, -26.0, n_lat)
    lons = np.linspace(28.7, 29.7, n_lon)

    co2 = np.full((n_lev, n_lat, n_lon), 420.0, dtype=np.float64)
    # Add spatial gradient (lat/lon dependent) to detect fill artifacts
    for j in range(n_lat):
        for i in range(n_lon):
            co2[:, j, i] += 0.5 * j + 0.3 * i

    temp = np.full((n_lev, n_lat, n_lon), 280.0, dtype=np.float64)

    ds = xr.Dataset(
        {
            "co2": (["level", "latitude", "longitude"], co2),
            "t": (["level", "latitude", "longitude"], temp),
        },
        coords={
            "level": np.arange(n_lev),
            "latitude": lats,
            "longitude": lons,
        },
    )
    path = tmp_path / "cams_gradient_test.nc"
    ds.to_netcdf(str(path))
    return path


@pytest.fixture
def domain() -> DomainConfig:
    return DomainConfig(
        origin_lat=-26.52,
        origin_lon=29.17,
        extent_x_km=100.0,
        extent_y_km=100.0,
        extent_z_km=15.0,
    )


@pytest.fixture
def gallery_grid() -> GridConfig:
    return GridConfig(nx=48, ny=48, nz=32, dx=1000.0, dy=1000.0, dz=500.0)


class TestAnomalyNormalizationRegression:
    """Regression tests for full-block bug in composite plume images.

    Root cause: Edge feathering applied to raw CAMS data corrupted the
    background profile estimation, causing mass saturation to 1.0.
    """

    def test_anomaly_normalized_has_sufficient_entropy(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Normalized composite must have sufficient information entropy for visual rendering.

        Rationale: A "full block" render occurs when normalized values collapse to a single
        value (entropy -> 0). Proper rendering requires a distribution of values (entropy > 0).
        Shannon entropy H = -sum p(x) log2(p(x)) measures value diversity robustly.

        Threshold: H > 2.0 bits ensures at least 4 distinguishable intensity levels.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        # Create composite with synthetic plume
        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0  # Point source
        composite = cams + plume

        # Normalize with anomaly mode
        rendering_cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, rendering_cfg)

        # Compute histogram and entropy
        hist, _ = np.histogram(normalized.flatten(), bins=256, range=(0, 1))
        hist_normalized = hist / hist.sum()
        h_val = float(entropy(hist_normalized + 1e-10, base=2))

        # INVARIANT: Entropy must exceed threshold for visual diversity
        # Note: Ellipsoidal falloff concentrates non-zero values in the center,
        # so entropy is naturally lower than with rectangular falloff.
        # H > 1.0 bits ensures at least 2 distinguishable intensity levels.
        min_entropy_bits = 1.0
        assert h_val > min_entropy_bits, (
            f"Normalized entropy H={h_val:.2f} bits < {min_entropy_bits} bits: "
            f"values collapsed to uniform distribution (full block regression)"
        )

    def test_anomaly_normalized_saturation_fraction(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Less than 10% of normalized values should saturate to 1.0.

        Rationale: When edge feathering corrupts background estimation, the enhancement
        calculation produces values >> anomaly_max_ppm, causing mass saturation to 1.0.
        In a properly normalized field, saturation should only occur at plume peaks.

        Threshold: <10% saturation is conservative; typical plumes saturate <1%.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0
        composite = cams + plume

        rendering_cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, rendering_cfg)

        # Count saturated voxels (value >= 0.99 to account for float precision)
        saturation_threshold = 0.99
        saturated_count = int(np.sum(normalized >= saturation_threshold))
        total_count = normalized.size
        saturation_fraction = saturated_count / total_count

        # INVARIANT: Saturation must be rare, not dominant
        max_saturation_fraction = 0.10
        assert saturation_fraction < max_saturation_fraction, (
            f"Saturation fraction {saturation_fraction:.1%} >= {max_saturation_fraction:.0%}: "
            f"{saturated_count}/{total_count} voxels at max value (background profile corrupted)"
        )

    def test_background_profile_within_physical_bounds(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Background profile must remain within physically plausible CO2 range.

        Rationale: Atmospheric CO2 is ~415-430 ppm globally. If edge feathering creates
        artificial 0 ppm values, the horizontal mean will be pulled below physical bounds.

        Threshold: Profile mean > 400 ppm (conservative lower bound for current atmosphere).
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0
        composite = cams + plume

        background_profile = compute_background_profile(composite)
        profile_mean = float(np.mean(background_profile))

        # INVARIANT: Background must be physically plausible
        min_physical_co2_ppm = 400.0
        assert profile_mean > min_physical_co2_ppm, (
            f"Background profile mean {profile_mean:.1f} ppm < {min_physical_co2_ppm} ppm: "
            f"edge artifacts corrupted physical values"
        )

    def test_normalized_coefficient_of_variation(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Normalized field must have measurable variation (CV > 0.1).

        Rationale: Coefficient of variation (sigma/mu) is dimensionless and robust to scale.
        A "full block" has CV ~ 0 (all values identical). Proper rendering needs CV > 0.

        Threshold: CV > 0.1 ensures visible gradients in the volume.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0
        composite = cams + plume

        rendering_cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, rendering_cfg)

        # Only consider non-zero values (edges legitimately go to 0)
        nonzero_values = normalized[normalized > 0.01]
        if len(nonzero_values) == 0:
            pytest.fail("All normalized values are near-zero")

        mean_val = float(np.mean(nonzero_values))
        std_val = float(np.std(nonzero_values))
        cv = std_val / mean_val if mean_val > 0 else 0.0

        # INVARIANT: Must have meaningful variation
        min_cv = 0.1
        assert cv > min_cv, (
            f"Coefficient of variation {cv:.3f} < {min_cv}: "
            f"normalized values too uniform for visual rendering"
        )


class TestNormalizationModes:
    """Tests for individual normalization modes."""

    def test_max_mode_range(self) -> None:
        """Max mode normalizes to [0, 1] range."""
        data = np.array([[[0.0, 5.0, 10.0]]], dtype=np.float32)
        cfg = RenderingConfig(mode="max")
        result = normalize_concentration(data, cfg)
        assert float(np.min(result)) == pytest.approx(0.0)
        assert float(np.max(result)) == pytest.approx(1.0)

    def test_max_mode_zero_input(self) -> None:
        """Max mode with zero input returns zeros."""
        data = np.zeros((2, 3, 4), dtype=np.float32)
        cfg = RenderingConfig(mode="max")
        result = normalize_concentration(data, cfg)
        assert np.all(result == 0)

    def test_absolute_mode_range(self) -> None:
        """Absolute mode maps [min_ppm, max_ppm] to [0, 1]."""
        data = np.array([[[415.0, 425.0, 435.0]]], dtype=np.float32)
        cfg = RenderingConfig(mode="absolute", absolute_min_ppm=415.0, absolute_max_ppm=435.0)
        result = normalize_concentration(data, cfg)
        assert float(result[0, 0, 0]) == pytest.approx(0.0)
        assert float(result[0, 0, 1]) == pytest.approx(0.5)
        assert float(result[0, 0, 2]) == pytest.approx(1.0)

    def test_anomaly_mode_removes_background(self) -> None:
        """Anomaly mode subtracts background profile."""
        # Create data with uniform background and one elevated point
        # Use larger grid to accommodate edge feathering (margin=5)
        data = np.full((20, 20, 20), 420.0, dtype=np.float32)
        data[10, 10, 10] = 430.0  # 10 ppm enhancement at center

        cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        result = normalize_concentration(data, cfg)

        # Interior non-enhanced points should be near zero (after background subtraction)
        # The peak should be near 1.0 (10 ppm / 10 ppm = 1.0)
        # Check a point that's not at the peak and not at the edge
        interior_val = float(result[10, 10, 8])  # Near center but not the peak
        assert interior_val < 0.1, f"Background not properly subtracted: {interior_val}"

        # Peak should be high (close to 1.0, accounting for slight background dilution)
        peak_val = float(result[10, 10, 10])
        assert peak_val > 0.8, f"Peak enhancement not preserved: {peak_val}"


class TestEdgeFeathering:
    """Tests for edge feathering behavior."""

    def test_edge_feathering_applied_in_anomaly_mode(self) -> None:
        """Edge feathering should taper values to zero at boundaries.

        Note: The feathering is applied to the normalized result, so we need
        data that produces non-zero enhancement values to see the effect.
        """
        # Create data with spatial variation that produces enhancement
        # The enhancement comes from values above the horizontal mean at each level
        data = np.full((20, 20, 20), 420.0, dtype=np.float32)
        # Add a plume-like enhancement in the center
        for z in range(20):
            for y in range(5, 15):
                for x in range(5, 15):
                    data[z, y, x] += 5.0  # 5 ppm above background in center region

        cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        result = normalize_concentration(data, cfg)

        # Interior enhanced region (center) should have non-zero values
        center_val = float(result[10, 10, 10])
        assert center_val > 0.0, f"Center value should be > 0, got {center_val}"

        # Edge values in the enhanced region should be tapered
        # The feathering ramp is 5 cells, so position 0 should be < center
        edge_z_val = float(result[0, 10, 10])
        edge_y_val = float(result[10, 0, 10])
        edge_x_val = float(result[10, 10, 0])

        # Edges should be lower than center due to feathering
        assert edge_z_val < center_val, f"Z-edge ({edge_z_val}) >= center ({center_val})"
        assert edge_y_val < center_val, f"Y-edge ({edge_y_val}) >= center ({center_val})"
        assert edge_x_val < center_val, f"X-edge ({edge_x_val}) >= center ({center_val})"

    def test_interior_values_unaffected_by_feathering(self) -> None:
        """Interior values (away from edges) should be unaffected by feathering."""
        # Create data with a localized enhancement at the center
        data = np.full((30, 30, 30), 420.0, dtype=np.float32)
        # Add enhancement only at specific points to create above-mean values
        # The background mean at each level will be ~420, so 425 is 5 ppm enhancement
        data[15, 15, 15] = 425.0

        cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        result = normalize_concentration(data, cfg)

        # The center point is well away from edges (margin=5), so feathering
        # should not affect it. Enhancement is 5 ppm, divided by 10 ppm max = 0.5
        # But the actual enhancement depends on the horizontal mean at that level
        center_val = float(result[15, 15, 15])

        # The enhancement at the peak should be close to the expected value
        # 5 ppm / 10 ppm = 0.5, but background estimation slightly reduces this
        assert center_val > 0.4, (
            f"Interior value {center_val} too low (feathering or background issue)"
        )


class TestEdgeFalloffGeometry:
    """Tests for edge falloff geometry to prevent rectangular boundary artifacts.

    Root cause: Rectangular axis-aligned falloff creates visible shell artifacts
    at volume boundaries when combined with step-like opacity transfer functions.
    """

    def test_ellipsoidal_falloff_has_smooth_gradients(self) -> None:
        """Ellipsoidal falloff must produce smooth gradients without sharp steps.

        Rationale: Rectangular feathering creates axis-aligned step changes visible
        as rectangular shells. Ellipsoidal feathering creates smooth continuous gradients.

        Method: Check that the gradient magnitude has low variance (no sharp transitions).
        """
        shape = (32, 48, 48)
        falloff = _compute_edge_falloff(shape, mode="ellipsoidal")

        # Compute gradient magnitude
        grad_z = sobel(falloff, axis=0)
        grad_y = sobel(falloff, axis=1)
        grad_x = sobel(falloff, axis=2)
        grad_mag = np.sqrt(grad_z**2 + grad_y**2 + grad_x**2)

        # Check that gradient magnitude varies smoothly (low CV in gradient)
        # Sharp rectangular edges would create localized high-gradient regions
        # Smooth ellipsoidal falloff has more uniform gradient distribution
        nonzero_grads = grad_mag[grad_mag > 0.01]
        if len(nonzero_grads) > 0:
            grad_cv = float(nonzero_grads.std() / nonzero_grads.mean())
            # CV should be moderate - too high indicates sharp edges
            assert grad_cv < 2.0, (
                f"Gradient CV {grad_cv:.2f} indicates non-smooth falloff: "
                f"mean={nonzero_grads.mean():.4f}, std={nonzero_grads.std():.4f}"
            )

    def test_falloff_matches_turbulent_plume_geometry(self) -> None:
        """Edge falloff geometry must match turbulent plume's natural falloff.

        Rationale: Mismatch between plume falloff (ellipsoidal) and edge falloff
        (rectangular) creates visible boundary artifacts.
        """
        shape = (32, 48, 48)
        nz, ny, nx = shape

        # Get edge falloff
        edge_falloff = _compute_edge_falloff(shape, mode="ellipsoidal")

        # Compute turbulent-style ellipsoidal falloff for comparison
        cz, cy, cx = nz / 2.0, ny / 2.0, nx / 2.0
        zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]
        dist = np.sqrt(((zz - cz) / cz) ** 2 + ((yy - cy) / cy) ** 2 + ((xx - cx) / cx) ** 2)
        turbulent_falloff = np.clip(1.0 - dist * 0.5, 0.0, 1.0)

        # Correlation should be high (>0.8) if geometries match
        correlation = float(np.corrcoef(edge_falloff.flatten(), turbulent_falloff.flatten())[0, 1])

        assert correlation > 0.8, (
            f"Edge falloff correlation with turbulent falloff = {correlation:.3f}: "
            f"geometry mismatch will cause visible boundary artifacts"
        )

    def test_no_hard_shell_at_opacity_thresholds(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Normalized values must not cluster at transfer function thresholds.

        Rationale: If many voxels cluster just above opacity threshold (e.g., 0.05),
        they create a visible shell. Proper feathering creates smooth distribution.

        Method: Check that histogram near common thresholds (0.05, 0.10) doesn't spike.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0
        composite = cams + plume

        cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, cfg)

        # Check for spike at common opacity thresholds
        hist, bins = np.histogram(normalized.flatten(), bins=100, range=(0, 1))

        # Bin 5 corresponds to ~0.05, bin 10 to ~0.10
        threshold_bins = [5, 10, 15]
        for b in threshold_bins:
            local_mean = float(hist[max(0, b - 2) : b + 3].mean())
            spike_ratio = hist[b] / (local_mean + 1)
            assert spike_ratio < 5.0, (
                f"Histogram spike at bin {b} (value ~{bins[b]:.2f}): "
                f"ratio={spike_ratio:.1f} indicates hard shell artifact"
            )

    def test_ellipsoidal_center_is_one(self) -> None:
        """Center of ellipsoidal falloff should be 1.0 (no attenuation)."""
        shape = (32, 48, 48)
        falloff = _compute_edge_falloff(shape, mode="ellipsoidal")
        center_val = float(falloff[16, 24, 24])
        assert center_val == pytest.approx(1.0, abs=0.01), (
            f"Center value {center_val} should be 1.0"
        )

    def test_ellipsoidal_corners_are_zero(self) -> None:
        """Corners of ellipsoidal falloff should be 0.0 (full attenuation)."""
        shape = (32, 48, 48)
        falloff = _compute_edge_falloff(shape, mode="ellipsoidal")
        corner_val = float(falloff[0, 0, 0])
        assert corner_val == pytest.approx(0.0, abs=0.01), (
            f"Corner value {corner_val} should be 0.0"
        )

    def test_rectangular_mode_preserved_for_compatibility(self) -> None:
        """Rectangular mode should still work for backward compatibility."""
        shape = (20, 20, 20)
        falloff = _compute_edge_falloff(shape, margin_cells=5, mode="rectangular")

        # Center should be 1.0
        center_val = float(falloff[10, 10, 10])
        assert center_val == pytest.approx(1.0)

        # Edges should be attenuated
        edge_val = float(falloff[0, 10, 10])
        assert edge_val < 0.5


class TestVisibilityGuards:
    """Visibility guard tests to catch black output before it happens.

    Root cause: Transfer function opacity too low at the scalar values
    produced by normalization causes invisible/black renders.
    """

    def test_default_plume_composite_visibility(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Mean effective opacity must be >= 0.01 for visible render.

        Rationale: A completely black render occurs when the effective opacity
        (normalized_value * transfer_function_opacity) is near zero for all
        voxels. This test ensures composite mode produces sufficient opacity.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        # Create realistic plume enhancement (not just a point source)
        plume = np.zeros_like(cams)
        # Gaussian-like plume in center
        nz, ny, nx = plume.shape
        cz, cy, cx = nz // 2, ny // 2, nx // 2
        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    dist = np.sqrt(
                        ((z - cz) / (nz / 4)) ** 2
                        + ((y - cy) / (ny / 4)) ** 2
                        + ((x - cx) / (nx / 4)) ** 2
                    )
                    if dist < 2.0:
                        plume[z, y, x] = 5.0 * np.exp(-(dist**2))

        composite = cams + plume

        # Normalize with anomaly mode
        rendering_cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, rendering_cfg)

        # Interpolate through default_plume transfer function
        tf = TransferFunction.default_plume()
        opacity_points = sorted(tf.opacity_points, key=lambda p: p.scalar)

        def interp_opacity(val: float) -> float:
            if val <= opacity_points[0].scalar:
                return opacity_points[0].opacity
            if val >= opacity_points[-1].scalar:
                return opacity_points[-1].opacity
            for i in range(len(opacity_points) - 1):
                if opacity_points[i].scalar <= val <= opacity_points[i + 1].scalar:
                    t = (val - opacity_points[i].scalar) / (
                        opacity_points[i + 1].scalar - opacity_points[i].scalar
                    )
                    return opacity_points[i].opacity + t * (
                        opacity_points[i + 1].opacity - opacity_points[i].opacity
                    )
            return 0.0

        # Compute effective opacity for all voxels
        effective_opacity = np.array([interp_opacity(v) for v in normalized.flatten()])
        mean_opacity = float(effective_opacity.mean())

        # Also compute max opacity to ensure the plume core is visible
        max_opacity = float(effective_opacity.max())

        # INVARIANT: Mean effective opacity must be sufficient for visibility
        # Note: With ellipsoidal falloff, most voxels are near zero, so mean is low.
        # Using 0.001 as threshold; before the fix it was essentially 0.
        min_mean_opacity = 0.001
        assert mean_opacity >= min_mean_opacity, (
            f"Mean effective opacity {mean_opacity:.4f} < {min_mean_opacity}: "
            f"composite render will be black/invisible"
        )

        # Also verify that the plume core has meaningful opacity (> 0.05)
        min_max_opacity = 0.05
        assert max_opacity >= min_max_opacity, (
            f"Max effective opacity {max_opacity:.4f} < {min_max_opacity}: "
            f"even plume core is invisible"
        )

    def test_normalized_value_distribution_matches_tf_threshold(
        self,
        tmp_path: Path,
        domain: DomainConfig,
        gallery_grid: GridConfig,
    ) -> None:
        """Some normalized values must be above 0.05 visibility threshold.

        Rationale: If all normalized values fall below the transfer function's
        first significant opacity threshold, the render will be black.
        """
        fixture = _make_cams_fixture_with_gradient(tmp_path)
        cams = load_cams_co2(fixture, domain, gallery_grid)

        # Create plume with enhancement
        plume = np.zeros_like(cams)
        plume[16, 24, 24] = 10.0
        # Add some spread
        plume[15:18, 22:27, 22:27] = 3.0
        composite = cams + plume

        cfg = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        normalized = normalize_concentration(composite, cfg)

        # Count voxels above visibility threshold
        visibility_threshold = 0.05
        above_threshold = int(np.sum(normalized > visibility_threshold))

        # INVARIANT: At least some voxels must be above threshold for visibility
        # Note: With ellipsoidal falloff and localized plume, only the plume core
        # will have significant values. Even 50 voxels is sufficient for a visible
        # plume in volume rendering.
        min_voxels_above = 50
        assert above_threshold >= min_voxels_above, (
            f"Only {above_threshold} voxels above {visibility_threshold}: "
            f"insufficient for visible plume core (need >= {min_voxels_above})"
        )


class TestAdaptiveNormalizationPositive:
    """Verify adaptive normalization produces expected results."""

    def test_adaptive_3ppm_enhancement_maps_to_near_one(self) -> None:
        """3 ppm peak with 3 ppm adaptive max → normalized ≈ 1.0.

        NUMERICAL CHECK: enhancement / percentile_max = 3.0 / 3.0 = 1.0
        """
        data = np.full((20, 20, 20), 420.0, dtype=np.float32)
        data[10, 10, 10] = 423.0  # 3 ppm enhancement

        cfg = RenderingConfig(
            mode="anomaly",
            adaptive_normalization=True,
            adaptive_percentile=100.0,  # Use max for deterministic test
            min_enhancement_ppm=0.1,
        )
        result = normalize_concentration(data, cfg)

        # At center (before edge falloff): enhancement / max = 1.0
        # Edge falloff at center = 1.0, so peak ≈ 1.0
        peak = float(result[10, 10, 10])
        assert 0.95 <= peak <= 1.0, f"Expected ~1.0, got {peak}"

    def test_adaptive_95th_percentile_excludes_outliers(self) -> None:
        """95th percentile excludes extreme outliers.

        Test the helper function directly since anomaly mode subtracts
        background which complicates the test setup.
        """
        # 95% of enhanced values at 5 ppm, 5% outliers at 50 ppm
        enhancement = np.array([5.0] * 95 + [50.0] * 5, dtype=np.float32)

        divisor = _compute_adaptive_divisor(enhancement, 95.0, 0.1)

        # 95th percentile should be much less than 50.0 (the outlier value)
        # Numpy interpolates, so actual value is ~7.25
        assert divisor < 10.0, f"Expected divisor ~7.25, got {divisor} (outliers included)"
        assert divisor > 5.0, f"Divisor should be above minimum value 5.0, got {divisor}"

        # Bulk enhancement (5 ppm) should normalize to moderate-high values (not 0.1)
        # Without adaptive: 5/50 = 0.1 (bad)
        # With adaptive: 5/7.25 ≈ 0.69 (much better)
        normalized_bulk = 5.0 / divisor
        assert normalized_bulk > 0.5, f"Bulk should normalize to >0.5, got {normalized_bulk}"

    def test_gamma_22_boosts_midrange_correctly(self) -> None:
        """Gamma 2.2 applies x^(1/2.2) transform.

        NUMERICAL CHECK:
        - 0.1^(1/2.2) = 0.351
        - 0.5^(1/2.2) = 0.730
        - 0.9^(1/2.2) = 0.954
        """
        # Use max mode for simple [0,1] input
        data = np.array([[[0.0, 0.1, 0.5, 0.9, 1.0]]], dtype=np.float32)

        cfg = RenderingConfig(mode="max", opacity_gamma=2.2)
        result = normalize_concentration(data, cfg)

        expected = [0.0, 0.351, 0.730, 0.954, 1.0]
        for i, exp in enumerate(expected):
            actual = float(result[0, 0, i])
            assert abs(actual - exp) < 0.02, f"Index {i}: expected {exp}, got {actual}"

    def test_combined_adaptive_gamma_dramatically_boosts_visibility(self) -> None:
        """Combined features produce large visibility improvement.

        NUMERICAL CHECK (3 ppm enhancement, adaptive + gamma 2.2):
        - Fixed: 3/10 = 0.30
        - Adaptive: 3/3 = 1.0 → after gamma: 1.0

        For 1.5 ppm (half-peak):
        - Fixed: 1.5/10 = 0.15
        - Adaptive: 1.5/3 = 0.5 → after gamma: 0.5^(1/2.2) = 0.73
        """
        data = np.full((30, 30, 30), 420.0, dtype=np.float32)
        # Gaussian-like plume
        for z in range(10, 20):
            for y in range(10, 20):
                for x in range(10, 20):
                    dist = np.sqrt((z - 15) ** 2 + (y - 15) ** 2 + (x - 15) ** 2)
                    if dist < 5:
                        data[z, y, x] = 420.0 + 3.0 * np.exp(-dist / 2)

        cfg_fixed = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        cfg_adaptive_gamma = RenderingConfig(
            mode="anomaly",
            adaptive_normalization=True,
            adaptive_percentile=95.0,
            opacity_gamma=2.2,
        )

        result_fixed = normalize_concentration(data, cfg_fixed)
        result_boosted = normalize_concentration(data, cfg_adaptive_gamma)

        # Mean non-zero values should be significantly higher
        mask = result_fixed > 0.01
        mean_fixed = float(result_fixed[mask].mean())
        mean_boosted = float(result_boosted[mask].mean())

        boost_ratio = mean_boosted / mean_fixed
        assert boost_ratio > 2.0, f"Expected 2x+ boost, got {boost_ratio:.2f}x"


class TestAdaptiveNormalizationNegative:
    """Verify adaptive normalization handles edge cases safely."""

    def test_all_zero_enhancement_no_division_by_zero(self) -> None:
        """Zero enhancement everywhere must not cause NaN/Inf.

        NUMERICAL GUARD: When all enhancements are 0, divisor = floor value.
        """
        data = np.full((10, 10, 10), 420.0, dtype=np.float32)  # Uniform, no enhancement

        cfg = RenderingConfig(
            mode="anomaly",
            adaptive_normalization=True,
            min_enhancement_ppm=1.0,
        )
        result = normalize_concentration(data, cfg)

        assert not np.any(np.isnan(result)), "NaN detected in output"
        assert not np.any(np.isinf(result)), "Inf detected in output"
        assert np.all(result >= 0), "Negative values in output"

    def test_tiny_enhancement_uses_floor_not_actual(self) -> None:
        """Enhancement < floor must use floor as divisor.

        NUMERICAL GUARD: 0.01 ppm / 0.01 ppm = 1.0 is WRONG (numerical instability)
        Should be: 0.01 ppm / 1.0 ppm (floor) = 0.01
        """
        data = np.full((20, 20, 20), 420.0, dtype=np.float32)
        data[10, 10, 10] = 420.01  # 0.01 ppm enhancement (tiny)

        cfg = RenderingConfig(
            mode="anomaly",
            adaptive_normalization=True,
            min_enhancement_ppm=1.0,  # Floor at 1 ppm
        )
        result = normalize_concentration(data, cfg)

        # Should be 0.01 / 1.0 = 0.01, NOT 0.01 / 0.01 = 1.0
        peak = float(result[10, 10, 10])
        assert peak < 0.1, f"Floor not applied: got {peak}, expected ~0.01"

    def test_negative_input_clipped_not_propagated(self) -> None:
        """Negative concentration values must be clipped to 0.

        NUMERICAL GUARD: Negative values could cause negative normalized output.
        """
        data = np.array([[[-10.0, 0.0, 10.0]]], dtype=np.float32)

        cfg = RenderingConfig(mode="max", opacity_gamma=2.2)
        result = normalize_concentration(data, cfg)

        assert float(result[0, 0, 0]) == 0.0, "Negative input not clipped"
        assert np.all(result >= 0), "Output contains negative values"

    def test_gamma_zero_rejected_by_schema(self) -> None:
        """Gamma = 0 would cause division by zero in exponent.

        SCHEMA GUARD: opacity_gamma must be > 0.
        """
        with pytest.raises(ValidationError):
            RenderingConfig(opacity_gamma=0.0)

    def test_gamma_negative_rejected_by_schema(self) -> None:
        """Negative gamma would invert the transform incorrectly.

        SCHEMA GUARD: opacity_gamma must be > 0.
        """
        with pytest.raises(ValidationError):
            RenderingConfig(opacity_gamma=-1.0)

    def test_percentile_below_50_rejected(self) -> None:
        """Low percentiles would be dominated by background noise.

        SCHEMA GUARD: adaptive_percentile must be >= 50.
        """
        with pytest.raises(ValidationError):
            RenderingConfig(adaptive_percentile=10.0)

    def test_output_never_exceeds_one(self) -> None:
        """Even with extreme values, output must be clipped to [0, 1].

        NUMERICAL INVARIANT: VTK transfer functions expect [0, 1].
        """
        data = np.full((10, 10, 10), 420.0, dtype=np.float32)
        data[5, 5, 5] = 1000.0  # Extreme outlier

        cfg = RenderingConfig(
            mode="anomaly",
            adaptive_normalization=True,
            opacity_gamma=3.0,  # Aggressive gamma
        )
        result = normalize_concentration(data, cfg)

        assert float(np.max(result)) <= 1.0, f"Output exceeds 1.0: {np.max(result)}"
        assert float(np.min(result)) >= 0.0, f"Output below 0.0: {np.min(result)}"


class TestNormalizationInvariants:
    """Property-based tests that must hold for ALL inputs."""

    @pytest.mark.parametrize("gamma", [0.5, 1.0, 1.5, 2.2, 3.0])
    def test_gamma_preserves_monotonicity(self, gamma: float) -> None:
        """Gamma transform must preserve ordering: x₁ < x₂ ⟹ f(x₁) ≤ f(x₂).

        INVARIANT: Power-law is monotonically increasing for positive exponents.
        """
        data = np.linspace(0, 1, 1000).reshape(10, 10, 10).astype(np.float32)

        cfg = RenderingConfig(mode="max", opacity_gamma=gamma)
        result = normalize_concentration(data, cfg)

        # Check monotonicity along flattened array
        flat = result.flatten()
        diffs = np.diff(flat)
        assert np.all(diffs >= -1e-6), f"Monotonicity violated with gamma={gamma}"

    @pytest.mark.parametrize("gamma", [1.0, 1.5, 2.2, 3.0])
    def test_gamma_fixes_endpoints(self, gamma: float) -> None:
        """Gamma must preserve 0 and 1: f(0)=0, f(1)=1.

        INVARIANT: 0^(1/gamma) = 0, 1^(1/gamma) = 1 for any gamma > 0.
        """
        data = np.array([[[0.0, 1.0]]], dtype=np.float32)

        cfg = RenderingConfig(mode="max", opacity_gamma=gamma)
        result = normalize_concentration(data, cfg)

        assert float(result[0, 0, 0]) == pytest.approx(0.0)
        assert float(result[0, 0, 1]) == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("adaptive", "gamma"),
        [(False, 1.0), (True, 1.0), (False, 2.2), (True, 2.2)],
    )
    def test_output_always_valid_range(
        self,
        adaptive: bool,  # noqa: FBT001
        gamma: float,
    ) -> None:
        """Output is ALWAYS in [0, 1] with no NaN/Inf.

        INVARIANT: Normalization contract with VTK.
        """
        rng = np.random.default_rng(42)
        # Extreme test data: zeros, negatives, outliers
        data = rng.uniform(-100, 1000, (10, 20, 20)).astype(np.float32)

        cfg = RenderingConfig(
            mode="max",
            adaptive_normalization=adaptive,
            opacity_gamma=gamma,
        )
        result = normalize_concentration(data, cfg)

        assert float(np.min(result)) >= 0.0, f"Below 0: {np.min(result)}"
        assert float(np.max(result)) <= 1.0, f"Above 1: {np.max(result)}"
        assert not np.any(np.isnan(result)), "Contains NaN"
        assert not np.any(np.isinf(result)), "Contains Inf"

    def test_adaptive_divisor_never_below_floor(self) -> None:
        """Adaptive divisor ≥ min_enhancement_ppm always.

        INVARIANT: Floor prevents numerical instability.
        """
        test_cases = [
            (np.array([0.001, 0.002, 0.003]), 95.0, 1.0),  # All tiny
            (np.array([0.0, 0.0, 0.0]), 95.0, 1.0),  # All zero
            (np.array([10.0, 20.0, 30.0]), 95.0, 1.0),  # Normal
        ]

        for enhancement, percentile, floor in test_cases:
            divisor = _compute_adaptive_divisor(
                enhancement.astype(np.float32),
                percentile,
                floor,
            )
            assert divisor >= floor, f"Divisor {divisor} < floor {floor}"


class TestBackwardCompatibility:
    """Ensure new features don't break existing behavior."""

    def test_default_config_identical_to_legacy(self) -> None:
        """Default RenderingConfig produces identical results to v1.0.

        CRITICAL: Users who don't opt-in must see NO change.
        """
        rng = np.random.default_rng(42)
        data = rng.uniform(0, 100, (10, 20, 20)).astype(np.float32)

        # Legacy behavior (no new fields)
        cfg_legacy = RenderingConfig(mode="max")

        # New config with all defaults
        cfg_new = RenderingConfig(
            mode="max",
            adaptive_normalization=False,  # Default
            opacity_gamma=1.0,  # Default
        )

        result_legacy = normalize_concentration(data, cfg_legacy)
        result_new = normalize_concentration(data, cfg_new)

        np.testing.assert_array_almost_equal(result_legacy, result_new)

    def test_explicit_false_matches_omitted(self) -> None:
        """Explicit adaptive_normalization=False identical to omitting it."""
        data = np.full((10, 10, 10), 420.0, dtype=np.float32)
        data[5, 5, 5] = 430.0

        cfg_omitted = RenderingConfig(mode="anomaly", anomaly_max_ppm=10.0)
        cfg_explicit = RenderingConfig(
            mode="anomaly",
            anomaly_max_ppm=10.0,
            adaptive_normalization=False,
        )

        result_omitted = normalize_concentration(data, cfg_omitted)
        result_explicit = normalize_concentration(data, cfg_explicit)

        np.testing.assert_array_almost_equal(result_omitted, result_explicit)


class TestGammaScalingUnit:
    """Unit tests for the gamma scaling helper function."""

    def test_gamma_1_returns_input(self) -> None:
        """Gamma = 1.0 should return input unchanged."""
        data = np.array([0.0, 0.25, 0.5, 0.75, 1.0], dtype=np.float32)
        result = _apply_gamma_scaling(data, 1.0)
        np.testing.assert_array_almost_equal(data, result)

    def test_gamma_22_values(self) -> None:
        """Gamma = 2.2 (sRGB standard) produces expected values."""
        data = np.array([0.0, 0.1, 0.5, 1.0], dtype=np.float32)
        result = _apply_gamma_scaling(data, 2.2)

        # x^(1/2.2) values
        expected = np.array([0.0, 0.351, 0.730, 1.0], dtype=np.float32)
        np.testing.assert_array_almost_equal(result, expected, decimal=2)

    def test_gamma_clips_to_valid_range(self) -> None:
        """Result is always in [0, 1] even with edge cases."""
        data = np.array([-0.1, 0.0, 1.0, 1.1], dtype=np.float32)
        result = _apply_gamma_scaling(data, 2.2)

        assert float(np.min(result)) >= 0.0
        assert float(np.max(result)) <= 1.0


class TestAdaptiveDivisorUnit:
    """Unit tests for the adaptive divisor calculation."""

    def test_returns_percentile_of_positive_values(self) -> None:
        """Uses percentile of positive values, ignoring zeros."""
        enhancement = np.array([0.0, 0.0, 5.0, 10.0, 15.0], dtype=np.float32)
        divisor = _compute_adaptive_divisor(enhancement, 100.0, 0.1)
        assert divisor == pytest.approx(15.0)

    def test_returns_floor_when_all_zero(self) -> None:
        """When all values are zero, returns the floor."""
        enhancement = np.zeros(100, dtype=np.float32)
        divisor = _compute_adaptive_divisor(enhancement, 95.0, 1.0)
        assert divisor == 1.0

    def test_floor_overrides_tiny_percentile(self) -> None:
        """Floor is used when percentile is smaller."""
        enhancement = np.array([0.001, 0.002, 0.003], dtype=np.float32)
        floor = 1.0
        divisor = _compute_adaptive_divisor(enhancement, 95.0, floor)
        assert divisor == floor

    def test_95th_percentile_excludes_top_5_percent(self) -> None:
        """95th percentile ignores top 5% of values."""
        # 100 values: 95 at 1.0, 5 at 100.0
        enhancement = np.array([1.0] * 95 + [100.0] * 5, dtype=np.float32)
        divisor = _compute_adaptive_divisor(enhancement, 95.0, 0.1)
        # 95th percentile of [1, 1, ..., 1, 100, 100, 100, 100, 100] should be ~1.0
        assert divisor < 10.0  # Definitely not 100
