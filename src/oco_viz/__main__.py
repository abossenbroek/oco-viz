"""CLI entry points for oco_viz."""

from __future__ import annotations

import argparse
from pathlib import Path

from oco_viz.config import load_config
from oco_viz.data.pipeline import run_data_pipeline
from oco_viz.data.zarr_store import write_zarr
from oco_viz.plume.gaussian import generate_sequence
from oco_viz.plume.turbulent import generate_turbulent_sequence
from oco_viz.sequencer.controller import render_sequence
from oco_viz.sequencer.encode import encode_video


def _get_tier(args: argparse.Namespace) -> str | None:
    """Extract tier from args, returning None if not set."""
    return getattr(args, "tier", None) or None


def cmd_generate_plume(args: argparse.Namespace) -> None:
    """Generate synthetic plume to Zarr."""
    config = load_config(args.profile, tier=_get_tier(args))
    output = Path(args.output)

    if args.turbulent:
        ds = generate_turbulent_sequence(
            config.plume,
            config.grid,
            config.turbulence,
            num_timesteps=args.timesteps,
        )
    else:
        ds = generate_sequence(config.plume, config.grid, num_timesteps=args.timesteps)

    write_zarr(ds, output)
    print(f"Wrote {args.timesteps} timesteps to {output}")


def cmd_render(args: argparse.Namespace) -> None:
    """Render frames from Zarr."""
    overrides: dict[str, dict[str, str]] = {}
    if args.preset:
        overrides["transfer_function"] = {"preset": args.preset}
    config = load_config(
        args.profile,
        overrides=overrides if overrides else None,
        tier=_get_tier(args),
    )
    zarr_path = Path(args.zarr)
    paths = render_sequence(config, zarr_path, num_frames=args.num_frames)
    print(f"Rendered {len(paths)} frames to {config.output.frames_dir}")


def cmd_encode(args: argparse.Namespace) -> None:
    """Encode frames to video."""
    config = load_config(args.profile, tier=_get_tier(args))
    frames_dir = Path(config.output.frames_dir)
    video_dir = Path(config.output.video_dir)
    output_path = video_dir / "synthetic_plume.mp4"
    encode_video(frames_dir, output_path, fps=config.output.fps)
    print(f"Encoded video: {output_path}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate modeled plume against observations."""
    from oco_viz.data.validation import (  # noqa: PLC0415
        compare_modeled_observed,
        compute_column_xco2,
        generate_validation_report,
    )
    from oco_viz.data.zarr_store import read_zarr  # noqa: PLC0415

    config = load_config(args.profile, tier=_get_tier(args))
    zarr_path = Path(args.zarr)
    ds = read_zarr(zarr_path)

    # Compute column XCO2 from last timestep
    conc_3d = ds["concentration"].isel(time=-1).values
    modeled_column = compute_column_xco2(conc_3d, config.grid, config.validation)

    # Check for observed data
    if "xco2_observed" not in ds:
        print("No xco2_observed in dataset — skipping comparison")
        return

    observed = ds["xco2_observed"].values
    result = compare_modeled_observed(modeled_column, observed, config.validation)

    output_dir = Path(args.output_dir)
    report_path = generate_validation_report(result, output_dir)
    print(f"Validation report: {report_path}")
    status = "PASSED" if result.passed else "FAILED"
    print(f"Status: {status} (RMSE={result.rmse_ppm:.2f} ppm, r={result.correlation:.3f})")


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Run full pipeline: generate -> render -> encode."""
    config = load_config(args.profile, tier=_get_tier(args))
    zarr_path = Path("output/plume.zarr")

    # Determine mode from flags
    mode = getattr(args, "mode", "gaussian")
    cams_path = Path(args.cams) if getattr(args, "cams", None) else None
    era5_path = Path(args.era5) if getattr(args, "era5", None) else None

    # For backward compat: --turbulent flag maps to mode=turbulent
    if getattr(args, "turbulent", False) and mode == "gaussian":
        mode = "turbulent"

    ds = run_data_pipeline(
        config,
        mode=mode,
        era5_path=era5_path,
        cams_path=cams_path,
        num_timesteps=args.num_frames,
    )
    write_zarr(ds, zarr_path)
    print(f"Generated plume ({mode}): {zarr_path}")

    # Render
    paths = render_sequence(config, zarr_path, num_frames=args.num_frames)
    print(f"Rendered {len(paths)} frames")

    # Encode
    video_dir = Path(config.output.video_dir)
    output_path = video_dir / "synthetic_plume.mp4"
    encode_video(Path(config.output.frames_dir), output_path, fps=config.output.fps)
    print(f"Video: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="oco_viz", description="OCO-3 CO2 Plume Visualization")
    sub = parser.add_subparsers(dest="command", required=True)

    # generate-plume
    p_gen = sub.add_parser("generate-plume", help="Generate synthetic plume to Zarr")
    p_gen.add_argument("--profile", default="dev_mac")
    p_gen.add_argument("--tier", default=None, choices=["sketch", "study", "exhibition"])
    p_gen.add_argument("--output", default="output/plume.zarr")
    p_gen.add_argument("--timesteps", type=int, default=48)
    p_gen.add_argument("--turbulent", action="store_true", help="Use turbulent plume compositor")
    p_gen.set_defaults(func=cmd_generate_plume)

    # render
    p_render = sub.add_parser("render", help="Render frames from Zarr")
    p_render.add_argument("--profile", default="dev_mac")
    p_render.add_argument("--tier", default=None, choices=["sketch", "study", "exhibition"])
    p_render.add_argument("--zarr", default="output/plume.zarr")
    p_render.add_argument("--num-frames", type=int, default=None)
    p_render.add_argument("--preset", default=None, help="Transfer function preset name")
    p_render.set_defaults(func=cmd_render)

    # encode
    p_encode = sub.add_parser("encode", help="Encode frames to video")
    p_encode.add_argument("--profile", default="dev_mac")
    p_encode.add_argument("--tier", default=None, choices=["sketch", "study", "exhibition"])
    p_encode.set_defaults(func=cmd_encode)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Full pipeline: generate -> render -> encode")
    p_pipe.add_argument("--profile", default="dev_mac")
    p_pipe.add_argument("--tier", default=None, choices=["sketch", "study", "exhibition"])
    p_pipe.add_argument("--num-frames", type=int, default=48)
    p_pipe.add_argument("--turbulent", action="store_true", help="Use turbulent plume compositor")
    p_pipe.add_argument(
        "--mode",
        default="gaussian",
        choices=["gaussian", "turbulent", "composite", "wind", "advected"],
        help="Pipeline mode (default: gaussian)",
    )
    p_pipe.add_argument("--cams", default=None, help="Path to CAMS NetCDF (for composite mode)")
    p_pipe.add_argument(
        "--era5", default=None, help="Path to ERA5 NetCDF (for wind/advected mode)"
    )
    p_pipe.set_defaults(func=cmd_pipeline)

    # validate
    p_validate = sub.add_parser("validate", help="Validate modeled plume against observations")
    p_validate.add_argument("--profile", default="dev_mac")
    p_validate.add_argument("--tier", default=None, choices=["sketch", "study", "exhibition"])
    p_validate.add_argument("--zarr", required=True, help="Path to Zarr store")
    p_validate.add_argument(
        "--output-dir", default="output/validation", help="Report output dir"
    )
    p_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
