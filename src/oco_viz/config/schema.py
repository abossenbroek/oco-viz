"""Pydantic v2 configuration schemas with YAML layered loading."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


def _configs_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "configs"


class GridConfig(BaseModel):
    """Spatial grid configuration."""

    nx: int = Field(default=100, gt=0)
    ny: int = Field(default=100, gt=0)
    nz: int = Field(default=60, gt=0)
    dx: float = Field(default=1000.0, gt=0, description="Grid spacing in meters")
    dy: float = Field(default=1000.0, gt=0)
    dz: float = Field(default=500.0, gt=0)

    @property
    def shape(self) -> tuple[int, int, int]:
        return (self.nz, self.ny, self.nx)


class SkyConfig(BaseModel):
    """Sky gradient background configuration."""

    enabled: bool = True
    top_color: tuple[float, float, float] = (0.01, 0.01, 0.04)
    bottom_color: tuple[float, float, float] = (0.08, 0.08, 0.12)


class GroundPlaneConfig(BaseModel):
    """Translucent ground plane grid configuration."""

    enabled: bool = True
    opacity: float = Field(default=0.08, ge=0, le=1)
    grid_spacing_km: float = Field(default=10.0, gt=0)
    color: tuple[float, float, float] = (0.3, 0.3, 0.3)


class ScatteringConfig(BaseModel):
    """Volume scattering parameters for VTK."""

    global_illumination_reach: float = Field(default=0.6, ge=0, le=1)
    volumetric_scattering_blending: float = Field(default=1.8, ge=0, le=2)
    anisotropy: float = Field(default=0.35, ge=-1, le=1)
    jittering: bool = True
    shade: bool = True
    ambient: float = Field(default=0.4, ge=0, le=1)
    diffuse: float = Field(default=0.5, ge=0, le=1)
    specular: float = Field(default=0.0, ge=0, le=1)
    sample_distance: float = Field(default=0.5, gt=0)


class TurbulenceConfig(BaseModel):
    """Fractal turbulence parameters for plume detail."""

    enabled: bool = True
    octaves: int = Field(default=6, ge=1, le=10)
    lacunarity: float = Field(default=2.0, gt=1.0)
    gain: float = Field(default=0.5, gt=0, lt=1)
    amplitude: float = Field(default=0.6, ge=0, le=2.0)
    curl_strength: float = Field(default=0.3, ge=0, le=1.0)
    temporal_speed: float = Field(default=0.02, gt=0)
    seed: int = 42


class CameraConfig(BaseModel):
    """Camera rig configuration."""

    rig: str = "orbit"
    azimuth_start: float = 0.0
    azimuth_end: float = 360.0
    elevation: float = 30.0
    distance: float = 300.0
    focal_point: tuple[float, float, float] = (50.0, 50.0, 30.0)


class LightingConfig(BaseModel):
    """Tier-conditional lighting configuration."""

    mode: str = Field(default="basic", description="none, basic, or smoldering")

    @field_validator("mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        valid = {"none", "basic", "smoldering"}
        if v not in valid:
            msg = f"Lighting mode must be one of {sorted(valid)}, got {v!r}"
            raise ValueError(msg)
        return v


class TransferFunctionConfig(BaseModel):
    """Transfer function reference."""

    preset: str = "soot"
    json_path: str | None = None


class PostProcessConfig(BaseModel):
    """Post-processing pipeline configuration."""

    fog_enabled: bool = True
    fog_density: float = Field(default=0.02, ge=0)
    fog_color: tuple[float, float, float] = (0.2, 0.2, 0.2)
    tonemap: str = "aces"
    bloom_enabled: bool = True
    bloom_threshold: float = Field(default=0.8, ge=0, le=1)
    bloom_intensity: float = Field(default=0.3, ge=0)
    bloom_passes: int = Field(default=3, ge=1)
    exposure: float = Field(default=0.6, gt=0)


class OutputConfig(BaseModel):
    """Output paths and format."""

    width: int = Field(default=1920, gt=0)
    height: int = Field(default=1080, gt=0)
    frames_dir: str = "output/frames"
    video_dir: str = "output/video"
    vdb_dir: str = "output/vdb"
    fps: int = Field(default=24, gt=0)
    bit_depth: int = Field(default=16, ge=8, le=16)

    @field_validator("width", "height")
    @classmethod
    def _positive_resolution(cls, v: int) -> int:
        if v <= 0:
            msg = "Resolution must be positive"
            raise ValueError(msg)
        return v


class PlumeConfig(BaseModel):
    """Gaussian plume source configuration."""

    source_x: float = 50.0
    source_y: float = 10.0
    source_z: float = 5.0
    emission_rate: float = Field(default=1000.0, gt=0, description="kg/s")
    stability_class: str = Field(default="D")
    wind_speed: float = Field(default=5.0, gt=0, description="m/s")
    wind_direction: float = Field(default=270.0, ge=0, lt=360, description="degrees from N")
    mixing_height: float = Field(default=1500.0, gt=0, description="meters")
    stack_height: float = Field(default=200.0, ge=0, description="meters")

    @field_validator("stability_class")
    @classmethod
    def _valid_stability(cls, v: str) -> str:
        if v.upper() not in "ABCDEF":
            msg = f"Stability class must be A-F, got {v}"
            raise ValueError(msg)
        return v.upper()


class DomainConfig(BaseModel):
    """Geographic domain centered on a facility."""

    origin_lat: float = Field(default=-26.52, description="Facility latitude")
    origin_lon: float = Field(default=29.17, description="Facility longitude")
    extent_x_km: float = Field(default=100.0, gt=0, description="East-west extent in km")
    extent_y_km: float = Field(default=100.0, gt=0, description="North-south extent in km")
    extent_z_km: float = Field(default=15.0, gt=0, description="Vertical extent in km")

    def bbox(self) -> tuple[float, float, float, float]:
        """Return (lon_min, lat_min, lon_max, lat_max) bounding box.

        Approximates degree offsets from km extents using equirectangular projection.
        """
        half_x = self.extent_x_km / 2.0
        half_y = self.extent_y_km / 2.0
        km_per_deg_lat = 111.32
        km_per_deg_lon = 111.32 * math.cos(math.radians(self.origin_lat))
        dlat = half_y / km_per_deg_lat
        dlon = half_x / max(km_per_deg_lon, 1e-6)
        return (
            self.origin_lon - dlon,
            self.origin_lat - dlat,
            self.origin_lon + dlon,
            self.origin_lat + dlat,
        )


class CamsConfig(BaseModel):
    """CAMS high-resolution GHG forecast configuration."""

    dataset: str = "cams-global-ghg-forecasts"
    cache_dir: str = "data/cams"


class RenderingConfig(BaseModel):
    """Concentration normalization and rendering mode configuration.

    Modes:
        max: Simple max-normalization. Divides by maximum value. Appropriate for
            pure plume data (gaussian/turbulent) without background.
        anomaly: Subtract horizontal-mean background profile, clip to [0, anomaly_max_ppm],
            then divide by anomaly_max_ppm. Background regions become ~0 (transparent).
            Appropriate for composite data (CAMS background + plume enhancement).
        absolute: Map [absolute_min_ppm, absolute_max_ppm] linearly to [0, 1].
            Shows full atmospheric column including background.

    Adaptive normalization (anomaly mode only):
        When adaptive_normalization=True, divides by the adaptive_percentile-th
        percentile of positive enhancement values instead of anomaly_max_ppm.

    Gamma correction:
        Applied after normalization: output = normalized ** (1/gamma).
        gamma > 1 boosts mid-range values, improving visibility.
    """

    mode: str = Field(default="max", description="max, anomaly, or absolute")
    anomaly_max_ppm: float = Field(default=10.0, gt=0)
    absolute_min_ppm: float = Field(default=415.0)
    absolute_max_ppm: float = Field(default=435.0, gt=0)

    # Adaptive normalization (anomaly mode only)
    adaptive_normalization: bool = Field(
        default=False,
        description="Use percentile-based max instead of fixed anomaly_max_ppm",
    )
    adaptive_percentile: float = Field(
        default=95.0,
        ge=50.0,
        le=100.0,
        description="Percentile of positive enhancement values to use as divisor",
    )
    min_enhancement_ppm: float = Field(
        default=1.0,
        gt=0,
        description="Floor for adaptive divisor to avoid division by tiny values",
    )

    # Gamma correction
    opacity_gamma: float = Field(
        default=1.0,
        gt=0,
        description="Gamma for power-law scaling (>1 boosts mid-range values)",
    )

    @field_validator("mode")
    @classmethod
    def _valid_mode(cls, v: str) -> str:
        if v not in ("max", "anomaly", "absolute"):
            msg = f"Rendering mode must be 'max', 'anomaly', or 'absolute', got {v!r}"
            raise ValueError(msg)
        return v


class ERA5Config(BaseModel):
    """ERA5 reanalysis data configuration."""

    pressure_levels: list[int] = Field(
        default=[1000, 975, 950, 925, 900, 850, 800, 700, 600, 500],
    )
    variables: list[str] = Field(
        default=["u_component_of_wind", "v_component_of_wind"],
    )
    cache_dir: str = "data/era5"


class OCO3Config(BaseModel):
    """OCO-3 L2 Lite observation configuration."""

    collection_id: str = "C2237486636-GES_DISC"
    cache_dir: str = "data/oco3"
    quality_threshold: int = Field(default=0, ge=0, description="Max quality flag to accept")


class DataSourceConfig(BaseModel):
    """Data ingestion configuration."""

    start_date: str = "2024-01-15"
    end_date: str = "2024-01-15"
    domain: DomainConfig = Field(default_factory=DomainConfig)
    era5: ERA5Config = Field(default_factory=ERA5Config)
    oco3: OCO3Config = Field(default_factory=OCO3Config)


class AnnotationConfig(BaseModel):
    """Text annotation overlay configuration."""

    show_timestamp: bool = True
    show_facility: bool = True
    show_credits: bool = True
    show_scale_bar: bool = True
    font_size: int = Field(default=18, ge=8, le=72)
    facility_name: str = "Sasol Secunda"
    text_color: tuple[float, float, float] = (0.9, 0.9, 0.9)
    panel_opacity: float = Field(default=0.4, ge=0, le=1)


class OverlayConfig(BaseModel):
    """OCO observation overlay configuration."""

    enabled: bool = True
    dot_scale: float = Field(default=0.5, gt=0)
    max_enhancement_ppm: float = Field(default=10.0, gt=0)
    background_ppm: float = Field(default=415.0, gt=0)
    colormap: str = Field(default="turbo")
    emissive_brightness: float = Field(default=1.5, ge=0)

    @field_validator("colormap")
    @classmethod
    def _valid_colormap(cls, v: str) -> str:
        valid = {"turbo", "inferno", "RdYlBu_r", "hot", "plasma"}
        if v not in valid:
            msg = f"Colormap must be one of {sorted(valid)}, got {v!r}"
            raise ValueError(msg)
        return v


class AdvectionConfig(BaseModel):
    """Semi-Lagrangian advection configuration."""

    dt: float = Field(default=3600.0, gt=0, description="Advection timestep in seconds")
    sub_steps: int = Field(default=4, ge=1, le=16, description="Sub-steps per timestep")
    source_injection_sigma: float = Field(
        default=2.0, gt=0, description="Source injection spread in grid cells"
    )
    scheme: str = Field(
        default="maccormack",
        description="Advection scheme: semi_lagrangian or maccormack",
    )
    mass_correction: bool = Field(default=True, description="Apply per-step mass correction")
    buoyancy_flux: float = Field(
        default=50.0, ge=0, description="Briggs buoyancy flux parameter (m^4/s^3)"
    )

    @field_validator("scheme")
    @classmethod
    def _valid_scheme(cls, v: str) -> str:
        valid = {"semi_lagrangian", "maccormack"}
        if v not in valid:
            msg = f"Advection scheme must be one of {sorted(valid)}, got {v!r}"
            raise ValueError(msg)
        return v


class ValidationConfig(BaseModel):
    """Column XCO2 validation configuration."""

    background_ppm: float = Field(default=415.0, gt=0, description="Background CO2 in ppm")
    threshold_fraction: float = Field(
        default=0.20, gt=0, le=1, description="Fraction threshold for pass/fail"
    )
    pass_criterion: float = Field(
        default=0.50, gt=0, le=1, description="Min fraction within threshold to pass"
    )
    pressure_weighted: bool = Field(
        default=True, description="Use pressure-weighted column average"
    )


class AppConfig(BaseModel):
    """Top-level application configuration."""

    tier: str = "study"
    grid: GridConfig = Field(default_factory=GridConfig)
    sky: SkyConfig = Field(default_factory=SkyConfig)
    ground_plane: GroundPlaneConfig = Field(default_factory=GroundPlaneConfig)
    scattering: ScatteringConfig = Field(default_factory=ScatteringConfig)
    lighting: LightingConfig = Field(default_factory=LightingConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    transfer_function: TransferFunctionConfig = Field(default_factory=TransferFunctionConfig)
    postprocess: PostProcessConfig = Field(default_factory=PostProcessConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    plume: PlumeConfig = Field(default_factory=PlumeConfig)
    turbulence: TurbulenceConfig = Field(default_factory=TurbulenceConfig)
    advection: AdvectionConfig = Field(default_factory=AdvectionConfig)
    cams: CamsConfig = Field(default_factory=CamsConfig)
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)
    annotations: AnnotationConfig = Field(default_factory=AnnotationConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)

    @field_validator("tier")
    @classmethod
    def _valid_tier(cls, v: str) -> str:
        valid = {"sketch", "study", "exhibition"}
        if v not in valid:
            msg = f"Tier must be one of {sorted(valid)}, got {v!r}"
            raise ValueError(msg)
        return v


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge overlay into base."""
    result = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    profile: str | None = None,
    *,
    overrides: dict[str, Any] | None = None,
    configs_dir: Path | None = None,
    tier: str | None = None,
) -> AppConfig:
    """Load config from base.yaml, optionally overlay a profile and tier, then apply overrides.

    Loading order: base.yaml -> profile overlay -> tier overlay -> runtime overrides.
    """
    cdir = configs_dir or _configs_dir()
    base_path = cdir / "base.yaml"

    data: dict[str, Any] = {}
    if base_path.exists():
        with base_path.open() as f:
            loaded = yaml.safe_load(f)
            if loaded:
                data = loaded

    if profile:
        profile_path = cdir / f"{profile}.yaml"
        if profile_path.exists():
            with profile_path.open() as f:
                overlay = yaml.safe_load(f)
                if overlay:
                    data = _deep_merge(data, overlay)

    # Determine tier: explicit parameter > overrides > data > default
    effective_tier = tier or (overrides or {}).get("tier") or data.get("tier", "study")
    tier_path = cdir / "tiers" / f"{effective_tier}.yaml"
    if tier_path.exists():
        with tier_path.open() as f:
            tier_overlay = yaml.safe_load(f)
            if tier_overlay:
                data = _deep_merge(data, tier_overlay)
    data["tier"] = effective_tier

    if overrides:
        data = _deep_merge(data, overrides)

    return AppConfig.model_validate(data)
