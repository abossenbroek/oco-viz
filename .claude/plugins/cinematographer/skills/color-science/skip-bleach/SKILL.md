---
name: skip-bleach
user-invocable: false
type: instruction
primary_owner: colorist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Skip Bleach — Photochemical Desaturation for Arid, Harsh Environments

Desaturated highlights, preserved shadows, reduced contrast in the upper tonal range.
The skip-bleach process creates an arid, harsh feel without being uniformly desaturated.
It is a surgical intervention in the highlight-to-midtone transition, not a global
desaturation. The shadows retain their color and density. The emotional result is
bleached harshness above and grounded reality below.

> "Skip bleach doesn't remove color. It removes comfort."

---

## Principle

The skip-bleach (or bleach-bypass) process is a photochemical technique in which the
bleach step of film processing is partially or fully skipped, leaving silver halide
crystals in the emulsion alongside the color dyes. The result: reduced saturation in
highlights and mid-tones, increased apparent grain, retained shadow density, and a
characteristic harsh, desaturated look in bright areas while darker tones remain
relatively saturated.

FotoKem's implementation of this process for production cinema involves running actual
film through a modified photochemical bath, scanning the result, and matching the
characteristics scientifically. The digital emulation in oco-viz recreates this behavior
as an OCIO transform that operates on ACEScg data, applying a luminance-dependent
desaturation curve that mimics the photochemical behavior.

The key distinction: skip bleach is NOT flat desaturation. It is a non-linear,
luminance-dependent process that affects highlights more than shadows. Applying uniform
desaturation destroys the shadow-highlight contrast that makes the process distinctive.

---

## Procedure

### Step 1 — Determine Application Context

Skip bleach is appropriate for specific narrative contexts:

| Context | Application | Notes |
|---------|-------------|-------|
| Exterior harsh environments | Full skip bleach | Arrakis-style arid sequences |
| Industrial emission scenes | Partial (50-75%) | Bleached factory, retained soot texture |
| Confrontation / exposure | Full | Harsh reveal, uncomfortable brightness |
| Interior / intimate | Not appropriate | Use Soot Base LUT instead |
| Night / low-light | Not appropriate | Highlights too dim for visible effect |

### Step 2 — Configure Highlight Desaturation Curve

The core of the emulation is a luminance-dependent desaturation function. Saturation is
preserved in shadows and progressively removed as luminance increases:

```
saturation_mult(luminance) = {
    luminance < shadow_threshold:  1.0  (full saturation preserved)
    shadow_threshold < luminance < highlight_threshold:  lerp(1.0, target_desat)
    luminance > highlight_threshold:  target_desat  (maximum desaturation)
}
```

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `shadow_threshold` | 0.08 | 0.02 - 0.15 | Luminance below which full saturation is preserved |
| `highlight_threshold` | 0.5 | 0.3 - 0.8 | Luminance above which maximum desaturation applies |
| `target_desat` | 0.35 | 0.1 - 0.6 | Saturation multiplier in highlights (1.0 = no change, 0.0 = monochrome) |
| `transition_curve` | smooth | smooth / linear | Transition shape between thresholds |

### Step 3 — Configure Shadow Preservation

Shadow preservation ensures that the lower tonal range retains its density and color,
creating the characteristic skip-bleach contrast between colored shadows and desaturated
highlights:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `shadow_density_boost` | 1.1 | 1.0 - 1.3 | Slight density increase in shadows |
| `shadow_saturation_mult` | 1.05 | 1.0 - 1.15 | Slight saturation increase in shadows |
| `black_point_hold` | 0.0 | 0.0 - 0.02 | Minimum output value (true black preserved) |

### Step 4 — Configure Contrast Reduction

The upper tonal range is compressed, reducing contrast in highlights while preserving
shadow contrast:

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `highlight_contrast_mult` | 0.75 | 0.5 - 0.9 | Contrast reduction factor in highlights |
| `shoulder_start` | 0.6 | 0.4 - 0.8 | Luminance where contrast compression begins |
| `peak_white` | 0.88 | 0.8 - 0.95 | Maximum output luminance |

### Step 5 — Validate Against FotoKem Reference

The digital emulation must be compared against known skip-bleach film references:

1. Process a Macbeth ColorChecker through the emulation
2. Compare highlight patches (rows 1-2) — should be visibly desaturated
3. Compare shadow patches (rows 3-4) — should retain most of their saturation
4. Compare achromatic column — should remain neutral (no color shift from the process)
5. Overall: highlights should feel "bleached" while shadows feel grounded

---

## OCIO Transform Implementation

### Transform as OCIO FileTransform

```yaml
- !<ColorSpace>
  name: Skip Bleach Emulation
  family: Creative
  description: "FotoKem-style skip bleach emulation. Luminance-dependent desaturation."
  isdata: false
  encoding: scene-linear
  from_scene_reference: !<GroupTransform>
    children:
      - !<FileTransform> {src: skip_bleach_emulation.spi3d}
```

### Procedural Transform (for LUT Baking)

