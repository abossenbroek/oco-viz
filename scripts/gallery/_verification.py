"""Verification of rendered gallery images via image_stats analysis."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any

import yaml


def _analyze_single(
    img_path: Path,
    tier: str,
    analyze_fn: Any,
) -> dict[str, Any]:
    """Analyze a single image and return its result dict."""
    if not img_path.exists():
        return {
            "name": img_path.name,
            "path": str(img_path),
            "verdict": "skip",
            "reason": "file not found",
        }

    stats = analyze_fn(img_path, tier=tier)
    verdicts = stats.get("verdicts", {})
    overall = verdicts.get("overall", "fail")

    metrics: dict[str, Any] = {}
    fill = stats.get("frame_fill", {})
    if "percent" in fill:
        metrics["frame_fill_pct"] = fill["percent"]
    div = stats.get("channel_divergence", {})
    max_div = max(
        div.get("max_rg", 0),
        div.get("max_rb", 0),
        div.get("max_gb", 0),
    )
    metrics["max_divergence"] = max_div
    lum = stats.get("luminance", {})
    if "max" in lum:
        metrics["peak_luminance"] = lum["max"]

    verdict_flags: dict[str, bool] = {}
    for vk, vv in verdicts.items():
        if isinstance(vv, dict) and "pass" in vv:
            verdict_flags[vk] = vv["pass"]

    return {
        "name": img_path.name,
        "path": str(img_path),
        "verdict": "pass" if overall == "pass" else "fail",
        "metrics": metrics,
        "verdicts": verdict_flags,
    }


def run_verification(
    rendered: list[Path],
    output_path: Path,
    *,
    tier: str = "study",
) -> dict[str, Any]:
    """Analyze rendered images and write a verification YAML report.

    Parameters
    ----------
    rendered
        Paths to rendered PNG files.
    output_path
        Where to write the verification YAML.
    tier
        Tier to evaluate against (``study``, ``exhibition``, ``sketch``).

    Returns
    -------
    dict
        The verification report structure.
    """
    from scripts.image_stats import analyze_image  # noqa: PLC0415

    results = [_analyze_single(p, tier, analyze_image) for p in rendered]

    passed = sum(1 for r in results if r["verdict"] == "pass")
    failed = sum(1 for r in results if r["verdict"] == "fail")

    wave_groups: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        p = Path(r["path"])
        parts = p.parts
        wave_key = "base"
        if "examples" in parts:
            idx = parts.index("examples")
            if idx + 1 < len(parts) and parts[idx + 1] != p.name:
                wave_key = parts[idx + 1]
        wave_groups.setdefault(wave_key, []).append(r)

    tier_entry: dict[str, Any] = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "waves": {},
    }
    for wave_name, images in wave_groups.items():
        tier_entry["waves"][wave_name] = {"images": images}

    report: dict[str, Any] = {
        "verification": {
            "timestamp": datetime.datetime.now(tz=datetime.UTC).isoformat(),
            "total_images": len(results),
            "passed": passed,
            "failed": failed,
            "tiers": {tier: tier_entry},
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.dump(report, default_flow_style=False, sort_keys=False))

    return report
