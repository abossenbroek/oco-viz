"""End-to-end assembly script: generate -> validate -> render -> encode -> export -> report."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy-import helpers
# ---------------------------------------------------------------------------
# Heavy modules are imported once on first use and cached in module globals.
# Tests can patch these globals via ``unittest.mock.patch``.


def _import_data_pipeline() -> Any:
    from oco_viz.data import pipeline  # noqa: PLC0415

    return pipeline.run_data_pipeline


def _import_write_zarr() -> Any:
    from oco_viz.data import zarr_store  # noqa: PLC0415

    return zarr_store.write_zarr


def _import_read_zarr() -> Any:
    from oco_viz.data import zarr_store  # noqa: PLC0415

    return zarr_store.read_zarr


def _import_validation() -> tuple[Any, Any, Any]:
    from oco_viz.data import validation  # noqa: PLC0415

    return (
        validation.compute_column_xco2,
        validation.compare_modeled_observed,
        validation.generate_validation_report,
    )


def _import_batch() -> Any:
    from oco_viz.sequencer import batch  # noqa: PLC0415

    return batch.BatchRenderManager


def _import_encode() -> tuple[Any, Any, Any]:
    from oco_viz.sequencer import encode  # noqa: PLC0415

    return encode.encode_video, encode.generate_slate, encode.prepare_frames_with_slate


def _import_export() -> tuple[Any, Any, Any, Any]:
    from oco_viz.sequencer import td_export  # noqa: PLC0415

    return (
        td_export.export_td_vdb_sequence,
        td_export.export_td_camera_chop,
        td_export.export_td_manifest,
        td_export.export_point_cloud,
    )


# Module-level callables — populated lazily, patchable by tests.
run_data_pipeline: Any = None
write_zarr: Any = None
read_zarr: Any = None
compute_column_xco2: Any = None
compare_modeled_observed: Any = None
generate_validation_report: Any = None
BatchRenderManager: Any = None
encode_video: Any = None
generate_slate: Any = None
prepare_frames_with_slate: Any = None
export_td_vdb_sequence: Any = None
export_td_camera_chop: Any = None
export_td_manifest: Any = None
export_point_cloud: Any = None


def _ensure_generate() -> None:
    global run_data_pipeline, write_zarr  # noqa: PLW0603
    if run_data_pipeline is None:
        run_data_pipeline = _import_data_pipeline()
        write_zarr = _import_write_zarr()


def _ensure_validate() -> None:
    global read_zarr, compute_column_xco2  # noqa: PLW0603
    global compare_modeled_observed, generate_validation_report
    if read_zarr is None:
        read_zarr = _import_read_zarr()
        compute_column_xco2, compare_modeled_observed, generate_validation_report = (
            _import_validation()
        )


def _ensure_render() -> None:
    global BatchRenderManager  # noqa: PLW0603
    if BatchRenderManager is None:
        BatchRenderManager = _import_batch()


def _ensure_encode() -> None:
    global encode_video, generate_slate, prepare_frames_with_slate
    if encode_video is None:
        encode_video, generate_slate, prepare_frames_with_slate = _import_encode()


def _ensure_export() -> None:
    global export_td_vdb_sequence, export_td_camera_chop
    global export_td_manifest, export_point_cloud
    if export_td_vdb_sequence is None:
        (
            export_td_vdb_sequence,
            export_td_camera_chop,
            export_td_manifest,
            export_point_cloud,
        ) = _import_export()


# ---------------------------------------------------------------------------
# Stage 1: GENERATE
# ---------------------------------------------------------------------------


def stage_generate(
    config: Any,
    output_dir: Path,
    *,
    skip: bool = False,
) -> dict[str, Any]:
    """Generate advected plume data and write to Zarr."""
    _ensure_generate()
    zarr_path = output_dir / "concentration.zarr"

    if skip and zarr_path.exists():
        logger.info("GENERATE: skipped (zarr exists at %s)", zarr_path)
        return {"zarr_path": str(zarr_path), "timesteps": 0, "skipped": True}

    # Calculate frame count from date range with fallback
    num_frames = 48
    try:
        from datetime import datetime  # noqa: PLC0415

        start = datetime.strptime(config.data_source.start_date, "%Y-%m-%d")  # noqa: DTZ007
        end = datetime.strptime(config.data_source.end_date, "%Y-%m-%d")  # noqa: DTZ007
        days = max((end - start).days, 1)
        num_frames = days * config.output.fps
    except (ValueError, AttributeError):
        logger.warning("Could not parse date range, using %d frames", num_frames)

    ds = run_data_pipeline(config, mode="advected", num_timesteps=num_frames)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_zarr(ds, zarr_path)

    logger.info("GENERATE: wrote %d timesteps to %s", ds.sizes["time"], zarr_path)
    return {
        "zarr_path": str(zarr_path),
        "timesteps": int(ds.sizes["time"]),
        "skipped": False,
    }


# ---------------------------------------------------------------------------
# Stage 2: VALIDATE
# ---------------------------------------------------------------------------


def stage_validate(
    config: Any,
    zarr_path: Path,
    output_dir: Path,
    *,
    skip: bool = False,
) -> dict[str, Any]:
    """Run column XCO2 validation against observations."""
    if skip:
        logger.info("VALIDATE: skipped (--skip-validation)")
        return {"skipped": True}

    _ensure_validate()
    ds = read_zarr(zarr_path)

    if "xco2_observed" not in ds:
        logger.warning("VALIDATE: no xco2_observed in dataset — skipping comparison")
        return {"skipped": True}

    conc_3d = ds["concentration"].isel(time=-1).values
    modeled_column = compute_column_xco2(conc_3d, config.grid, config.validation)

    observed = ds["xco2_observed"].values
    result = compare_modeled_observed(modeled_column, observed, config.validation)

    val_dir = output_dir / "validation"
    report_path = generate_validation_report(result, val_dir)

    if result.fraction_within_threshold < 0.5:
        logger.warning(
            "VALIDATE: low agreement (%.1f%% within threshold) — continuing",
            result.fraction_within_threshold * 100,
        )

    return {
        "report_path": str(report_path),
        "rmse_ppm": result.rmse_ppm,
        "passed": result.passed,
        "skipped": False,
    }


# ---------------------------------------------------------------------------
# Stage 3: RENDER
# ---------------------------------------------------------------------------


def stage_render(
    config: Any,
    zarr_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Render frames via BatchRenderManager with resume support."""
    _ensure_render()
    frames_dir = output_dir / "frames"

    t_start = time.monotonic()
    manager = BatchRenderManager(
        zarr_path=zarr_path,
        output_dir=frames_dir,
        config=config,
    )
    result = manager.resume()
    elapsed = time.monotonic() - t_start

    logger.info(
        "RENDER: %s — %d frames in %.1fs",
        result.status,
        result.total_frames,
        elapsed,
    )
    return {
        "frames_dir": str(frames_dir),
        "total_frames": result.total_frames,
        "elapsed_seconds": elapsed,
        "status": result.status,
    }


