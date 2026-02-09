"""Tests for multi-codec video encoding and title slate (ticket 7-2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from oco_viz.config.schema import AppConfig, EncodingConfig
from oco_viz.sequencer.encode import (
    encode_video,
    generate_slate,
    prepare_frames_with_slate,
    validate_ffmpeg_codec,
)

if TYPE_CHECKING:
    from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_test_frames(frames_dir: Path, n: int = 5, size: int = 64) -> None:
    """Create small test PNG frames."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        arr = np.random.default_rng(i).integers(0, 255, (size, size, 3), dtype=np.uint8)
        Image.fromarray(arr).save(frames_dir / f"frame_{i:06d}.png")


def _default_config(**encoding_overrides: object) -> AppConfig:
    """Build an AppConfig with optional encoding overrides."""
    enc = EncodingConfig(**encoding_overrides)  # type: ignore[arg-type]
    return AppConfig(encoding=enc)


# ===========================================================================
# EncodingConfig validation
# ===========================================================================


class TestEncodingConfigValidation:
    """Validation rules for EncodingConfig."""

    def test_defaults(self) -> None:
        cfg = EncodingConfig()
        assert cfg.codec == "h264"
        assert cfg.crf == 18
        assert cfg.pixel_format is None
        assert cfg.include_slate is True
        assert cfg.slate_duration_s == 3.0

    @pytest.mark.parametrize("codec", ["h264", "h265", "prores4444", "dnxhr_hqx", "png"])
    def test_valid_codecs(self, codec: str) -> None:
        cfg = EncodingConfig(codec=codec)
        assert cfg.codec == codec

    def test_invalid_codec_raises(self) -> None:
        with pytest.raises(ValidationError, match="Codec must be one of"):
            EncodingConfig(codec="vp9")

    def test_crf_lower_bound(self) -> None:
        cfg = EncodingConfig(crf=0)
        assert cfg.crf == 0

    def test_crf_upper_bound(self) -> None:
        cfg = EncodingConfig(crf=63)
        assert cfg.crf == 63

    def test_crf_below_range(self) -> None:
        with pytest.raises(ValidationError):
            EncodingConfig(crf=-1)

    def test_crf_above_range(self) -> None:
        with pytest.raises(ValidationError):
            EncodingConfig(crf=64)

    def test_encoding_wired_into_appconfig(self) -> None:
        config = AppConfig()
        assert isinstance(config.encoding, EncodingConfig)
        assert config.encoding.codec == "h264"


# ===========================================================================
# Codec dispatch (mock subprocess)
# ===========================================================================


class TestCodecDispatch:
    """encode_video dispatches correct ffmpeg commands per codec."""

    def test_h264_args(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mp4"
        enc = EncodingConfig(codec="h264", crf=20)

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24, encoding=enc)

        cmd = mock_run.call_args[0][0]
        assert "-c:v" in cmd
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "libx264"
        assert "-pix_fmt" in cmd
        pf_idx = cmd.index("-pix_fmt")
        assert cmd[pf_idx + 1] == "yuv420p"
        assert "-crf" in cmd
        crf_idx = cmd.index("-crf")
        assert cmd[crf_idx + 1] == "20"

    def test_h265_args(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mp4"
        enc = EncodingConfig(codec="h265", crf=22)

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24, encoding=enc)

        cmd = mock_run.call_args[0][0]
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "libx265"
        assert "-crf" in cmd

    def test_prores4444_args(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mov"
        enc = EncodingConfig(codec="prores4444")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24, encoding=enc)

        cmd = mock_run.call_args[0][0]
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "prores_ks"
        assert "-pix_fmt" in cmd
        pf_idx = cmd.index("-pix_fmt")
        assert cmd[pf_idx + 1] == "yuva444p10le"
        # ProRes does NOT support CRF
        assert "-crf" not in cmd

    def test_dnxhr_hqx_args(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mxf"
        enc = EncodingConfig(codec="dnxhr_hqx")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24, encoding=enc)

        cmd = mock_run.call_args[0][0]
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "dnxhd"
        assert "-pix_fmt" in cmd
        pf_idx = cmd.index("-pix_fmt")
        assert cmd[pf_idx + 1] == "yuv422p10le"
        assert "-crf" not in cmd

    def test_png_codec_copies_frames(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir, n=3)
        output_dir = tmp_path / "png_out"
        enc = EncodingConfig(codec="png")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            result = encode_video(frames_dir, output_dir, fps=24, encoding=enc)

        # No ffmpeg call for PNG
        mock_run.assert_not_called()
        assert result.is_dir()
        assert len(list(result.glob("*.png"))) == 3

    def test_pixel_format_override(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mp4"
        enc = EncodingConfig(codec="h264", pixel_format="yuv444p")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24, encoding=enc)

        cmd = mock_run.call_args[0][0]
        pf_idx = cmd.index("-pix_fmt")
        assert cmd[pf_idx + 1] == "yuv444p"

    def test_ffmpeg_failure_raises(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mp4"
        enc = EncodingConfig(codec="h264")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="encoder error")
            with pytest.raises(RuntimeError, match="ffmpeg failed"):
                encode_video(frames_dir, output, fps=24, encoding=enc)

    def test_auto_correct_extension(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        # Request .mp4 but use prores — should auto-correct to .mov
        output = tmp_path / "out.mp4"
        enc = EncodingConfig(codec="prores4444")

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = encode_video(frames_dir, output, fps=24, encoding=enc)

        assert result.suffix == ".mov"

    def test_backward_compat_no_encoding(self, tmp_path: Path) -> None:
        """encoding=None produces same H.264 behavior as before."""
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir)
        output = tmp_path / "out.mp4"

        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            encode_video(frames_dir, output, fps=24)

        cmd = mock_run.call_args[0][0]
        idx = cmd.index("-c:v")
        assert cmd[idx + 1] == "libx264"
        assert "-pix_fmt" in cmd
        assert "-crf" in cmd


