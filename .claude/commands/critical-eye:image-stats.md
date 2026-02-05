---
description: Run pixel-level and composition analysis on gallery images
argument-hint: "<image-or-glob> [--tier exhibition|study|sketch] [--format yaml|text]"
---

Run structured pixel analysis on rendered gallery images via `pixi run image-stats`.

Outputs YAML (default) or human-readable text with all measurements needed for visual quality review: per-channel RGB stats, corner sampling, channel divergence, frame fill, luminance histogram, center-of-mass offset, bounding box, edge blackness, and tier-specific pass/fail verdicts.

```bash
pixi run image-stats $ARGUMENTS
```

This command wraps `scripts/image_stats.py`. Both critical-eye agents use this for quantitative backing during reviews, but it can also be run standalone.

$ARGUMENTS passed through to `pixi run image-stats`.