```python
"""Generate skip-bleach emulation as a 3D LUT."""
from __future__ import annotations

import numpy as np

def skip_bleach_transform(
    rgb: np.ndarray,
    shadow_threshold: float = 0.08,
    highlight_threshold: float = 0.5,
    target_desat: float = 0.35,
    highlight_contrast_mult: float = 0.75,
    shoulder_start: float = 0.6,
    peak_white: float = 0.88,
) -> np.ndarray:
    """Apply skip-bleach emulation to linear ACEScg data.

    Parameters
    ----------
    rgb : np.ndarray
        Input RGB values in ACEScg linear (shape: [..., 3]).
    """
    # Compute luminance (ACEScg weights)
    lum = 0.2722287 * rgb[..., 0] + 0.6740818 * rgb[..., 1] + 0.0536895 * rgb[..., 2]

    # Luminance-dependent saturation multiplier
    t = np.clip((lum - shadow_threshold) / (highlight_threshold - shadow_threshold), 0, 1)
    t = t * t * (3 - 2 * t)  # smoothstep
    sat_mult = 1.0 - t * (1.0 - target_desat)

    # Apply desaturation
    lum_3 = np.stack([lum] * 3, axis=-1)
    result = lum_3 + sat_mult[..., None] * (rgb - lum_3)

    # Highlight contrast compression
    above_shoulder = result > shoulder_start
    compressed = shoulder_start + (result - shoulder_start) * highlight_contrast_mult
    result = np.where(above_shoulder, compressed, result)

    # Peak white clamp
    result = np.clip(result, 0.0, peak_white)

    return result
```

---

## Parameters

### Primary Skip Bleach Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `shadow_threshold` | float | 0.08 | 0.02 - 0.15 | Luminance below which saturation is fully preserved |
| `highlight_threshold` | float | 0.5 | 0.3 - 0.8 | Luminance above which maximum desaturation applies |
| `target_desat` | float | 0.35 | 0.1 - 0.6 | Highlight saturation multiplier (lower = more desaturated) |
| `transition_curve` | string | smooth | smooth / linear | Transition interpolation |
| `shadow_density_boost` | float | 1.1 | 1.0 - 1.3 | Shadow density increase |
| `shadow_saturation_mult` | float | 1.05 | 1.0 - 1.15 | Shadow saturation boost |

### Contrast Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `highlight_contrast_mult` | float | 0.75 | 0.5 - 0.9 | Highlight contrast reduction |
| `shoulder_start` | float | 0.6 | 0.4 - 0.8 | Compression onset luminance |
| `peak_white` | float | 0.88 | 0.8 - 0.95 | Maximum output luminance |
| `black_point_hold` | float | 0.0 | 0.0 - 0.02 | Minimum output value |

### Application Strength Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `effect_strength` | float | 1.0 | 0.0 - 1.0 | Global blend (0 = bypass, 1 = full effect) |
| `partial_blend` | float | 0.75 | 0.5 - 1.0 | Partial application for industrial scenes |

---

## Anti-Patterns

### 1. The Flat Desat

**Symptom:** The entire image is uniformly desaturated — shadows, midtones, and
highlights all lose the same amount of saturation. The result looks like a washed-out
photograph, not a skip-bleach film.

**Cause:** Applying a global saturation reduction instead of a luminance-dependent
desaturation curve. The fundamental character of skip bleach — harsh highlights vs
grounded shadows — is destroyed by uniform treatment.

**Fix:** Use the luminance-dependent desaturation curve (Step 2). Saturation must be
fully preserved below `shadow_threshold` and progressively removed above it. The
shadow-highlight saturation contrast IS the skip-bleach look.

### 2. The Harsh Contrast

**Symptom:** Shadow detail is crushed and highlight detail is clipped. The image has
extreme contrast but loses the textured, grain-like quality of real skip-bleach film.

**Cause:** Boosting contrast globally instead of compressing highlights specifically.
Real skip bleach reduces contrast in the upper range while preserving shadow density.

**Fix:** Apply contrast compression only above `shoulder_start` using
`highlight_contrast_mult`. Shadows should retain their natural contrast. If shadows are
too dark, increase `shadow_density_boost` slightly, but never crush them.

### 3. The Color Shift

**Symptom:** The skip-bleach emulation introduces an unwanted color cast — typically
green or yellow in the mid-tones — that was not part of the photochemical process.

**Cause:** Desaturation math that does not use correct luminance weights for ACEScg, or
a LUT with interpolation artifacts that create hue rotations.

**Fix:** Use ACEScg luminance weights (0.2722287, 0.6740818, 0.0536895) for the
desaturation calculation. Validate by processing an achromatic ramp — the output must
remain achromatic through the emulation. Any hue in achromatic output is a bug.

### 4. The Everywhere Bleach

**Symptom:** Skip bleach is applied to every shot in the sequence, including interior
scenes, night shots, and intimate moments where the harsh aesthetic is inappropriate.

**Cause:** Treating skip bleach as a project-wide look instead of a narrative tool
applied to specific contexts (arid exteriors, harsh environments, confrontation
sequences).

**Fix:** Apply skip bleach selectively based on narrative context (see Step 1 table).
Use the show base LUT for sequences where skip bleach is inappropriate. The effect_strength
parameter allows gradual transitions between bleached and unbleached segments.

---

## Validation Checklist

- [ ] Desaturation is luminance-dependent, not uniform
- [ ] Highlights (above highlight_threshold) are visibly desaturated
- [ ] Shadows (below shadow_threshold) retain full saturation
- [ ] Achromatic ramp processed through emulation remains neutral (no color shift)
- [ ] Contrast is compressed in highlights, preserved in shadows
- [ ] Peak white does not exceed 0.95 (highlight headroom preserved)
- [ ] True black (0,0,0) is preserved
- [ ] Macbeth chart comparison shows correct shadow/highlight saturation split
- [ ] Application context documented (which shots/sequences use skip bleach)
- [ ] Effect strength appropriate for context (full for exterior, partial for industrial)
- [ ] OCIO transform operates on ACEScg data (not display-referred)
- [ ] LUT uses correct ACEScg luminance weights for desaturation