# ---------------------------------------------------------------------------
# Stage 4: ENCODE
# ---------------------------------------------------------------------------


def stage_encode(
    config: Any,
    frames_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Encode ProRes 4444 master and H.264 distribution from frames."""
    _ensure_encode()
    output_dir.mkdir(parents=True, exist_ok=True)

    master_path = output_dir / "master.mov"
    dist_path = output_dir / "distribution.mp4"

    skipped_master = master_path.exists()
    skipped_distribution = dist_path.exists()

    # Prepare slate + frames if needed
    encode_dir = frames_dir
    if config.encoding.include_slate and (not skipped_master or not skipped_distribution):
        slate_frames = generate_slate(config)
        work_dir = output_dir / "_slate_work"
        encode_dir = prepare_frames_with_slate(frames_dir, slate_frames, work_dir)

    # ProRes 4444 master
    if not skipped_master:
        prores_enc = config.encoding.model_copy(update={"codec": "prores4444"})
        encode_video(
            encode_dir,
            master_path,
            fps=config.output.fps,
            encoding=prores_enc,
        )
        logger.info("ENCODE: master → %s", master_path)

    # H.264 distribution
    if not skipped_distribution:
        h264_enc = config.encoding.model_copy(update={"codec": "h264"})
        encode_video(
            encode_dir,
            dist_path,
            fps=config.output.fps,
            encoding=h264_enc,
        )
        logger.info("ENCODE: distribution → %s", dist_path)

    return {
        "master_path": str(master_path),
        "distribution_path": str(dist_path),
        "skipped_master": skipped_master,
        "skipped_distribution": skipped_distribution,
    }


# ---------------------------------------------------------------------------
# Stage 5: EXPORT
# ---------------------------------------------------------------------------


def stage_export(
    config: Any,
    zarr_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Export VDB sequence, camera CHOP, manifest, and point cloud."""
    vdb_dir = output_dir / "vdb"
    td_dir = output_dir / "td"
    manifest_path = td_dir / "td_manifest.json"

    if manifest_path.exists():
        logger.info("EXPORT: skipped (manifest exists at %s)", manifest_path)
        return {"skipped": True}

    _ensure_export()
    _ensure_validate()

    ds = read_zarr(zarr_path)
    conc = ds["concentration"].values
    frames = [conc[i] for i in range(conc.shape[0])]
    n_frames = len(frames)

    # VDB sequence
    velocities = None
    if "u_wind" in ds and "v_wind" in ds:
        u = ds["u_wind"].values
        v = ds["v_wind"].values
        w = np.zeros_like(u)
        velocities = [(u[i], v[i], w[i]) for i in range(n_frames)]

    vdb_paths = export_td_vdb_sequence(frames, velocities, config, vdb_dir)

    # Camera CHOP
    from oco_viz.render.camera_path import reveal_path  # noqa: PLC0415

    cam = reveal_path(
        config.camera.focal_point,
        config.camera.distance,
    )
    chop_path = export_td_camera_chop(cam, td_dir, n_frames)

    # Manifest
    manifest_result = export_td_manifest(config, td_dir, n_frames)

    # Point cloud from last frame
    pc_path = export_point_cloud(
        frames[-1],
        config.grid,
        td_dir / "points.csv",
    )

    logger.info("EXPORT: %d VDB frames, CHOP, manifest, point cloud", len(vdb_paths))
    return {
        "vdb_count": len(vdb_paths),
        "manifest_path": str(manifest_result),
        "chop_path": str(chop_path),
        "point_cloud_path": str(pc_path),
        "skipped": False,
    }


# ---------------------------------------------------------------------------
# Stage 6: REPORT
# ---------------------------------------------------------------------------


def stage_report(
    config: Any,
    output_dir: Path,
    stage_results: dict[str, Any],
    *,
    config_path: str = "",
    total_time: float = 0.0,
) -> Path:
    """Collect all stage results and write render_report.json."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # File inventory
    inventory = [
        {
            "path": str(p.relative_to(output_dir)),
            "size_bytes": p.stat().st_size,
        }
        for p in sorted(output_dir.rglob("*"))
        if p.is_file()
    ]

    report = {
        "stages": stage_results,
        "total_time": total_time,
        "output_dir": str(output_dir),
        "config_path": config_path,
        "tier": config.tier,
        "file_inventory": inventory,
    }

    report_path = output_dir / "render_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    logger.info("REPORT: %s", report_path)
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Run all assembly stages."""
    parser = argparse.ArgumentParser(description="Assemble final deliverables")
    parser.add_argument(
        "--config",
        required=True,
        help="Config YAML path (overlaid on base.yaml)",
    )
    parser.add_argument("--output-dir", default="output/hero", help="Output directory")
    parser.add_argument("--skip-validation", action="store_true")
    parser.add_argument(
        "--no-regenerate",
        action="store_true",
        help="Skip generation if zarr exists",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    from oco_viz.config import load_config  # noqa: PLC0415

    with Path(args.config).open() as f:
        overrides = yaml.safe_load(f) or {}

    config = load_config(overrides=overrides)
    output_dir = Path(args.output_dir)
    t_start = time.monotonic()

    results: dict[str, Any] = {}

    # Stage 1: GENERATE
    logger.info("=== Stage 1: GENERATE ===")
    results["generate"] = stage_generate(config, output_dir, skip=args.no_regenerate)
    zarr_path = Path(results["generate"]["zarr_path"])

    # Stage 2: VALIDATE
    logger.info("=== Stage 2: VALIDATE ===")
    results["validate"] = stage_validate(
        config,
        zarr_path,
        output_dir,
        skip=args.skip_validation,
    )

    # Stage 3: RENDER
    logger.info("=== Stage 3: RENDER ===")
    results["render"] = stage_render(config, zarr_path, output_dir)
    frames_dir = Path(results["render"]["frames_dir"])

    # Stage 4: ENCODE
    logger.info("=== Stage 4: ENCODE ===")
    results["encode"] = stage_encode(config, frames_dir, output_dir)

    # Stage 5: EXPORT
    logger.info("=== Stage 5: EXPORT ===")
    results["export"] = stage_export(config, zarr_path, output_dir)

    # Stage 6: REPORT
    logger.info("=== Stage 6: REPORT ===")
    total_time = time.monotonic() - t_start
    report_path = stage_report(
        config,
        output_dir,
        results,
        config_path=args.config,
        total_time=total_time,
    )
    print(f"Assembly complete: {report_path}")


if __name__ == "__main__":
    main()
