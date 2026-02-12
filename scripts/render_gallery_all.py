"""Unified gallery renderer: render any wave x tier cross-product.

Usage:
    pixi run gallery                                           # All waves, native tiers
    pixi run gallery -- --wave 2,3,4 --tier exhibition --verify  # Cross-product + verify
    pixi run gallery -- --dry-run                              # List all ~115 images
    pixi run gallery -- --wave 3 --tier study --verify-output report.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is importable so ``scripts.gallery`` resolves.
_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import structlog

from scripts.gallery import WAVE_DEFAULT_TIER, WAVE_NAMES, load_wave_module
from scripts.gallery._common import configure_gallery_logging
from scripts.gallery._progress import DryRunProgress, GalleryProgress
from scripts.gallery._verification import run_verification

log = structlog.get_logger()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Unified gallery renderer for oco-viz.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--wave",
        default="all",
        help=(
            "Comma-separated wave names to render. "
            f"Values: {','.join(WAVE_NAMES)},all (default: all)"
        ),
    )
    parser.add_argument(
        "--tier",
        default=None,
        help=(
            "Comma-separated tiers. Values: sketch,study,exhibition "
            "(default: each wave's native tier)"
        ),
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run image_stats verification on rendered images.",
    )
    parser.add_argument(
        "--verify-output",
        default="output/examples/verification.yaml",
        help="Path for verification YAML output (default: output/examples/verification.yaml).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List all images without rendering.",
    )
    return parser.parse_args(argv)


def _parse_waves(wave_arg: str) -> list[str]:
    """Parse --wave argument into list of wave names."""
    if wave_arg.strip().lower() == "all":
        return list(WAVE_NAMES)
    names = [w.strip() for w in wave_arg.split(",") if w.strip()]
    for name in names:
        if name not in WAVE_NAMES:
            log.error("unknown wave", wave=name, valid=WAVE_NAMES)
            sys.exit(1)
    return names


def _parse_tiers(tier_arg: str | None) -> list[str] | None:
    """Parse --tier argument. Returns None if not specified (use native tiers)."""
    if tier_arg is None:
        return None
    valid = {"sketch", "study", "exhibition"}
    tiers = [t.strip() for t in tier_arg.split(",") if t.strip()]
    for t in tiers:
        if t not in valid:
            log.error("unknown tier", tier=t, valid=sorted(valid))
            sys.exit(1)
    return tiers


def _compute_total_images(waves: list[str], tiers: list[str] | None) -> int:
    """Compute total image count from manifests."""
    total = 0
    for wave_name in waves:
        mod = load_wave_module(wave_name)
        manifest = mod.IMAGE_MANIFEST
        n_tiers = len(tiers) if tiers else 1
        total += len(manifest) * n_tiers
    return total


def _output_dir_for(
    wave_name: str,
    tier: str | None,
    *,
    multi_tier: bool,
) -> Path:
    """Compute output directory for a wave/tier combination.

    Multi-tier: ``output/examples/{wave}/{tier}/``
    Single tier: ``output/examples/{wave}/`` (flat, no tier subdirectory).
    """
    wave_dir_name = {
        "base": "",  # base wave outputs to output/examples/ directly
        "2": "wave2",
        "3": "wave3",
        "4": "wave4",
        "5": "wave5",
        "6": "wave6",
        "exhibition": "exhibition",
        "real_data": "real_data",
    }.get(wave_name, wave_name)

    base = Path("output/examples")
    if wave_dir_name:
        base = base / wave_dir_name
    if multi_tier and tier:
        base = base / tier
    return base


def run_gallery(argv: list[str] | None = None) -> int:
    """Main entry point. Returns exit code (0 = success)."""
    args = _parse_args(argv)

    waves = _parse_waves(args.wave)
    tiers = _parse_tiers(args.tier)
    multi_tier = tiers is not None and len(tiers) > 1

    total = _compute_total_images(waves, tiers)

    if args.dry_run:
        log.info("dry-run mode", waves=waves, tiers=tiers, total_images=total)
        drp = DryRunProgress()
        for wave_name in waves:
            mod = load_wave_module(wave_name)
            tier_list = tiers if tiers else [WAVE_DEFAULT_TIER[wave_name]]
            for tier in tier_list:
                drp.begin_wave(wave_name)
                for img_name in mod.IMAGE_MANIFEST:
                    out_dir = _output_dir_for(wave_name, tier, multi_tier=multi_tier)
                    drp.image_done(f"{out_dir}/{img_name}")
        # Print collected images
        for img in drp.images:
            print(img)
        print(f"\nTotal: {drp.total_images} images")
        return 0

    # Actual rendering
    log.info("gallery render starting", waves=waves, tiers=tiers, total_images=total)
    progress = GalleryProgress(total_images=total)
    all_rendered: list[Path] = []

    for wave_name in waves:
        mod = load_wave_module(wave_name)
        tier_list = tiers if tiers else [WAVE_DEFAULT_TIER[wave_name]]

        for tier in tier_list:
            out_dir = _output_dir_for(wave_name, tier, multi_tier=multi_tier)
            log.info("rendering wave", wave=wave_name, tier=tier, output_dir=str(out_dir))

            rendered = mod.render_wave(
                tier_override=tier,
                progress=progress,
                output_dir=out_dir,
            )
            all_rendered.extend(rendered)

    log.info("gallery render complete", **progress.summary())

    # Verification
    if args.verify:
        verify_tier = tiers[0] if tiers and len(tiers) == 1 else "study"
        verify_path = Path(args.verify_output)
        log.info("running verification", tier=verify_tier, output=str(verify_path))
        existing = [p for p in all_rendered if p.exists()]
        report = run_verification(existing, verify_path, tier=verify_tier)
        v = report["verification"]
        log.info(
            "verification complete",
            total=v["total_images"],
            passed=v["passed"],
            failed=v["failed"],
        )

    return 0


def main() -> None:
    """CLI entry point."""
    configure_gallery_logging()
    sys.exit(run_gallery())


if __name__ == "__main__":
    main()
