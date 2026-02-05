---
name: image-stats
user-invocable: false
---

# Image Stats — Pixel Analysis Skill

Structured pixel-level and composition analysis for rendered gallery images. Runs via `pixi run image-stats` and outputs YAML or human-readable text.

**Script**: `scripts/image_stats.py`

---

## Usage

```bash
# Full YAML output (default) — all measurements
pixi run image-stats output/examples/wave5/tier_exhibition_soot.png

# With tier-specific pass/fail verdicts
pixi run image-stats output/examples/wave5/tier_exhibition_soot.png --tier exhibition

# Human-readable text output
pixi run image-stats output/examples/wave5/tier_exhibition_soot.png --tier exhibition --format text

# Batch: multiple images
pixi run image-stats output/examples/wave5/tier_*.png --tier exhibition

# Glob patterns
pixi run image-stats "output/examples/wave5/*.png" --tier study
```

---

## Output Sections

The YAML output contains these sections:

| Section | Contents |
|---------|----------|
| `channels` | Per-channel (R, G, B) max, mean, min |
| `corners` | 10x10 patch stats from 4 frame corners |
| `channel_divergence` | Max/mean |R-G|, |R-B|, |G-B| across non-black pixels |
| `frame_fill` | Percent of frame occupied by non-black content |
| `luminance` | Histogram quartiles (Q25, Q50, Q75, Q95, Q99) + max |
| `center_of_mass` | Luminance-weighted CoM + offset from frame center |
| `bounding_box` | Plume extent, aspect ratio, vertical emphasis flag |
| `edge_blackness` | Per-edge max pixel value + all_black flag |
| `verdicts` | (if `--tier`) Per-check pass/fail against tier thresholds |

---

## Tier Thresholds

| Check | Exhibition | Study | Sketch |
|-------|-----------|-------|--------|
| Max channel divergence | <= 2 | <= 5 | <= 255 |
| Frame fill | 60-80% | 30-90% | 5-100% |
| Peak luminance | <= 210 | <= 230 | <= 255 |
| Corner blackness | == 0 | <= 15 | <= 255 |
| Edge blackness | == 0 | <= 15 | <= 255 |
| CoM asymmetry | >= 0.03 | (not checked) | (not checked) |

---

## Agent Usage

Both the **critical-eye** and **art-director** agents should use this command
for quantitative backing instead of inline pixel analysis scripts.

The critical-eye agent runs:
```bash
pixi run image-stats <image> --tier <tier>
```

The output provides all measurements needed for Phase 2 (Image Analysis) and
feeds directly into Phase 3 (VFX Evaluation) verdicts.
