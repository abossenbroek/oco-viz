---
name: show-lut
user-invocable: false
type: instruction
primary_owner: colorist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Show LUT — One Base, Minimal Trims, Invisible Grades

One base LUT per project, then minimal per-shot trims. The viewer should never notice
the grade. A visible grade is a failed grade. The show LUT defines the overall tonal
character of the project — the relationship between scene-referred values and the
emotional tone of the final image. It is the bridge between the ACES technical pipeline
and the creative vision encoded in the visual bible.

> "The best color correction is the one nobody notices."

---

## Principle

The show LUT is the colorist's primary creative tool. It establishes the base tonality,
contrast character, and color bias for the entire project. Per-shot CDL trims are
refinements measured in fractions of a stop — they correct for lighting variations, not
for creative direction. If a shot requires more than +-0.3 stops of CDL correction, the
problem is upstream (lighting, exposure, material) and must be fixed there, not
compensated in the grade.

The show LUT operates in ACEScg space and is applied as an OCIO view transform. It does
not replace the ACES Output Transform — it augments it with project-specific tonal
character. The base LUT is validated against an achromatic target to ensure neutral gray
maps to neutral gray (no unintended color bias).

---

## Procedure

### Step 1 — Create Base LUT from Material Research

The base LUT is derived from the visual bible's material research, not from aesthetic
preference. The tonal character should match what the specified materials produce under
the specified lighting:

1. Render a reference scene using the visual bible's material presets and lighting rigs
2. Compare the rendered tonality against the material reference photographs
3. Author the base LUT to match the photographed tonal character
4. The LUT should make the rendered materials feel like the real-world references

### Step 2 — Validate Against Achromatic Target

The base LUT must pass the achromatic compliance test:

| Test | Input | Expected Output | Tolerance |
|------|-------|-----------------|-----------|
| Pure black | (0.0, 0.0, 0.0) | (0.0, 0.0, 0.0) | Exact |
| 18% gray | (0.18, 0.18, 0.18) | Neutral gray (equal RGB) | +- 0.005 |
| Pure white | (1.0, 1.0, 1.0) | Near-white (equal RGB) | +- 0.01 |
| Mid-tone ramp | Achromatic 0.0-1.0 | Monotonic, equal RGB | +- 0.005 |

If any achromatic input maps to a chromatic output, the base LUT has an unintended
color bias that must be corrected before the LUT is distributed.

### Step 3 — Author CDL Trims

CDL (ASC Color Decision List) trims are per-shot corrections applied on top of the base
LUT. They operate in ACEScct space and are limited to small adjustments:

| CDL Parameter | Allowed Range | Purpose |
|---------------|--------------|---------|
| Slope (R, G, B) | 0.7 - 1.3 (+-0.3) | Exposure correction per channel |
| Offset (R, G, B) | -0.3 - +0.3 | Lift / shadow color bias |
| Power (R, G, B) | 0.7 - 1.3 (+-0.3) | Gamma / mid-tone response |
| Saturation | 0.8 - 1.2 | Global saturation adjustment |

If a shot requires CDL values outside these ranges, the shot has a lighting or material
problem that must be fixed at the source.

### Step 4 — Distribute to All Agents

The show LUT and CDL trims are shared pipeline assets:

1. Base LUT file: `luts/show_base.spi3d` (or `.cube`)
2. CDL file: `grades/show_cdl.yml` (per-shot entries)
3. OCIO config updated to include show LUT as a view transform
4. All agents reference the same OCIO config — no per-agent LUT overrides

---

## Show LUT Types

### Soot Base

**Character:** Achromatic, dirty near-white peak, compressed highlights, deep open
shadows. The tonality of carbon — everything is dark, but the darkness has texture.

**Tonal curve:** Slight S-curve with compressed highlights rolling off at 85% of peak
display value. Shadows open (not crushed) to preserve soot texture detail. Near-white
peak at (0.82, 0.82, 0.82) — never pure white, because soot absorbs.

```yaml
show_lut_type: soot_base
peak_white: [0.82, 0.82, 0.82]    # dirty white — soot absorbs
black_point: [0.0, 0.0, 0.0]       # true black — void is void
mid_gray_response: 0.18             # standard 18% gray response
highlight_rolloff: soft              # compressed, never clipped
shadow_character: open               # textured shadows, not crushed
saturation_bias: 0.0                 # achromatic — no saturation shift
achromatic_compliance: true          # neutral gray stays neutral
```

### Skip Bleach

**Character:** Desaturated highlights, preserved shadow saturation, reduced contrast in
upper tonal range. Creates an arid, harsh, photochemical feel. Based on the FotoKem
skip-bleach process (see `color-science/skip-bleach` skill).

```yaml
show_lut_type: skip_bleach
peak_white: [0.88, 0.88, 0.86]    # desaturated, slightly warm peak
black_point: [0.0, 0.0, 0.0]       # maintained true black
mid_gray_response: 0.20             # slightly lifted mid-tones
highlight_rolloff: aggressive        # flattened highlights
shadow_character: preserved          # shadows retain saturation
saturation_bias: -0.15               # global desaturation, stronger in highlights
achromatic_compliance: false         # intentional warm shift in highlights
```

