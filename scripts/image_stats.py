"""Pixel-level and composition statistics for rendered gallery images.

Usage:
    pixi run image-stats <image> [--tier exhibition|study|sketch] [--format yaml|text]
    pixi run image-stats output/examples/wave5/tier_exhibition_soot.png --tier exhibition
    pixi run image-stats output/examples/wave5/*.png

Outputs structured YAML (default) or human-readable text with all
measurements the critical-eye agents need for review:
  - Per-channel RGB stats (max, mean, min)
  - Background corner sampling (4 corners, 10x10 patches)
  - Channel divergence / achromatic test
  - Frame fill percentage
  - Luminance histogram quartiles
  - Center-of-mass offset (composition asymmetry)
  - Bounding box aspect ratio (vertical emphasis)
  - Frame edge blackness
  - Tier-specific pass/fail flags
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Tier thresholds
# ---------------------------------------------------------------------------

TIER_THRESHOLDS: dict[str, dict[str, int | float]] = {
    "exhibition": {
        "max_channel_divergence": 2,
        "frame_fill_min": 60.0,
        "frame_fill_max": 80.0,
        "peak_luminance_max": 210,
        "corner_max": 0,
        "edge_max": 0,
        "com_offset_min": 0.03,
    },
    "study": {
        "max_channel_divergence": 5,
        "frame_fill_min": 30.0,
        "frame_fill_max": 90.0,
        "peak_luminance_max": 230,
        "corner_max": 15,
        "edge_max": 15,
        "com_offset_min": 0.0,
    },
    "sketch": {
        "max_channel_divergence": 255,
        "frame_fill_min": 5.0,
        "frame_fill_max": 100.0,
        "peak_luminance_max": 255,
        "corner_max": 255,
        "edge_max": 255,
        "com_offset_min": 0.0,
    },
}


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------


def channel_stats(im: np.ndarray) -> dict[str, dict[str, float]]:
    """Per-channel max, mean, min."""
    result: dict[str, dict[str, float]] = {}
    for i, ch in enumerate(["R", "G", "B"]):
        data = im[:, :, i]
        result[ch] = {
            "max": int(data.max()),
            "mean": round(float(data.mean()), 1),
            "min": int(data.min()),
        }
    return result


def corner_sampling(im: np.ndarray, size: int = 10) -> dict[str, dict[str, float]]:
    """Sample 10x10 patches from each corner."""
    h, w = im.shape[:2]
    corners = {
        "top_left": im[:size, :size],
        "top_right": im[:size, w - size :],
        "bottom_left": im[h - size :, :size],
        "bottom_right": im[h - size :, w - size :],
    }
    return {
        name: {"max": int(patch.max()), "mean": round(float(patch.mean()), 2)}
        for name, patch in corners.items()
    }


def channel_divergence(im: np.ndarray) -> dict[str, float]:
    """Max and mean channel divergence across non-black pixels."""
    mask = im.sum(axis=2) > 0
    if not mask.any():
        return {"max_rg": 0, "max_rb": 0, "max_gb": 0, "mean_rg": 0.0}
    px = im[mask].astype(float)
    return {
        "max_rg": int(np.abs(px[:, 0] - px[:, 1]).max()),
        "max_rb": int(np.abs(px[:, 0] - px[:, 2]).max()),
        "max_gb": int(np.abs(px[:, 1] - px[:, 2]).max()),
        "mean_rg": round(float(np.abs(px[:, 0] - px[:, 1]).mean()), 2),
    }


def frame_fill(im: np.ndarray) -> dict[str, float]:
    """Fraction of frame occupied by non-black content."""
    h, w = im.shape[:2]
    total = h * w
    nonblack = int((im.sum(axis=2) > 0).sum())
    return {
        "percent": round(100.0 * nonblack / total, 1),
        "nonblack_pixels": nonblack,
        "total_pixels": total,
    }


def luminance_histogram(im: np.ndarray) -> dict[str, float]:
    """Luminance quartiles for non-black pixels."""
    lum = np.array(Image.fromarray(im).convert("L"))
    vals = lum[lum > 0]
    if len(vals) == 0:
        return {"count": 0}
    q = np.percentile(vals, [25, 50, 75, 95, 99])
    return {
        "count": len(vals),
        "Q25": int(q[0]),
        "Q50": int(q[1]),
        "Q75": int(q[2]),
        "Q95": int(q[3]),
        "Q99": int(q[4]),
        "max": int(vals.max()),
    }


def center_of_mass(im: np.ndarray) -> dict[str, float]:
    """Luminance-weighted center of mass and offset from frame center."""
    lum = np.array(Image.fromarray(im).convert("L")).astype(float)
    h, w = lum.shape
    total = lum.sum()
    if total == 0:
        return {"cx": 0, "cy": 0, "offset_x": 0.0, "offset_y": 0.0, "total_offset": 0.0}
    cy = float((lum * np.arange(h).reshape(-1, 1)).sum() / total)
    cx = float((lum * np.arange(w).reshape(1, -1)).sum() / total)
    ox = (cx - w / 2) / (w / 2)
    oy = (cy - h / 2) / (h / 2)
    return {
        "cx": round(cx, 0),
        "cy": round(cy, 0),
        "offset_x": round(ox, 3),
        "offset_y": round(oy, 3),
        "total_offset": round(abs(ox) + abs(oy), 3),
    }


def bounding_box(im: np.ndarray) -> dict[str, Any]:
    """Plume bounding box and aspect ratio."""
    mask = im.sum(axis=2) > 0
    if not mask.any():
        return {"width": 0, "height": 0, "aspect_hw": 0.0, "vertical_emphasis": False}
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    y_min, y_max = int(np.where(rows)[0][0]), int(np.where(rows)[0][-1])
    x_min, x_max = int(np.where(cols)[0][0]), int(np.where(cols)[0][-1])
    bh = y_max - y_min
    bw = x_max - x_min
    ratio = bh / max(bw, 1)
    return {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "width": bw,
        "height": bh,
        "aspect_hw": round(ratio, 2),
        "vertical_emphasis": ratio > 1.0,
    }


def edge_blackness(im: np.ndarray) -> dict[str, Any]:
    """Check that frame edges are absolute black."""
    h, w = im.shape[:2]
    edges: dict[str, Any] = {
        "top": int(im[0, :].max()),
        "bottom": int(im[h - 1, :].max()),
        "left": int(im[:, 0].max()),
        "right": int(im[:, w - 1].max()),
    }
    edges["max"] = max(edges["top"], edges["bottom"], edges["left"], edges["right"])
    edges["all_black"] = edges["max"] == 0
    return edges


# ---------------------------------------------------------------------------
# Tier verdicts
# ---------------------------------------------------------------------------


def tier_verdicts(
    tier: str,
    div: dict[str, float],
    fill: dict[str, float],
    lum: dict[str, float],
    corners: dict[str, dict[str, float]],
    edges: dict[str, Any],
    com: dict[str, float],
) -> dict[str, Any]:
    """Evaluate measurements against tier thresholds."""
    t = TIER_THRESHOLDS.get(tier, TIER_THRESHOLDS["study"])
    max_div = max(div.get("max_rg", 0), div.get("max_rb", 0), div.get("max_gb", 0))
    corner_max = max(c["max"] for c in corners.values())
    verdicts: dict[str, Any] = {
        "achromatic": {
            "pass": max_div <= t["max_channel_divergence"],
            "max_divergence": max_div,
            "threshold": t["max_channel_divergence"],
        },
        "frame_fill": {
            "pass": t["frame_fill_min"] <= fill["percent"] <= t["frame_fill_max"],
            "percent": fill["percent"],
            "range": [t["frame_fill_min"], t["frame_fill_max"]],
        },
        "peak_luminance": {
            "pass": lum.get("max", 0) <= t["peak_luminance_max"],
            "max": lum.get("max", 0),
            "threshold": t["peak_luminance_max"],
        },
        "corner_blackness": {
            "pass": corner_max <= t["corner_max"],
            "max": corner_max,
            "threshold": t["corner_max"],
        },
        "edge_blackness": {
            "pass": edges["max"] <= t["edge_max"],
            "max": edges["max"],
            "threshold": t["edge_max"],
        },
    }
    if t["com_offset_min"] > 0:
        verdicts["asymmetry"] = {
            "pass": com["total_offset"] >= t["com_offset_min"],
            "total_offset": com["total_offset"],
            "threshold": t["com_offset_min"],
        }
    all_pass = all(
        v["pass"] for v in verdicts.values() if isinstance(v, dict) and "pass" in v
    )
    verdicts["overall"] = "pass" if all_pass else "fail"
    return verdicts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def analyze_image(path: Path, tier: str | None = None) -> dict[str, Any]:
    """Run full analysis on a single image. Returns structured dict."""
    im = np.array(Image.open(path))
    h, w = im.shape[:2]

    channels = channel_stats(im)
    corners = corner_sampling(im)
    div = channel_divergence(im)
    fill_data = frame_fill(im)
    lum = luminance_histogram(im)
    com = center_of_mass(im)
    bbox = bounding_box(im)
    edges = edge_blackness(im)

    result: dict[str, Any] = {
        "image": str(path),
        "dimensions": {"width": w, "height": h},
        "channels": channels,
        "corners": corners,
        "channel_divergence": div,
        "frame_fill": fill_data,
        "luminance": lum,
        "center_of_mass": com,
        "bounding_box": bbox,
        "edge_blackness": edges,
    }

    if tier:
        result["tier"] = tier
        result["verdicts"] = tier_verdicts(tier, div, fill_data, lum, corners, edges, com)

    return result


def format_yaml(data: dict[str, Any], indent: int = 0) -> str:
    """Simple YAML-like formatter (avoids PyYAML import for script portability)."""
    lines: list[str] = []
    prefix = "  " * indent
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(format_yaml(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{prefix}{k}: [{', '.join(str(x) for x in v)}]")
        elif isinstance(v, bool):
            lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{prefix}{k}: {v}")
    return "\n".join(lines)


def format_text(data: dict[str, Any]) -> str:
    """Human-readable summary."""
    lines: list[str] = []
    dims = data["dimensions"]
    lines.append(f"=== {data['image']} ({dims['width']}x{dims['height']}) ===")
    lines.append("")

    ch = data["channels"]
    for c in ["R", "G", "B"]:
        s = ch[c]
        lines.append(f"  {c}: max={s['max']}, mean={s['mean']}, min={s['min']}")

    lines.append("")
    for name, vals in data["corners"].items():
        lines.append(f"  {name}: max={vals['max']}, mean={vals['mean']}")

    div = data["channel_divergence"]
    lines.append("")
    lines.append(
        f"  Channel divergence: max|R-G|={div['max_rg']},"
        f" max|R-B|={div['max_rb']}, max|G-B|={div['max_gb']}"
    )

    fill_data = data["frame_fill"]
    lines.append(f"  Frame fill: {fill_data['percent']}%")

    lum = data["luminance"]
    if lum.get("count", 0) > 0:
        lines.append(
            f"  Luminance: Q25={lum['Q25']} Q50={lum['Q50']} Q75={lum['Q75']}"
            f" Q95={lum['Q95']} Q99={lum['Q99']} max={lum['max']}"
        )

    com = data["center_of_mass"]
    lines.append(
        f"  CoM offset: x={com['offset_x']:+.3f} y={com['offset_y']:+.3f}"
        f" (total={com['total_offset']:.3f})"
    )

    bbox = data["bounding_box"]
    vert = "yes" if bbox["vertical_emphasis"] else "no"
    lines.append(
        f"  Bbox: {bbox['width']}w x {bbox['height']}h,"
        f" aspect={bbox['aspect_hw']}, vertical={vert}"
    )

    edges = data["edge_blackness"]
    edge_label = "black" if edges["all_black"] else "NON-BLACK"
    lines.append(f"  Edges: max={edges['max']} ({edge_label})")

    if "verdicts" in data:
        lines.append("")
        lines.append(f"  --- Tier verdicts ({data['tier']}) ---")
        verdicts = data["verdicts"]
        for vk, vv in verdicts.items():
            if vk == "overall":
                lines.append(f"  OVERALL: {vv}")
            elif isinstance(vv, dict):
                status = "PASS" if vv.get("pass") else "FAIL"
                lines.append(f"  {vk}: {status}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pixel-level and composition statistics for rendered gallery images",
    )
    parser.add_argument("images", nargs="+", help="Image file paths or glob patterns")
    parser.add_argument(
        "--tier",
        choices=["exhibition", "study", "sketch"],
        default=None,
        help="Tier for pass/fail verdicts (optional)",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "text"],
        default="yaml",
        dest="output_format",
        help="Output format (default: yaml)",
    )
    args = parser.parse_args()

    # Expand globs
    paths: list[Path] = []
    for pattern in args.images:
        p = Path(pattern)
        if p.exists():
            paths.append(p)
        else:
            # Try as glob from cwd
            expanded = list(Path().glob(pattern))
            if expanded:
                paths.extend(sorted(expanded))
            else:
                print(f"WARNING: no files match '{pattern}'", file=sys.stderr)

    if not paths:
        print("ERROR: no images found", file=sys.stderr)
        sys.exit(1)

    for path in paths:
        data = analyze_image(path, tier=args.tier)
        if args.output_format == "yaml":
            print(format_yaml(data))
        else:
            print(format_text(data))
        if len(paths) > 1:
            print("---")


if __name__ == "__main__":
    main()
