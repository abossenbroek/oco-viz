---
name: fraser-shift
user-invocable: false
type: methodology
primary_owner: colorist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# The Fraser SHIFT — Digital-Film-Digital Color Pipeline

Greig Fraser shot Dune on the Arri Alexa LF but insisted the image pass through
photochemical film as an intermediate step. The SHIFT process (named for the optical
printer used) recorded the digital negative to 35mm Kodak Vision3 1-ASA stock,
chemically processed it, scanned it back, and match-graded in digital. The result was
not nostalgia or retro styling — it was organic photochemical characteristics embedded
in the image at a molecular level: halation from light bleeding through emulsion layers,
dye coupler interactions creating non-linear color relationships, physical gate weave
adding living imperfection, and grain structure that varies with exposure rather than
sitting as a flat overlay.

For our volumetric rendering pipeline, the SHIFT methodology means: design the color
pipeline to emulate photochemical characteristics through OCIO view transforms, not
through post-processing filters. The organic character should be built into the color
science, not bolted on as an afterthought.

> "It's not about making it look like film. It's about making it feel physical."
> — Greig Fraser, DP, Dune

---

## Principle

Imbue digital imagery with organic photochemical characteristics — halation, gate weave,
dye coupler interactions, exposure-dependent grain. These characteristics emerge from
the physics of photochemical processes and cannot be faithfully reproduced by flat
overlays or simple filters. The SHIFT approach integrates them into the color pipeline
itself, ensuring they interact with the image content rather than sitting on top of it.

The key insight: film grain is not noise. Halation is not bloom. Gate weave is not
camera shake. Each is a specific physical phenomenon with distinct mathematical
characteristics that differ fundamentally from their digital approximations. The SHIFT
methodology respects these differences.

---

## Procedure

### Step 1 — Grade in Digital (Linear / ACEScg)

Begin with a clean digital grade in linear colorspace. Establish the foundational
tonal relationships — density-to-luminance mapping, shadow depth, highlight behavior —
without any photochemical emulation. This is the "negative" that will be processed.

```
Input:  VTK render → EXR linear (ACEScg or scene-linear)
Grade:  Exposure, contrast, lift/gamma/gain per channel
Output: Graded linear EXR — the "digital negative"
```

### Step 2 — Define Film Stock Characteristics

Select the photochemical characteristics to emulate. Each stock has distinct behavior:

| Characteristic | Kodak Vision3 5254 (Dune) | Kodak 2383 Print | Fuji Eterna |
|----------------|---------------------------|-------------------|-------------|
| Halation radius | 8-12 px (at 4K) | 4-6 px | 6-8 px |
| Halation color | Warm (red-orange bleed) | Neutral | Cool-shifted |
| Gate weave amplitude | 0.2-0.5 px | N/A (print stock) | 0.3-0.6 px |
| Gate weave frequency | 0.5-2.0 Hz | N/A | 0.5-1.5 Hz |
| Grain structure | Fine, exposure-dependent | Medium, uniform | Very fine |
| Grain size (σ) | 0.8-1.2 px (at 4K) | 1.5-2.0 px | 0.6-0.9 px |
| Dye coupler: CMY cross | Moderate | Strong | Subtle |
| Shoulder rolloff | Gentle (wide latitude) | Hard (narrow) | Medium |
| Toe response | Extended (rich shadows) | Short | Medium |

### Step 3 — SHIFT Emulation via OCIO

Build the photochemical characteristics into OCIO view transforms rather than
post-processing steps. This ensures the characteristics interact with the image at
the color-science level:

```yaml
# OCIO config fragment for SHIFT emulation
colorspaces:
  - !<ColorSpace>
    name: shift_negative
    description: "Digital negative with film stock response curve"
    from_scene_reference: !<GroupTransform>
      children:
        # Film stock response curve (H&D / sensitometric)
        - !<FileTransform> { src: "luts/kodak_5254_response.spi1d" }
        # Dye coupler cross-talk matrix
        - !<MatrixTransform> { matrix: [1.0, 0.04, 0.02, 0,
                                         0.03, 1.0, 0.04, 0,
                                         0.01, 0.03, 1.0, 0,
                                         0, 0, 0, 1] }
        # Shoulder and toe shaping
        - !<FileTransform> { src: "luts/kodak_5254_shoulder_toe.spi1d" }

displays:
  sRGB:
    - !<View>
      name: "SHIFT Grade"
      colorspace: shift_negative
      looks: "+shift_halation, +shift_grain"
```

### Step 4 — Halation Pass

Halation is light bleeding through the emulsion base and reflecting back, causing
bright areas to glow into adjacent regions. It is NOT bloom — bloom is an optical
lens effect; halation is a photochemical emulsion effect. Key differences:

| Property | Halation | Bloom |
|----------|----------|-------|
| Source | Emulsion backscatter | Lens diffraction |
| Color | Warm-shifted (red channel dominant) | Neutral / lens-coating dependent |
| Falloff | Exponential, soft | Gaussian, even |
| Interaction | Exposure-dependent (only in highlights) | Brightness-dependent (anywhere) |

```
HALATION: radius = 8-12px at 4K
          threshold = 0.8 (normalized, only bright areas)
          color_bias = [1.2, 0.9, 0.7]  # warm shift
          falloff = exponential, sigma = radius/3
          blend = additive, clamped to 1.0
```

### Step 5 — Gate Weave

Physical film moves through the gate with microscopic positional variation. This
creates a living, organic micro-motion that is fundamentally different from digital
camera shake or stabilization artifacts.

```
GATE_WEAVE: amplitude_x = 0.3 px    # horizontal shift
            amplitude_y = 0.2 px     # vertical shift
            frequency = 1.0 Hz       # primary oscillation
            noise_type = perlin      # not random — smooth organic motion
            correlation = 0.7        # successive frames are correlated
```

### Step 6 — Exposure-Dependent Grain

Film grain varies with exposure: shadows have more visible grain, highlights have less.
This is the opposite of digital noise (which is exposure-independent or highlight-biased).

```
GRAIN: base_size = 1.0 px (at 4K)
       shadow_mult = 1.5      # more grain in shadows
       midtone_mult = 1.0     # baseline
       highlight_mult = 0.4   # less grain in highlights
       color_variation = true  # RGB channels get different grain patterns
       temporal_stability = 0.3  # some grain persists frame-to-frame
```

### Step 7 — Match Grade

After applying SHIFT characteristics, perform a final match grade to ensure the
image reads as intended. The photochemical step should enhance the emotional read, not
distort it. Compare against the Step 1 digital grade and verify the SHIFT step added
character without altering the fundamental tonal and narrative intent.

---

## Parameters

### Film Stock Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `film_stock` | enum | kodak_5254 | kodak_5254, kodak_2383, fuji_eterna | Base film stock to emulate |
| `halation_radius` | float | 10.0 | 4.0 - 16.0 | Halation radius in pixels at 4K |
| `halation_threshold` | float | 0.8 | 0.6 - 0.95 | Normalized luminance threshold for halation |
| `halation_color_bias` | vec3 | [1.2, 0.9, 0.7] | — | RGB multiplier for halation warmth |
| `gate_weave_amplitude` | float | 0.3 | 0.0 - 0.6 | Gate weave displacement in pixels |
| `gate_weave_frequency` | float | 1.0 | 0.5 - 2.0 | Gate weave oscillation frequency (Hz) |

### Grain Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_base_size` | float | 1.0 | 0.5 - 2.0 | Base grain size in pixels at 4K |
| `grain_shadow_mult` | float | 1.5 | 1.0 - 3.0 | Grain intensity multiplier in shadows |
| `grain_midtone_mult` | float | 1.0 | 0.5 - 1.5 | Grain intensity multiplier in midtones |
| `grain_highlight_mult` | float | 0.4 | 0.1 - 0.8 | Grain intensity multiplier in highlights |
| `grain_color_variation` | bool | true | — | Different grain per RGB channel |
| `grain_temporal_stability` | float | 0.3 | 0.0 - 0.6 | Frame-to-frame grain persistence |

### Color Science Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `dye_coupler_strength` | float | 0.04 | 0.0 - 0.10 | CMY cross-talk intensity |
| `shoulder_rolloff` | float | 0.7 | 0.3 - 1.0 | Highlight shoulder softness (1.0 = gentle) |
| `toe_extension` | float | 0.6 | 0.2 - 1.0 | Shadow toe extension (1.0 = rich shadows) |
| `base_lut` | path | null | — | Custom 1D LUT for stock response curve |

---

## Presets

### Dune Skip Bleach

Fraser's custom process for Arrakis exteriors — skip bleach (bleach bypass) desaturates
and increases contrast, creating the parched, oppressive look of the desert planet.
For Soot-tier plumes this provides maximum tonal authority in the achromatic range.

```yaml
film_stock: kodak_5254
halation_radius: 10.0
halation_color_bias: [1.1, 0.95, 0.85]  # slightly warm
gate_weave_amplitude: 0.3
grain_base_size: 1.2
grain_shadow_mult: 2.0           # enhanced shadow grain — skip bleach effect
dye_coupler_strength: 0.02       # reduced — skip bleach suppresses coupler activity
shoulder_rolloff: 0.4            # hard shoulder — skip bleach increases contrast
toe_extension: 0.8               # extended toe preserved
saturation_reduction: 0.3        # 30% desaturation from bleach bypass
contrast_boost: 1.15             # skip bleach adds ~15% contrast
```

### Clean Negative

Minimal SHIFT — just the stock response curve and subtle dye coupler interaction,
no halation, weave, or grain. Useful for establishing the color science foundation
before adding physical characteristics.

