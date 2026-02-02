"""Pydantic v2 configuration schemas with YAML layered loading."""

from __future__ import annotations

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

    global_illumination_reach: float = Field(default=1.0, ge=0, le=1)
    volumetric_scattering_blending: float = Field(default=1.8, ge=0, le=2)
    anisotropy: float = Field(default=0.75, ge=-1, le=1)
    jittering: bool = True
    shade: bool = True
    ambient: float = Field(default=0.05, ge=0, le=1)
    diffuse: float = Field(default=0.85, ge=0, le=1)
    specular: float = Field(default=0.1, ge=0, le=1)
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


class TransferFunctionConfig(BaseModel):
    """Transfer function reference."""

    preset: str = "default_plume"
    json_path: str | None = None


class PostProcessConfig(BaseModel):
    """Post-processing pipeline configuration."""

    fog_density: float = Field(default=0.02, ge=0)
    fog_color: tuple[float, float, float] = (0.7, 0.75, 0.85)
    tonemap: str = "aces"
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


class AppConfig(BaseModel):
    """Top-level application configuration."""

    grid: GridConfig = Field(default_factory=GridConfig)
    sky: SkyConfig = Field(default_factory=SkyConfig)
    ground_plane: GroundPlaneConfig = Field(default_factory=GroundPlaneConfig)
    scattering: ScatteringConfig = Field(default_factory=ScatteringConfig)
    camera: CameraConfig = Field(default_factory=CameraConfig)
    transfer_function: TransferFunctionConfig = Field(default_factory=TransferFunctionConfig)
    postprocess: PostProcessConfig = Field(default_factory=PostProcessConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    plume: PlumeConfig = Field(default_factory=PlumeConfig)
    turbulence: TurbulenceConfig = Field(default_factory=TurbulenceConfig)
    data_source: DataSourceConfig = Field(default_factory=DataSourceConfig)


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
) -> AppConfig:
    """Load config from base.yaml, optionally overlay a profile, then apply overrides."""
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

    if overrides:
        data = _deep_merge(data, overrides)

    return AppConfig.model_validate(data)
