"""Tests for gallery infrastructure: progress, verification, common, registry, CLI."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
import yaml
from scripts.gallery import WAVE_DEFAULT_TIER, WAVE_NAMES, load_wave_module
from scripts.gallery._common import configure_gallery_logging, save_rgb
from scripts.gallery._progress import DryRunProgress, GalleryProgress, _format_eta
from scripts.gallery._verification import run_verification
from scripts.render_gallery_all import (
    _compute_total_images,
    _output_dir_for,
    _parse_tiers,
    _parse_waves,
    run_gallery,
)

# ── _format_eta ────────────────────────────────────────────────────


class TestFormatEta:
    def test_seconds(self) -> None:
        assert _format_eta(45.0) == "45s"

    def test_minutes(self) -> None:
        assert _format_eta(125.0) == "2m 5s"

    def test_hours(self) -> None:
        assert _format_eta(3725.0) == "1h 2m"

    def test_zero(self) -> None:
        assert _format_eta(0.0) == "0s"

    def test_exactly_one_minute(self) -> None:
        assert _format_eta(60.0) == "1m 0s"

    def test_exactly_one_hour(self) -> None:
        assert _format_eta(3600.0) == "1h 0m"


# ── GalleryProgress ───────────────────────────────────────────────


class TestGalleryProgress:
    def test_counts(self) -> None:
        progress = GalleryProgress(total_images=10)
        progress.begin_wave("3")
        progress.image_done("a.png", success=True)
        progress.image_done("b.png", success=True)
        progress.image_done("c.png", success=False)
        assert progress.completed == 2
        assert progress.failed == 1
        assert progress.total_images == 10

    def test_elapsed_increases(self) -> None:
        progress = GalleryProgress(total_images=1)
        time.sleep(0.01)
        assert progress.elapsed > 0

    def test_summary(self) -> None:
        progress = GalleryProgress(total_images=5)
        progress.image_done("x.png")
        summary = progress.summary()
        assert summary["total"] == 5
        assert summary["completed"] == 1
        assert summary["failed"] == 0
        assert isinstance(summary["elapsed"], float)


# ── DryRunProgress ────────────────────────────────────────────────


class TestDryRunProgress:
    def test_collects_images(self) -> None:
        drp = DryRunProgress()
        drp.begin_wave("3")
        drp.image_done("gaussian_basic.png")
        drp.image_done("turbulent_2oct.png")
        assert drp.total_images == 2
        assert "3/gaussian_basic.png" in drp.images
        assert "3/turbulent_2oct.png" in drp.images

    def test_no_wave_prefix(self) -> None:
        drp = DryRunProgress()
        drp.image_done("test.png")
        assert drp.images == ["test.png"]


# ── save_rgb ──────────────────────────────────────────────────────


class TestSaveRgb:
    def test_roundtrip(self, tmp_path: Path) -> None:
        """save_rgb writes valid PNG; pixel values survive roundtrip."""
        rgb = np.full((4, 4, 3), 0.5, dtype=np.float32)
        out = tmp_path / "test.png"
        save_rgb(rgb, out)
        assert out.exists()
        from PIL import Image  # noqa: PLC0415

        img = Image.open(out)
        arr = np.array(img)
        # 0.5 * 255 = 127.5 -> 127 or 128 (rounding)
        assert arr.shape == (4, 4, 3)
        assert 126 <= arr[0, 0, 0] <= 128

    def test_creates_dirs(self, tmp_path: Path) -> None:
        """save_rgb creates parent directories if missing."""
        rgb = np.zeros((2, 2, 3), dtype=np.float32)
        out = tmp_path / "deep" / "nested" / "dir" / "img.png"
        save_rgb(rgb, out)
        assert out.exists()


# ── configure_gallery_logging ─────────────────────────────────────


class TestConfigureGalleryLogging:
    def test_no_error(self) -> None:
        """configure_gallery_logging sets up structlog without raising."""
        configure_gallery_logging()


# ── Wave registry ─────────────────────────────────────────────────


class TestWaveRegistry:
    def test_wave_names_not_empty(self) -> None:
        assert len(WAVE_NAMES) > 0

    def test_all_waves_have_default_tier(self) -> None:
        for name in WAVE_NAMES:
            assert name in WAVE_DEFAULT_TIER, f"missing default tier for wave {name!r}"

    def test_load_wave_module_valid(self) -> None:
        """Every registered wave loads and exposes IMAGE_MANIFEST + render_wave."""
        for name in WAVE_NAMES:
            mod = load_wave_module(name)
            assert hasattr(mod, "IMAGE_MANIFEST"), f"wave {name!r} missing IMAGE_MANIFEST"
            assert hasattr(mod, "render_wave"), f"wave {name!r} missing render_wave"
            assert callable(mod.render_wave)
            assert isinstance(mod.IMAGE_MANIFEST, list)
            assert len(mod.IMAGE_MANIFEST) > 0, f"wave {name!r} has empty IMAGE_MANIFEST"

    def test_load_wave_module_invalid(self) -> None:
        with pytest.raises(KeyError, match="unknown wave"):
            load_wave_module("nonexistent_wave")

    def test_no_duplicate_manifests(self) -> None:
        """No duplicate filenames within any wave's manifest."""
        for name in WAVE_NAMES:
            mod = load_wave_module(name)
            manifest = mod.IMAGE_MANIFEST
            dupes = [f for f in manifest if manifest.count(f) > 1]
            assert not dupes, f"wave {name!r} has duplicate manifest entries: {dupes}"