---

## Parameters

### Base LUT Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `peak_white` | [float, float, float] | [0.82, 0.82, 0.82] | [0.7, 0.7, 0.7] - [1.0, 1.0, 1.0] | Maximum output value |
| `black_point` | [float, float, float] | [0.0, 0.0, 0.0] | [0.0, 0.0, 0.0] - [0.03, 0.03, 0.03] | Minimum output value |
| `mid_gray_response` | float | 0.18 | 0.12 - 0.25 | Output level for 18% gray input |
| `highlight_rolloff` | string | soft | soft / aggressive | Highlight compression character |
| `shadow_character` | string | open | open / crushed / lifted | Shadow tonal behavior |
| `saturation_bias` | float | 0.0 | -0.3 - 0.3 | Global saturation shift |
| `achromatic_compliance` | bool | true | -- | Whether LUT preserves achromatic neutrality |

### CDL Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `slope` | [float, float, float] | [1.0, 1.0, 1.0] | [0.7, 0.7, 0.7] - [1.3, 1.3, 1.3] | Per-channel exposure |
| `offset` | [float, float, float] | [0.0, 0.0, 0.0] | [-0.3, -0.3, -0.3] - [0.3, 0.3, 0.3] | Per-channel lift |
| `power` | [float, float, float] | [1.0, 1.0, 1.0] | [0.7, 0.7, 0.7] - [1.3, 1.3, 1.3] | Per-channel gamma |
| `saturation` | float | 1.0 | 0.8 - 1.2 | Global saturation multiplier |

### Distribution Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lut_format` | string | spi3d | LUT file format (spi3d, cube) |
| `lut_resolution` | int | 65 | 3D LUT resolution (33, 49, 65) |
| `cdl_format` | string | yaml | CDL file format |
| `ocio_integration` | bool | true | Auto-register in OCIO config |

---

## Anti-Patterns

### 1. The Per-Shot LUT

**Symptom:** Every shot has its own base LUT with different tonal character, contrast
curve, and color bias. The sequence feels like a slideshow of different looks instead of
a unified film.

**Cause:** Treating the show LUT as a per-shot creative tool instead of a project-level
tonal contract. "This shot needs a different feel" is solved with CDL trims, not a new
base LUT.

**Fix:** One base LUT for the entire project. Per-shot differences are expressed as CDL
trims within the +-0.3 range. If a shot genuinely cannot conform to the base LUT, the
problem is in the lighting or material, not the grade.

### 2. The Heavy Grade

**Symptom:** CDL values are far outside the +-0.3 range — slope of 0.5, offset of -0.8,
power of 2.0. The grade is doing the work of lighting and material correction, creating
artifacts, noise amplification, and color shifts.

**Cause:** Using the CDL to compensate for upstream problems (wrong exposure, wrong
material, wrong lighting) instead of fixing the source.

**Fix:** If CDL values exceed +-0.3 on any parameter, reject the shot back to lighting
or material. The CDL is for fine-tuning, not for rescue operations. A heavy CDL always
produces worse results than fixing the render.

### 3. The Visible Grade

**Symptom:** A viewer watching the sequence can perceive the transition between shots
as a color or contrast change. The grade calls attention to itself instead of serving
the story.

**Cause:** CDL trims that are too aggressive, inconsistent base LUT application, or
per-shot LUTs creating visual discontinuity.

**Fix:** Watch the sequence in real-time playback. If any shot transition produces a
visible color or contrast shift, reduce the CDL trim or equalize the upstream lighting.
The grade should be invisible — the viewer should feel the emotion without noticing the
mechanism.

### 4. The Unvalidated LUT

**Symptom:** The show LUT introduces an unintended color bias — shadows are slightly
blue, highlights are slightly yellow — that was not part of the creative intent. The bias
is subtle enough to pass casual inspection but visible in achromatic test patches.

**Cause:** Skipping the achromatic compliance test (Step 2). The LUT was tuned visually
on saturated content and never tested against neutral gray ramps.

**Fix:** Run the achromatic compliance test on every revision of the base LUT. Neutral
gray must map to neutral gray within tolerance. If the LUT intentionally introduces
bias (as in the skip-bleach type), document it explicitly and set
`achromatic_compliance: false`.

---

## Validation Checklist

- [ ] One base LUT for the entire project (no per-shot base LUTs)
- [ ] Base LUT passes achromatic compliance test (or explicitly documented as non-compliant)
- [ ] Pure black (0,0,0) maps to pure black
- [ ] 18% gray maps to neutral gray within +-0.005
- [ ] CDL slope values within 0.7 - 1.3 (+-0.3 from unity)
- [ ] CDL offset values within -0.3 - +0.3
- [ ] CDL power values within 0.7 - 1.3
- [ ] CDL saturation within 0.8 - 1.2
- [ ] LUT registered in OCIO config as a view transform
- [ ] All agents reference the same OCIO config
- [ ] Real-time playback shows no visible grade transitions between shots
- [ ] Grading delivery conforms to `grading_delivery` schema from output-schemas
