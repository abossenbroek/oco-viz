---
description: Run pixel-level and composition analysis on gallery images
argument-hint: "<image-or-glob> [--tier exhibition|study|sketch] [--format yaml|text]"
---

Run structured pixel analysis on rendered gallery images. Outputs YAML (default) or human-readable text with all measurements needed for visual quality review.

```bash
pixi run image-stats $ARGUMENTS
```

## What it measures

- Per-channel RGB stats (max, mean, min)
- Background corner sampling (4 corners)
- Channel divergence / achromatic test
- Frame fill percentage
- Luminance histogram quartiles
- Center-of-mass offset (composition asymmetry)
- Bounding box aspect ratio (vertical emphasis)
- Frame edge blackness
- Tier-specific pass/fail verdicts (when `--tier` specified)

## Examples

```
/critical-eye:image-stats output/examples/wave5/tier_exhibition_soot.png --tier exhibition
/critical-eye:image-stats output/examples/wave5/tier_*.png --tier exhibition --format text
/critical-eye:image-stats output/examples/wave5/*.png
```

$ARGUMENTS passed through to `pixi run image-stats`.
