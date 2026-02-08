"""Tests for the final assembly script (ticket 7-4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import scripts.assemble_final as asm
import xarray as xr
import yaml

from oco_viz.config import AppConfig, load_config

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_dataset(nt: int = 4, nz: int = 2, ny: int = 3, nx: int = 3) -> xr.Dataset:
    """Create a minimal concentration dataset."""
    data = np.random.default_rng(42).random((nt, nz, ny, nx), dtype=np.float32)
    return xr.Dataset(
        {"concentration": (["time", "z", "y", "x"], data)},
        coords={
            "time": np.arange(nt),
            "z": np.arange(nz, dtype=np.float64) * 500.0,
            "y": np.arange(ny, dtype=np.float64) * 1000.0,
            "x": np.arange(nx, dtype=np.float64) * 1000.0,
        },
    )


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Provide a temporary output directory."""
    return tmp_path / "hero_output"


@pytest.fixture
def hero_config() -> dict[str, Any]:
    """Load hero.yaml as overrides dict."""
    hero_path = Path(__file__).resolve().parents[1] / "configs" / "hero.yaml"
    with hero_path.open() as f:
        return yaml.safe_load(f)


@pytest.fixture
def config(hero_config: dict[str, Any]) -> AppConfig:
    """Load AppConfig with hero overrides."""
    return load_config(overrides=hero_config)


# ---------------------------------------------------------------------------
# hero.yaml tests
# ---------------------------------------------------------------------------


def test_hero_yaml_loads(config: AppConfig) -> None:
    """hero.yaml loads without error via load_config."""
    assert config is not None
    assert config.tier == "exhibition"


def test_hero_yaml_scattering(config: AppConfig) -> None:
    """Hero config has exhibition scattering settings."""
    assert config.scattering.sample_distance == 10.0
    assert config.scattering.shade is False
    assert config.scattering.global_illumination_reach == 0.8
    assert config.scattering.jittering is True


def test_hero_yaml_transfer_function(config: AppConfig) -> None:
    """Hero config uses soot_exhibition preset."""
    assert config.transfer_function.preset == "soot_exhibition"


def test_hero_yaml_output(config: AppConfig) -> None:
    """Hero config has 4K output at 24fps."""
    assert config.output.width == 3840
    assert config.output.height == 2160
    assert config.output.fps == 24


def test_hero_yaml_encoding(config: AppConfig) -> None:
    """Hero config uses prores4444 with slate."""
    assert config.encoding.codec == "prores4444"
    assert config.encoding.include_slate is True


def test_hero_yaml_sky_disabled(config: AppConfig) -> None:
    """Hero config disables sky for black background."""
    assert config.sky.enabled is False


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------

_ASM = "scripts.assemble_final"


@pytest.fixture
def mock_pipeline() -> dict[str, MagicMock]:
    """Create mock objects for all heavy pipeline imports."""
    ds = _make_dataset()
    mocks: dict[str, MagicMock] = {}

    mocks["run_data_pipeline"] = MagicMock(return_value=ds)
    mocks["write_zarr"] = MagicMock()
    mocks["read_zarr"] = MagicMock(return_value=ds)

    mock_result = MagicMock(
        rmse_ppm=1.5, fraction_within_threshold=0.8, passed=True,
    )
    mocks["compute_column_xco2"] = MagicMock(
        return_value=np.zeros((3, 3), dtype=np.float32),
    )
    mocks["compare_modeled_observed"] = MagicMock(return_value=mock_result)
    mocks["generate_validation_report"] = MagicMock(
        return_value=Path("/tmp/validation_report.json"),  # noqa: S108
    )

    batch_result = MagicMock(total_frames=4, elapsed_seconds=10.0, status="completed")
    batch_cls = MagicMock()
    batch_cls.return_value.resume.return_value = batch_result
    mocks["BatchRenderManager"] = batch_cls

    mocks["encode_video"] = MagicMock(return_value=Path("/tmp/output.mov"))  # noqa: S108
    mocks["generate_slate"] = MagicMock(
        return_value=[np.zeros((1080, 1920, 3), dtype=np.uint8)],
    )
    mocks["prepare_frames_with_slate"] = MagicMock(
        return_value=Path("/tmp/combined"),  # noqa: S108
    )

    mocks["export_td_vdb_sequence"] = MagicMock(
        return_value=[Path("/tmp/vdb/plume_000000.vdb")],  # noqa: S108
    )
    mocks["export_td_camera_chop"] = MagicMock(
        return_value=Path("/tmp/td/camera.tsv"),  # noqa: S108
    )
    mocks["export_td_manifest"] = MagicMock(
        return_value=Path("/tmp/td/td_manifest.json"),  # noqa: S108
    )
    mocks["export_point_cloud"] = MagicMock(
        return_value=Path("/tmp/td/points.csv"),  # noqa: S108
    )

    return mocks