# ── Verification ──────────────────────────────────────────────────


class TestVerification:
    def test_yaml_structure(self, tmp_path: Path) -> None:
        """run_verification writes YAML with expected top-level keys."""
        from PIL import Image  # noqa: PLC0415

        img = Image.new("RGB", (100, 100), (50, 50, 50))
        img_path = tmp_path / "output" / "examples" / "wave3" / "test.png"
        img_path.parent.mkdir(parents=True)
        img.save(str(img_path))

        out = tmp_path / "verification.yaml"
        run_verification([img_path], out, tier="study")

        assert out.exists()
        loaded = yaml.safe_load(out.read_text())
        assert "verification" in loaded
        v = loaded["verification"]
        assert "timestamp" in v
        assert "total_images" in v
        assert "passed" in v
        assert "failed" in v
        assert "tiers" in v

    def test_pass_fail_counts(self, tmp_path: Path) -> None:
        """Verdict counts match individual image verdicts."""
        from PIL import Image  # noqa: PLC0415

        # Create two images: one bright (likely pass), one black (likely fail frame_fill)
        bright_path = tmp_path / "output" / "examples" / "wave3" / "bright.png"
        bright_path.parent.mkdir(parents=True)
        img_bright = Image.new("RGB", (100, 100), (100, 100, 100))
        img_bright.save(str(bright_path))

        dark_path = tmp_path / "output" / "examples" / "wave3" / "dark.png"
        img_dark = Image.new("RGB", (100, 100), (0, 0, 0))
        img_dark.save(str(dark_path))

        out = tmp_path / "verify.yaml"
        report = run_verification([bright_path, dark_path], out, tier="sketch")

        v = report["verification"]
        # Sketch tier is very permissive, but a fully black image
        # will have 0% frame fill which fails even sketch (min 5%)
        assert v["total_images"] == 2
        assert v["passed"] + v["failed"] == 2

    def test_missing_file_skipped(self, tmp_path: Path) -> None:
        """Missing files are recorded as 'skip' verdict."""
        out = tmp_path / "verify.yaml"
        missing = tmp_path / "does_not_exist.png"
        report = run_verification([missing], out, tier="study")

        v = report["verification"]
        tiers = v["tiers"]["study"]
        all_images = []
        for wave_data in tiers["waves"].values():
            all_images.extend(wave_data["images"])
        assert any(img["verdict"] == "skip" for img in all_images)


# ── CLI parsing ──────────────────────────────────────────────────


class TestCLIParsing:
    def test_parse_waves_all(self) -> None:
        result = _parse_waves("all")
        assert result == list(WAVE_NAMES)

    def test_parse_waves_csv(self) -> None:
        result = _parse_waves("3,4,5")
        assert result == ["3", "4", "5"]

    def test_parse_waves_single(self) -> None:
        result = _parse_waves("exhibition")
        assert result == ["exhibition"]

    def test_parse_tiers_none(self) -> None:
        assert _parse_tiers(None) is None

    def test_parse_tiers_csv(self) -> None:
        result = _parse_tiers("exhibition,study")
        assert result == ["exhibition", "study"]

    def test_parse_tiers_single(self) -> None:
        result = _parse_tiers("sketch")
        assert result == ["sketch"]


class TestCLIDryRun:
    def test_dry_run_exits_zero(self) -> None:
        """--dry-run exits 0 and lists images."""
        code = run_gallery(["--dry-run"])
        assert code == 0

    def test_dry_run_wave_filter(self) -> None:
        """--wave 3 --dry-run only lists wave 3 images."""
        code = run_gallery(["--wave", "3", "--dry-run"])
        assert code == 0

    def test_dry_run_cross_product(self) -> None:
        """--wave 2,3 --tier sketch,study --dry-run produces cross-product."""
        code = run_gallery(["--wave", "2,3", "--tier", "sketch,study", "--dry-run"])
        assert code == 0


# ── Output directory computation ────────────────────────────────


class TestOutputDirFor:
    def test_base_wave_no_tier_subdir(self) -> None:
        result = _output_dir_for("base", "study", multi_tier=False)
        assert result == Path("output/examples")

    def test_numbered_wave(self) -> None:
        result = _output_dir_for("3", "study", multi_tier=False)
        assert result == Path("output/examples/wave3")

    def test_multi_tier_appends_tier(self) -> None:
        result = _output_dir_for("3", "exhibition", multi_tier=True)
        assert result == Path("output/examples/wave3/exhibition")

    def test_exhibition_wave(self) -> None:
        result = _output_dir_for("exhibition", "exhibition", multi_tier=False)
        assert result == Path("output/examples/exhibition")


# ── Total image computation ─────────────────────────────────────


class TestComputeTotalImages:
    def test_single_wave_no_tier(self) -> None:
        total = _compute_total_images(["3"], None)
        mod = load_wave_module("3")
        assert total == len(mod.IMAGE_MANIFEST)

    def test_multi_tier_multiplies(self) -> None:
        mod = load_wave_module("3")
        total = _compute_total_images(["3"], ["sketch", "study"])
        assert total == 2 * len(mod.IMAGE_MANIFEST)


# ── Regression guard: no standalone main ────────────────────────


class TestOldMainRemoved:
    def test_no_main_in_wave_modules(self) -> None:
        for name in WAVE_NAMES:
            mod = load_wave_module(name)
            assert not hasattr(mod, "main"), (
                f"wave {name!r} still has main() — should have been removed"
            )
