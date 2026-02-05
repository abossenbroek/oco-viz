# Composition Checks — Coordinator Reference

## Preferred Method: `pixi run image-stats`

All composition checks are included in the unified `image-stats` command:

```bash
pixi run image-stats <image> --tier exhibition
```

The output includes:
- `frame_fill.percent` — frame fill percentage
- `center_of_mass.offset_x`, `offset_y`, `total_offset` — asymmetry measurement
- `bounding_box.aspect_hw`, `vertical_emphasis` — vertical vs horizontal emphasis
- `edge_blackness.all_black` — frame edge purity
- `verdicts.frame_fill.pass` — tier-specific pass/fail
- `verdicts.asymmetry.pass` — (exhibition only) asymmetry threshold check

See `.claude/plugins/critical-eye/skills/image-stats/SKILL.md` for full schema.

---

## Fallback: Inline Recipes

If `pixi run image-stats` is unavailable:

### Combined Composition Report

```bash
IMG="output/examples/wave5/tier_exhibition_soot.png"
python3 -c "
from PIL import Image
import numpy as np
im = np.array(Image.open('$IMG'))
lum = np.array(Image.open('$IMG').convert('L')).astype(float)
h, w = im.shape[:2]
mask = im.sum(axis=2) > 0
print(f'=== Composition Report ===')
filled = mask.sum()
pct = 100.0 * filled / (h * w)
print(f'Frame fill: {pct:.1f}%')
total = lum.sum()
if total > 0:
    cy = (lum * np.arange(h).reshape(-1,1)).sum() / total
    cx = (lum * np.arange(w).reshape(1,-1)).sum() / total
    ox = (cx - w/2) / (w/2)
    oy = (cy - h/2) / (h/2)
    print(f'CoM offset: x={ox:+.3f} y={oy:+.3f}')
if mask.any():
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    bh = np.where(rows)[0][-1] - np.where(rows)[0][0]
    bw = np.where(cols)[0][-1] - np.where(cols)[0][0]
    print(f'Aspect (h/w): {bh/max(bw,1):.2f} ({\"vertical\" if bh > bw else \"horizontal\"})')
edge_max = max(im[0,:].max(), im[h-1,:].max(), im[:,0].max(), im[:,w-1].max())
print(f'Edge max pixel: {edge_max} ({\"OK\" if edge_max == 0 else \"WARNING: non-black\"})')
"
```
