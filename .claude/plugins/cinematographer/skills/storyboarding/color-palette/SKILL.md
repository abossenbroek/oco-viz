---
name: color-palette
user-invocable: false
type: instruction
primary_owner: storyboarder
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Color Palette — Emotional Color Design for Volumetric Sequences

Color tells the emotional story. Each sequence has a dominant palette, each shot a
palette variation. In achromatic work — the Soot aesthetic — color discipline is even
more critical because the palette operates in the narrow band between pure black and
dark gray, where tiny variations in hue, saturation, and value carry enormous weight.
A warm dark is not the same as a cool dark. A warm dark next to a cool dark creates
contrast that the viewer feels even if they cannot name it.

Greig Fraser's SHIFT process for Dune created palettes that felt physical — the orange
of Arrakis was not a color grade but a simulation of how desert sand interacts with
late-afternoon light through photochemical emulsion. For Soot-tier plumes the discipline
is the same: color emerges from material physics (coal, ash, char), not from artistic
preference.

> "Remove the software from yourself." — Deak Ferrand, Concept Artist, BR2049

---

## Principle

Color tells the emotional story. Each sequence has a dominant palette, each shot a
palette variation within that palette. For the Soot aesthetic: achromatic discipline
with carefully controlled contamination. The achromatic range (#000000 to #1A1A1A) is
NOT a single color — it contains an infinite landscape of warm-cool, red-blue,
green-absent variations that are felt more than seen.

The color palette is not a mood board pick. It is derived from material research: what
does coal dust look like under side-lighting? What color temperature does volcanic ash
reflect? What spectral absorption curve does industrial soot follow? These physical
facts determine the palette; the palette determines the emotion.

---

## Procedure

### Step 1 — Material-Derived Palette Generation

Begin with the visual bible's material references (see vermette-bible skill). For each
material, extract its color behavior under controlled illumination:

| Material | Dominant Wavelength | Undertone | Behavior Under Side-Light |
|----------|-------------------|-----------|--------------------------|
| Coal dust | 580-600nm (warm) | Red-orange, barely visible | Warm glints at specular angles |
| Volcanic ash | 460-500nm (cool) | Blue-gray, subtle | Cool scatter, no specular |
| Charcoal | Broadband absorber | Nearly neutral, slight warm | Very faint warm reflection at grazing angle |
| Industrial soot | Broadband absorber | True neutral, achromatic | No color response — absorbs all |
| Smoke | N/A (scatter) | Temperature of illumination | Takes on color of light source |
| Condensed water | N/A (scatter) | Cool blue at thickness | Rayleigh-biased scattering |

### Step 2 — Define Sequence Palette

Each sequence gets a palette specification with hierarchy:

```yaml
palette:
  sequence_id: SEQ-003
  name: "Soot Emergence — Industrial Dawn"

  # Dominant: 60-70% of frame area
  dominant:
    hex: "#080604"
    material: "coal dust core"
    role: "The mass — oppressive, warm-dark, absorbing"

  # Secondary: 20-30% of frame area
  secondary:
    hex: "#0E0C0A"
    material: "coal dust at density boundary"
    role: "The transition — where core meets halo"

  # Accent: 5-10% of frame area
  accent:
    hex: "#1A1614"
    material: "ash halo catching rim light"
    role: "The edge — where the plume meets the void"

  # Background: remaining frame area
  background:
    hex: "#000000"
    material: "void"
    role: "Negative space — pure absence"

  # Contamination: 0-3% — controlled color injection
  contamination:
    hex: "#1A1008"
    material: "furnace glow reflected in near-field particulate"
    role: "Temperature cue — warmth from the emission source"
    max_area: 0.03  # never more than 3% of frame
```

### Step 3 — Shot-Level Palette Variation

Within a sequence palette, each shot varies to serve its emotional beat:

| Beat | Palette Shift | Technique |
|------|--------------|-----------|
| Establish | Cooler, less contamination | Suppress warm undertones — neutral observation |
| Build | Warming slightly | Introduce coal-dust warmth as plume approaches |
| Tension | Maximum warm contamination | Furnace glow reaching maximum — heat and threat |
| Peak | Desaturate contamination, increase value contrast | Strip color, maximize tonal drama |
| Release | Return to cool, reduce contrast | Let the palette exhale — cool gray, softer |
| Coda | Near-neutral, minimal variation | Stillness — the palette settles to rest |

### Step 4 — Achromatic Contamination Control

In Soot-tier work, "contamination" is any deviation from pure achromatic. It must be:

1. **Material-motivated** — derived from a physical material's spectral behavior
2. **Spatially bounded** — never more than the specified max_area percentage
3. **Narratively purposeful** — the contamination tells you something (warmth from a
   furnace, coolness from altitude, toxicity from chemical composition)

Contamination hierarchy:

| Level | Saturation | Visible To | Use |
|-------|-----------|------------|-----|
| **Zero** | 0% | Nobody | Pure achromatic — Soot baseline |
| **Subliminal** | 1-3% | Trained colorists | Material undertone — coal warmth, ash coolness |
| **Perceptible** | 3-8% | Attentive viewers | Intentional color accent — furnace glow, sky scatter |
| **Dominant** | 8-15% | Everyone | Color statement — ONLY at peak beats |
| **Forbidden** | >15% | — | Violates Soot aesthetic — never in Soot tier |

### Step 5 — Palette Continuity Across Sequences

When sequences are viewed in order, their palettes must form a coherent meta-arc:

```
Sequence 1 (Dawn):     cool neutral → warm contamination → cool neutral
Sequence 2 (Day):      warm neutral → hot contamination → warm neutral
Sequence 3 (Dusk):     warm neutral → cool contamination → near-black
Sequence 4 (Night):    pure achromatic throughout

Meta-arc: overall warming from dawn to day, then cooling from dusk to night
         Contamination peaks in sequence 2, disappears by sequence 4
```

---

## Parameters

### Palette Structure Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `dominant_area_ratio` | float | 0.65 | 0.50 - 0.75 | Fraction of frame area for dominant color |
| `secondary_area_ratio` | float | 0.25 | 0.15 - 0.35 | Fraction for secondary color |
| `accent_area_ratio` | float | 0.07 | 0.03 - 0.15 | Fraction for accent color |
| `contamination_max_area` | float | 0.03 | 0.0 - 0.10 | Maximum contamination area (Soot: 0.03) |
| `palette_colors_max` | int | 5 | 3 - 7 | Maximum distinct colors in palette |

### Achromatic Control Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_saturation_soot` | float | 0.08 | 0.0 - 0.15 | Maximum saturation for Soot tier |
| `max_saturation_study` | float | 0.15 | 0.05 - 0.25 | Maximum saturation for Study tier |
| `max_saturation_exhibition` | float | 0.12 | 0.03 - 0.20 | Maximum saturation for Exhibition tier |
| `contamination_level` | enum | subliminal | zero, subliminal, perceptible, dominant | Contamination intensity |
| `dominant_value_max` | float | 0.06 | 0.02 - 0.12 | Maximum value (HSV V) for dominant color |
| `accent_value_max` | float | 0.12 | 0.06 - 0.20 | Maximum value for accent color |

### Material Derivation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `material_source_required` | bool | true | Every palette color must reference a material |
| `spectral_data_required` | bool | false | Require spectral absorption data (exhibition only) |
| `illumination_specified` | bool | true | Light source for material color must be documented |
| `warmth_direction` | enum | neutral | warm, cool, neutral | Overall palette temperature bias |

---

## Presets

### Coal Study

Warm achromatic palette derived from coal and charcoal materials. Minimal contamination
from furnace-motivated warm accents. For sequences emphasizing the plume's material
origin — combustion, emission, carbon.

```yaml
dominant:    { hex: "#080604", material: coal_dust, saturation: 0.02 }
secondary:   { hex: "#0E0C0A", material: charcoal, saturation: 0.01 }
accent:      { hex: "#1A1614", material: coal_dust_rimlit, saturation: 0.04 }
background:  { hex: "#000000", material: void }
contamination: { hex: "#1A1008", material: furnace_glow, max_area: 0.02, saturation: 0.06 }
warmth_direction: warm
max_saturation_soot: 0.06
```

### Ash Atmosphere

Cool achromatic palette derived from volcanic ash and atmospheric scatter. The plume
as geological event rather than industrial emission. For sequences emphasizing scale,
altitude, atmospheric behavior.

```yaml
dominant:    { hex: "#060608", material: volcanic_ash, saturation: 0.02 }
secondary:   { hex: "#0A0C0E", material: fine_particulate, saturation: 0.01 }
accent:      { hex: "#14161A", material: ash_scatter, saturation: 0.03 }
background:  { hex: "#000000", material: void }
contamination: { hex: "#080C14", material: rayleigh_scatter, max_area: 0.02, saturation: 0.05 }
warmth_direction: cool
max_saturation_soot: 0.05
```

### Pure Soot

Zero contamination. True achromatic. Every color is a gray value with no hue component.
For sequences demanding maximum tonal purity — the plume as pure form, stripped of all
material association.

```yaml
dominant:    { hex: "#060606", material: industrial_soot, saturation: 0.0 }
secondary:   { hex: "#0C0C0C", material: soot_boundary, saturation: 0.0 }
accent:      { hex: "#161616", material: soot_scatter, saturation: 0.0 }
background:  { hex: "#000000", material: void }
contamination: null  # no contamination permitted
warmth_direction: neutral
max_saturation_soot: 0.0
```

---

## Anti-Patterns

### 1. The Rainbow

**Symptom:** Too many colors in the palette. Each shot introduces a new hue. The
sequence reads as a color sampler rather than a focused statement. In achromatic work,
the equivalent: too many value levels creating a muddy, indistinct range.

**Cause:** Trying to create visual interest through color variety rather than color
discipline. More colors do not mean more emotion — they mean less. Dilution of palette
dilutes emotional focus.

**Fix:** Limit the palette to 5 colors maximum (dominant, secondary, accent, background,
contamination). In Soot tier, the effective palette is often 3 colors: dark, less dark,
void. Variety comes from spatial distribution and temporal change, not from adding more
colors.

**Fraser reference:** On Dune, Greig Fraser limited the Arrakis palette to three tones:
sand (warm midtone), sky (cool highlight), shadow (deep neutral). An entire planet
defined by three colors.

### 2. The Flat Gray

**Symptom:** Achromatic without variation. Every dark area reads as the same gray. There
is no warmth-coolness modulation, no value rhythm, no material character. The image is
technically achromatic but emotionally dead.

**Cause:** Confusing achromatic discipline with absence of color thought. Achromatic
does not mean "no color decisions" — it means color decisions in the micro-range of
hue and saturation where 1% saturation at 2% value creates the difference between coal
and ash.

**Fix:** Use the material derivation process. Coal has a warm undertone (#080604 is not
the same as #060606). Ash has a cool undertone (#060608 is not the same as #060606).
These micro-differences, applied consistently, create material truth that the viewer
feels as texture and substance even if they cannot see it as "color."

### 3. The Unmotivated Accent

**Symptom:** A color accent appears in the palette — a warm glow, a cool highlight —
but it has no material source. It exists because the artist felt the image "needed a
pop of something." The accent is arbitrary.

**Cause:** Aesthetic intuition overriding material discipline. The accent may look good
but it does not belong in this physical world. It breaks the material contract.

**Fix:** Every accent must trace to a material source. The warm glow must come from a
furnace. The cool highlight must come from atmospheric scatter. If no material source
exists for the accent, the accent does not exist. Create visual interest through spatial
composition and value contrast, not through unmotivated color.

### 4. The Sequence Break

**Symptom:** Two consecutive sequences have dramatically different palettes with no
transitional logic. Sequence 1 is warm coal, Sequence 2 is cool ash, and the viewer
experiences the shift as an error rather than a progression.

**Cause:** Designing sequence palettes in isolation without considering the meta-arc.
Each sequence's palette was optimized individually, resulting in jarring transitions.

**Fix:** Plan the palette meta-arc across all sequences before finalizing individual
palettes. The shift from warm to cool should follow a narrative logic (time of day,
altitude change, material transformation). If the shift is intentional and dramatic,
use a dip-to-black transition at the sequence boundary to acknowledge the palette change.

### 5. The Grade-First Approach

**Symptom:** Color palette designed in color grading software by eyeballing values and
adjusting until it "looks right." No material references, no spectral data, no
physical motivation. The palette works visually but cannot be defended scientifically.

**Cause:** Treating color as a purely aesthetic domain rather than a physically-grounded
one. In conventional filmmaking this is standard practice. In science visualization it
is insufficient — every color choice should be traceable to physical reality.

**Fix:** Start with materials (Step 1), not with a grading tool. Extract color from
physical measurement, then use grading tools to refine within the material-defined
boundaries. The grade serves the physics; the physics does not serve the grade.

---

## Validation Checklist

- [ ] Every palette color has a material source reference
- [ ] Material sources include spectral or photometric properties (albedo, dominant wavelength)
- [ ] Illumination conditions documented for material color extraction
- [ ] Palette limited to 5 colors maximum (dominant, secondary, accent, background, contamination)
- [ ] Dominant color occupies 50-75% of frame area
- [ ] Contamination (if present) limited to max_area threshold (3% default for Soot)
- [ ] Maximum saturation within tier limit (8% Soot, 15% Study, 12% Exhibition)
- [ ] Shot-level palette variations serve emotional beats
- [ ] No two consecutive shots have identical palette (variation required)
- [ ] Palette meta-arc planned across all sequences
- [ ] Palette transitions between sequences are motivated (not arbitrary)
- [ ] Achromatic work has warm/cool modulation (not flat gray)
- [ ] No unmotivated accents — every color traces to a physical source
- [ ] Contamination level documented per shot (zero / subliminal / perceptible / dominant)
