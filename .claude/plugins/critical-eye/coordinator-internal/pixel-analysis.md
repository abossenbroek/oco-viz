# Pixel Analysis — Coordinator Reference

## Preferred Method: `pixi run image-stats`

All pixel analysis should be run via the unified `image-stats` command:

```bash
# Full YAML output with tier verdicts
pixi run image-stats <image> --tier exhibition

# Human-readable text
pixi run image-stats <image> --tier exhibition --format text

# Batch
pixi run image-stats output/examples/wave5/*.png --tier study
```

This command (backed by `scripts/image_stats.py`) provides all measurements
in a single invocation: channels, corners, divergence, fill, luminance,
center-of-mass, bounding box, edges, and tier-specific verdicts.

See `.claude/plugins/critical-eye/skills/image-stats/SKILL.md` for the full
output schema and tier threshold reference.

---

## Fallback: Inline Recipes

If `pixi run image-stats` is unavailable (e.g., pixi not installed), these
inline Python one-liners provide equivalent functionality.

### Quick Diagnostic (All-In-One)

```bash
IMG="output/examples/wave5/tier_exhibition_soot.png"
python3 -c "
from PIL import Image
import numpy as np
im = np.array(Image.open('$IMG'))
h, w = im.shape[:2]
print(f'=== {\"$IMG\"} ({w}x{h}) ===')
print()
for i, ch in enumerate(['R', 'G', 'B']):
    print(f'{ch}: max={im[:,:,i].max()}, mean={im[:,:,i].mean():.1f}')
print()
for name, sl in [('TL', (slice(10), slice(10))), ('TR', (slice(10), slice(w-10, w))),
                  ('BL', (slice(h-10, h), slice(10))), ('BR', (slice(h-10, h), slice(w-10, w)))]:
    print(f'{name} corner max: {im[sl].max()}')
print()
mask = im.sum(axis=2) > 0
if mask.any():
    px = im[mask].astype(float)
    print(f'Channel divergence: max|R-G|={np.abs(px[:,0]-px[:,1]).max():.0f}, max|R-B|={np.abs(px[:,0]-px[:,2]).max():.0f}')
print()
total = h * w
nonblack = mask.sum()
print(f'Frame fill: {100.0*nonblack/total:.1f}%')
lum = np.array(Image.open('$IMG').convert('L'))
vals = lum[lum > 0]
if len(vals):
    q = np.percentile(vals, [50, 95, 99])
    print(f'Luminance Q50={q[0]:.0f} Q95={q[1]:.0f} Q99={q[2]:.0f} max={vals.max()}')
"
```