```yaml
film_stock: kodak_5254
halation_radius: 0.0
gate_weave_amplitude: 0.0
grain_base_size: 0.0
dye_coupler_strength: 0.04
shoulder_rolloff: 0.7
toe_extension: 0.6
```

### Full SHIFT Exhibition

Maximum photochemical character for exhibition-quality output. Every characteristic
active at calibrated levels. The image should feel as though it was shot on film without
reading as "retro."

```yaml
film_stock: kodak_5254
halation_radius: 10.0
halation_threshold: 0.8
halation_color_bias: [1.2, 0.9, 0.7]
gate_weave_amplitude: 0.4
gate_weave_frequency: 0.8
grain_base_size: 1.0
grain_shadow_mult: 1.5
grain_highlight_mult: 0.4
grain_color_variation: true
grain_temporal_stability: 0.3
dye_coupler_strength: 0.04
shoulder_rolloff: 0.7
toe_extension: 0.6
```

---

## Anti-Patterns

### 1. The Filter Approach

**Symptom:** Film grain applied as a flat overlay blended on top of the rendered image
in compositing. The grain has uniform intensity across shadows, midtones, and highlights.
It looks like noise, not photochemistry.

**Cause:** Using a static grain texture or uniform noise generator instead of modeling
the exposure-dependent grain response of photochemical emulsion. This is the compositing
shortcut — quick to implement, wrong in character.

**Fix:** Grain must be exposure-dependent: heavy in shadows, moderate in midtones, light
in highlights. Each RGB channel gets an independent grain pattern (photochemical dye
layers are physically separate). Grain must have temporal stability — not random noise
per frame but partially persistent structures.

**Fraser reference:** The SHIFT process produces grain through actual photochemical
processing — each molecule of silver halide responds independently to light exposure.
The grain is the image, not an overlay on the image.

### 2. The Nostalgia Trap

**Symptom:** The image looks "retro" — heavy grain, visible gate weave, strong color
shifts — as if attempting to recreate a 1970s film look. Viewers perceive a stylistic
choice rather than an organic quality.

**Cause:** SHIFT parameters set too aggressively. The photochemical characteristics
should be subliminal — they should make the image feel grounded and physical without the
viewer consciously noticing film-like qualities.

**Fix:** Reduce all SHIFT parameters until the characteristics are subliminal. The test:
show the image to someone who does not know about the SHIFT pipeline. They should
describe the image as "organic" or "grounded" — never as "film-like" or "retro." If
they notice the treatment, it is too strong.

### 3. The Technical Bypass

**Symptom:** SHIFT characteristics applied in post-processing as compositing operations
(overlay blend, luminance-keyed grain, gaussian bloom) instead of integrated into the
color science via OCIO transforms.

**Cause:** Treating SHIFT as a visual effect rather than a color science methodology.
Compositing operations do not interact correctly with the image's tonal response —
they operate on display-referred values rather than scene-referred values.

**Fix:** Build SHIFT into the OCIO pipeline. The stock response curve, dye coupler
matrix, and shoulder/toe shaping are view transforms. Halation and grain are looks
applied in scene-referred space. The order of operations matters: grade → stock response
→ halation → grain → display transform.

### 4. The One-Size-Fits-All

**Symptom:** A single SHIFT preset applied to every tier and every sequence regardless
of emotional intent or subject matter. The industrial furnace sequence and the
atmospheric scatter sequence both have identical photochemical treatment.

**Cause:** Treating SHIFT as a pipeline setting rather than a creative tool. Each
sequence may benefit from different stock characteristics — the furnace sequence might
use a harder shoulder for more contrast, while the atmospheric sequence might use an
extended toe for richer shadow detail.

**Fix:** SHIFT presets per sequence, derived from the visual bible's emotional intent.
The stock characteristics serve the story — a harsh scene gets harsh photochemistry, a
contemplative scene gets gentler treatment.

---

## Validation Checklist

- [ ] Digital grade completed in linear (ACEScg) before any SHIFT processing
- [ ] Film stock characteristics documented with measured properties (not guessed)
- [ ] SHIFT integrated via OCIO view transforms (not compositing operations)
- [ ] Halation implemented as emulsion backscatter (not optical bloom)
- [ ] Halation is exposure-dependent (threshold > 0.6 normalized)
- [ ] Gate weave uses smooth Perlin noise (not random per-frame offset)
- [ ] Grain is exposure-dependent: heavy shadows, light highlights
- [ ] Grain has per-channel variation (RGB channels independent)
- [ ] Grain has temporal stability (not fully random per frame)
- [ ] Match grade performed: SHIFT enhances but does not distort tonal intent
- [ ] Subliminal test: non-expert viewer describes image as "organic" not "film-like"
- [ ] SHIFT preset selected per sequence based on emotional intent
- [ ] No flat overlays or uniform noise generators used for grain
- [ ] Color pipeline order correct: grade → stock → halation → grain → display
