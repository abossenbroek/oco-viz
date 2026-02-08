---
name: color-science-aces
user-invocable: false
---

# Color Science -- ACEScg & Achromatic Discipline

Color management pipeline for Soot rendering. Ensures achromatic integrity
from scene-linear rendering through deep compositing to final display output.

---

## ACES Pipeline

| Stage | Color Space | Notes |
|-------|------------|-------|
| Working | ACEScg (AP1 primaries, linear) | All rendering and compositing |
| Input | Scene-linear from renderer | VTK outputs linear RGB |
| Processing | ACEScg throughout compositing | Never convert mid-chain |
| Output Display Transform | ACES 1.0 ODT | Rec.709 for monitors, P3-D65 for projection |
| Tone mapping | ACES RRT | Smooth highlight rolloff -- no hard clipping |

**Why ACEScg:** AP1 primaries provide a wide gamut that encompasses all
physically realizable colors while remaining practical for CG computation.
Scene-linear encoding preserves the physical accuracy of light transport
calculations.

**Implementation:** OpenColorIO (OCIO) is the target implementation for all ACES
transforms, using the ACES 1.3 Studio Config. The current Narkowicz ACES
approximation (used in VTK post-processing) will be replaced by OCIO-driven
transforms in the exhibition pipeline (Wave 11+). Target: < 2% dE2000 difference
between Narkowicz approximation and OCIO reference in the achromatic range.

**Critical:** The ACES RRT provides the highlight rolloff that prevents the
dirty near-white (#c8c8c8 in display space) from hard-clipping. The rolloff
curve must be verified -- if it compresses the top of the achromatic ramp,
the contamination gradient is lost.

---

## Achromatic Discipline Toolkit

### Channel Enforcement

R = G = B at every pixel. This is not a suggestion -- it is the concept.

| Tier | Max Channel Divergence | Enforcement |
|------|----------------------|-------------|
| Exhibition | +- 2 levels (8-bit equivalent) | Blocking failure |
| Study | +- 5 levels | Concern |
| Sketch | Any | Not enforced |

### Measurement Protocol

1. Sample pixel values at 5 density levels (trace, low, medium, high, peak)
2. For each sample, compute max(R,G,B) - min(R,G,B)
3. Report divergence in 8-bit equivalent levels
4. Flag any pixel exceeding tier threshold

### No Color Temperature

Grey is grey. Not warm grey, not cool grey. No color temperature shift from
lighting, from compositing, from display transform. If the ODT introduces
a cool shift in shadows or warm shift in highlights, compensate.

### Contamination Control

"Dirty near-white" is a luminance property, not a chrominance property.
The contamination of the peak (#c8c8c8) is that it never reaches clean white
(#ffffff) -- the luminance is suppressed. This is NOT achieved by adding
color. The grey remains perfectly neutral.

### Gamut Verification

All pixel values must fall on the neutral axis in CIE xy (x = 0.3127,
y = 0.3290 for D65, within measurement tolerance). Any deviation from the
neutral axis indicates chromatic contamination.

---

## Log-Space Grading

Two adjustment controls operate in log space for perceptual uniformity:

### Clarity

Mid-tone contrast adjustment. Operates on the log-encoded density-to-luminance
curve without affecting blacks or peak whites. Increases separation between
density levels in the medium range.

- Positive clarity: more internal structure visible, stronger depth reading
- Negative clarity: softer transitions, less confrontational
- Range: -1.0 to +1.0 (0.0 = neutral)

### Contamination (grading control)

Adjusts the relationship between peak density and peak luminance in log space.
Distinct from the density-to-dread Contamination axis -- this is a
post-render grading operation.

- Higher: peak luminance closer to #c8c8c8 (dirtier)
- Lower: peak luminance closer to #9e9e9e (darker, less contaminated)
- Range: 0.0 to 1.0

---

## Deep Compositing Considerations

### AOV Separation

| AOV | Content | Use |
|-----|---------|-----|
| Emission | TF color contribution | Primary beauty pass in emission mode |
| Absorption | Light absorbed per sample | Volumetric holdout and density verification |
| Residual | Remaining light after volume | Background integration |

### Compositing Rules

- **Alpha**: premultiplied throughout. Never straight alpha in the compositing chain.
- **Deep merge**: front-to-back with proper absorption weighting.
- **Log-space operations**: Clarity and Contamination adjustments in log space preserve perceptual uniformity across the density range.
- **Flatten**: deep-to-flat conversion only at final output.

### Color Space Chain

```
Renderer (linear) -> ACEScg working space -> log-space grading -> ACEScg
  -> ACES RRT -> ODT (Rec.709 or P3-D65) -> display
```

No color space conversions between compositing operations. All operations
in ACEScg until the final display transform.