# ===========================================================================
# validate_ffmpeg_codec
# ===========================================================================


class TestValidateFfmpegCodec:
    """validate_ffmpeg_codec checks ffmpeg codec availability."""

    def test_png_always_true(self) -> None:
        assert validate_ffmpeg_codec("png") is True

    def test_ffmpeg_not_installed(self) -> None:
        with patch("oco_viz.sequencer.encode.subprocess.run", side_effect=FileNotFoundError):
            assert validate_ffmpeg_codec("h264") is False

    def test_codec_available(self) -> None:
        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="DEV.LS libx264")
            assert validate_ffmpeg_codec("h264") is True

    def test_codec_unavailable(self) -> None:
        with patch("oco_viz.sequencer.encode.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="DEV.LS libx265")
            assert validate_ffmpeg_codec("h264") is False


# ===========================================================================
# Slate generation
# ===========================================================================


class TestSlateGeneration:
    """generate_slate produces correct title card frames."""

    def test_frame_count(self) -> None:
        config = _default_config(slate_duration_s=3.0)
        frames = generate_slate(config)
        expected = config.output.fps * 3  # 24 * 3 = 72
        assert len(frames) == expected

    def test_frame_shape(self) -> None:
        config = _default_config()
        frames = generate_slate(config)
        for f in frames:
            assert f.shape == (config.output.height, config.output.width, 3)
            assert f.dtype == np.uint8

    def test_all_frames_identical(self) -> None:
        config = _default_config(slate_duration_s=1.0)
        frames = generate_slate(config)
        assert len(frames) > 1
        for f in frames[1:]:
            np.testing.assert_array_equal(frames[0], f)

    def test_frames_not_all_black(self) -> None:
        config = _default_config()
        frames = generate_slate(config)
        # At least some pixels should be non-zero (text + gradient bg)
        assert frames[0].sum() > 0


# ===========================================================================
# Slate prepend
# ===========================================================================


class TestSlatePrepend:
    """prepare_frames_with_slate merges slate + render frames."""

    def test_combined_count(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir, n=5)
        slate_frames = [np.zeros((64, 64, 3), dtype=np.uint8) for _ in range(3)]
        work_dir = tmp_path / "work"
        result = prepare_frames_with_slate(frames_dir, slate_frames, work_dir)
        total = len(list(result.glob("frame_*.png")))
        assert total == 3 + 5

    def test_contiguous_numbering(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir, n=3)
        slate_frames = [np.zeros((64, 64, 3), dtype=np.uint8) for _ in range(2)]
        work_dir = tmp_path / "work"
        result = prepare_frames_with_slate(frames_dir, slate_frames, work_dir)
        expected_names = {f"frame_{i:06d}.png" for i in range(5)}
        actual_names = {p.name for p in result.glob("frame_*.png")}
        assert actual_names == expected_names

    def test_original_frames_unmodified(self, tmp_path: Path) -> None:
        frames_dir = tmp_path / "frames"
        _create_test_frames(frames_dir, n=3)
        original_files = set(frames_dir.iterdir())
        slate_frames = [np.zeros((64, 64, 3), dtype=np.uint8)]
        work_dir = tmp_path / "work"
        prepare_frames_with_slate(frames_dir, slate_frames, work_dir)
        assert set(frames_dir.iterdir()) == original_files