# ---------------------------------------------------------------------------
# Stage: GENERATE
# ---------------------------------------------------------------------------


def test_stage_generate_creates_zarr(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_generate calls run_data_pipeline and write_zarr."""
    with (
        patch(f"{_ASM}.run_data_pipeline", mock_pipeline["run_data_pipeline"]),
        patch(f"{_ASM}.write_zarr", mock_pipeline["write_zarr"]),
    ):
        result = asm.stage_generate(config, output_dir, skip=False)

    assert result["skipped"] is False
    assert "zarr_path" in result
    mock_pipeline["run_data_pipeline"].assert_called_once()
    mock_pipeline["write_zarr"].assert_called_once()


def test_stage_generate_skips_existing(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_generate skips when zarr exists and skip=True."""
    zarr_path = output_dir / "concentration.zarr"
    zarr_path.mkdir(parents=True)

    with (
        patch(f"{_ASM}.run_data_pipeline", mock_pipeline["run_data_pipeline"]),
        patch(f"{_ASM}.write_zarr", mock_pipeline["write_zarr"]),
    ):
        result = asm.stage_generate(config, output_dir, skip=True)

    assert result["skipped"] is True
    mock_pipeline["run_data_pipeline"].assert_not_called()


# ---------------------------------------------------------------------------
# Stage: VALIDATE
# ---------------------------------------------------------------------------


def test_stage_validate_runs(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_validate runs validation pipeline."""
    ds = _make_dataset()
    ds["xco2_observed"] = xr.DataArray(
        np.ones((3, 3), dtype=np.float32) * 420.0, dims=["y", "x"],
    )
    mock_pipeline["read_zarr"].return_value = ds
    zarr_path = output_dir / "concentration.zarr"

    with (
        patch(f"{_ASM}.read_zarr", mock_pipeline["read_zarr"]),
        patch(f"{_ASM}.compute_column_xco2", mock_pipeline["compute_column_xco2"]),
        patch(f"{_ASM}.compare_modeled_observed", mock_pipeline["compare_modeled_observed"]),
        patch(f"{_ASM}.generate_validation_report", mock_pipeline["generate_validation_report"]),
    ):
        result = asm.stage_validate(config, zarr_path, output_dir, skip=False)

    assert result["skipped"] is False
    assert "rmse_ppm" in result


def test_stage_validate_skips_when_flagged(
    output_dir: Path,
    config: AppConfig,
) -> None:
    """stage_validate skips when skip=True."""
    zarr_path = output_dir / "concentration.zarr"
    result = asm.stage_validate(config, zarr_path, output_dir, skip=True)
    assert result["skipped"] is True


def test_stage_validate_skips_no_observed(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_validate skips comparison when no xco2_observed in dataset."""
    ds = _make_dataset()  # no xco2_observed
    mock_pipeline["read_zarr"].return_value = ds
    zarr_path = output_dir / "concentration.zarr"

    with patch(f"{_ASM}.read_zarr", mock_pipeline["read_zarr"]):
        result = asm.stage_validate(config, zarr_path, output_dir, skip=False)

    assert result["skipped"] is True
    mock_pipeline["compare_modeled_observed"].assert_not_called()


def test_stage_validate_continues_on_failure(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_validate logs warning but does not raise on low threshold."""
    ds = _make_dataset()
    ds["xco2_observed"] = xr.DataArray(
        np.ones((3, 3), dtype=np.float32) * 420.0, dims=["y", "x"],
    )
    mock_pipeline["read_zarr"].return_value = ds
    mock_pipeline["compare_modeled_observed"].return_value = MagicMock(
        rmse_ppm=10.0, fraction_within_threshold=0.3, passed=False,
    )
    zarr_path = output_dir / "concentration.zarr"

    with (
        patch(f"{_ASM}.read_zarr", mock_pipeline["read_zarr"]),
        patch(f"{_ASM}.compute_column_xco2", mock_pipeline["compute_column_xco2"]),
        patch(f"{_ASM}.compare_modeled_observed", mock_pipeline["compare_modeled_observed"]),
        patch(f"{_ASM}.generate_validation_report", mock_pipeline["generate_validation_report"]),
    ):
        result = asm.stage_validate(config, zarr_path, output_dir, skip=False)

    # Should NOT raise — just log warning and continue
    assert result["passed"] is False


# ---------------------------------------------------------------------------
# Stage: RENDER
# ---------------------------------------------------------------------------


def test_stage_render_calls_batch_manager(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_render uses BatchRenderManager in resume mode."""
    zarr_path = output_dir / "concentration.zarr"

    with patch(f"{_ASM}.BatchRenderManager", mock_pipeline["BatchRenderManager"]):
        result = asm.stage_render(config, zarr_path, output_dir)

    assert result["status"] == "completed"
    assert result["total_frames"] == 4
    mock_pipeline["BatchRenderManager"].assert_called_once()
    mock_pipeline["BatchRenderManager"].return_value.resume.assert_called_once()


# ---------------------------------------------------------------------------
# Stage: ENCODE
# ---------------------------------------------------------------------------


def test_stage_encode_two_formats(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_encode produces both ProRes master and H.264 distribution."""
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True)

    with (
        patch(f"{_ASM}.encode_video", mock_pipeline["encode_video"]),
        patch(f"{_ASM}.generate_slate", mock_pipeline["generate_slate"]),
        patch(
            f"{_ASM}.prepare_frames_with_slate",
            mock_pipeline["prepare_frames_with_slate"],
        ),
    ):
        result = asm.stage_encode(config, frames_dir, output_dir)

    assert "master_path" in result
    assert "distribution_path" in result
    # encode_video called twice (master + distribution)
    assert mock_pipeline["encode_video"].call_count == 2


def test_stage_encode_skips_existing(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_encode skips encoding when output files already exist."""
    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True)

    # Create existing output files
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "master.mov").touch()
    (output_dir / "distribution.mp4").touch()

    with (
        patch(f"{_ASM}.encode_video", mock_pipeline["encode_video"]),
        patch(f"{_ASM}.generate_slate", mock_pipeline["generate_slate"]),
        patch(
            f"{_ASM}.prepare_frames_with_slate",
            mock_pipeline["prepare_frames_with_slate"],
        ),
    ):
        result = asm.stage_encode(config, frames_dir, output_dir)

    assert result["skipped_master"] is True
    assert result["skipped_distribution"] is True


# ---------------------------------------------------------------------------
# Stage: EXPORT
# ---------------------------------------------------------------------------


def test_stage_export_creates_deliverables(
    output_dir: Path,
    config: AppConfig,
    mock_pipeline: dict[str, MagicMock],
) -> None:
    """stage_export creates VDB sequence, CHOP, manifest, point cloud."""
    zarr_path = output_dir / "concentration.zarr"

    with (
        patch(f"{_ASM}.read_zarr", mock_pipeline["read_zarr"]),
        patch(f"{_ASM}.export_td_vdb_sequence", mock_pipeline["export_td_vdb_sequence"]),
        patch(f"{_ASM}.export_td_camera_chop", mock_pipeline["export_td_camera_chop"]),
        patch(f"{_ASM}.export_td_manifest", mock_pipeline["export_td_manifest"]),
        patch(f"{_ASM}.export_point_cloud", mock_pipeline["export_point_cloud"]),
    ):
        result = asm.stage_export(config, zarr_path, output_dir)

    assert result["skipped"] is False
    assert "vdb_count" in result
    assert "manifest_path" in result
    assert "chop_path" in result
    assert "point_cloud_path" in result


def test_stage_export_skips_existing_manifest(
    output_dir: Path,
    config: AppConfig,
) -> None:
    """stage_export skips when manifest already exists."""
    zarr_path = output_dir / "concentration.zarr"
    td_dir = output_dir / "td"
    td_dir.mkdir(parents=True)
    (td_dir / "td_manifest.json").touch()

    result = asm.stage_export(config, zarr_path, output_dir)
    assert result["skipped"] is True


# ---------------------------------------------------------------------------
# Stage: REPORT
# ---------------------------------------------------------------------------


def test_stage_report_writes_json(
    output_dir: Path,
    config: AppConfig,
) -> None:
    """stage_report writes render_report.json with required keys."""
    output_dir.mkdir(parents=True, exist_ok=True)
    stage_results = {
        "generate": {"zarr_path": "/tmp/z.zarr", "skipped": False},  # noqa: S108
        "validate": {"skipped": True},
        "render": {"total_frames": 48, "status": "completed"},
        "encode": {"master_path": "/tmp/m.mov"},  # noqa: S108
        "export": {"vdb_count": 48, "skipped": False},
    }

    report_path = asm.stage_report(
        config, output_dir, stage_results, config_path="configs/hero.yaml",
    )

    assert report_path.exists()
    data = json.loads(report_path.read_text())
    assert "stages" in data
    assert "total_time" in data
    assert "config_path" in data
    assert "tier" in data


def test_stage_report_includes_file_inventory(
    output_dir: Path,
    config: AppConfig,
) -> None:
    """stage_report includes file sizes in inventory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "test.txt").write_text("hello")
    sub = output_dir / "sub"
    sub.mkdir()
    (sub / "nested.txt").write_text("world")

    report_path = asm.stage_report(
        config, output_dir, {}, config_path="configs/hero.yaml",
    )

    data = json.loads(report_path.read_text())
    assert "file_inventory" in data
    assert len(data["file_inventory"]) >= 2
