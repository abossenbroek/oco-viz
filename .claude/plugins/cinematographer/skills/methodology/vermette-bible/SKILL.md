---
name: vermette-bible
user-invocable: false
type: methodology
primary_owner: production-designer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# The Vermette Bible — Visual World-Building Before Rendering

Patrice Vermette spent seven months in pre-production on Blade Runner 2049, building a
visual bible of over 130 keyframes before a single set was constructed. Every material,
color, texture, and spatial relationship was specified in advance. The camera would
arrive on set and discover a world that already existed in complete detail. For
volumetric CO2 visualization the same discipline applies: build the visual world on
paper — materials, palettes, spatial rules, emotional intent — before a single voxel
renders.

> "We designed everything. Every object in every room. Nothing was accidental."
> — Patrice Vermette, Production Designer, BR2049

---

## Principle

130+ keyframes before a single pixel renders. Build the world on paper before
committing to code. The visual bible is not a mood board of inspirational images — it
is a rigorous specification document that defines materials, spatial relationships,
color palettes, and emotional intentions with enough precision that any member of the
team can implement a render that belongs in the same world.

Vermette's approach is brutalist in the truest sense: form follows function, every
element serves a purpose, nothing decorative survives unless it also communicates. The
spatial creativity lies in what is removed as much as what is placed. For Soot-tier
plumes this means: achromatic discipline, geological material references, and a pattern
language derived from combustion physics rather than aesthetic preference.

---

## Procedure

### Step 1 — Collect Physical Material References

Before any digital work, assemble real-world material references that define the visual
vocabulary. These are not mood images — they are material specifications with measurable
properties.

For CO2/Soot visualization:

| Material | Source | Properties to Record |
|----------|--------|---------------------|
| Coal dust | Mining/geology reference | Albedo 0.04-0.08, grain 0.1-0.5mm, warm undertone |
| Volcanic ash | Geological surveys | Albedo 0.10-0.15, grain 0.01-0.1mm, cool gray |
| Charcoal | Combustion reference | Albedo 0.02-0.05, irregular grain, pure achromatic |
| Industrial soot | Emission studies | Albedo 0.01-0.03, sub-micron, absorbs all wavelengths |
| Smoke plume | Atmospheric photography | Density gradients, scattering behavior, edge character |
| Fog bank | Meteorological reference | Low-density scatter, uniform internal structure |

### Step 2 — Create Keyframe Descriptions

Each keyframe specifies a single rendered view with full context. Minimum fields:

```yaml
keyframe:
  id: KF-042
  title: "Soot Plume — Industrial Dawn"
  tier: exhibition
  emotional_intent: "Oppressive mass emerging from darkness, first light catching the upper halo"

  color_palette:
    dominant: "#0A0A0A"    # near-black core
    secondary: "#1A1816"   # warm shadow (coal dust undertone)
    accent: "#2E2A24"      # halo edge where scatter catches light
    background: "#000000"  # void

  material_reference:
    primary: "coal dust at 200x magnification — granular, warm-dark"
    secondary: "volcanic ash cloud — cool gray, fine particulate"

  spatial_rules:
    plume_fills_frame: 0.6   # fraction of frame occupied by plume
    horizon_line: 0.7        # lower third — plume rises into upper frame
    depth_layers: 3          # foreground haze, mid plume, background void

  lighting_motivation: "Pre-dawn sky — cool rim from above, no direct sun yet"
  camera: "Static wide — let the plume's motion be the only movement"
```

### Step 3 — Establish Spatial Rules

Define the spatial grammar that governs all keyframes in this world:

| Rule | Specification | Rationale |
|------|---------------|-----------|
| Plume-to-void ratio | 40-70% plume, 30-60% void | Void is not empty — it is negative space that gives the plume weight |
| Horizon placement | Lower third (0.6-0.8) | Plume rises, viewer looks up — conveys scale and oppression |
| Depth layering | Minimum 3 layers | Foreground particulate, mid volume, background void/atmosphere |
| Edge character | Wispy, fractal, never hard | Hard edges read as CG; fractal edges read as physical |
| Symmetry | Avoid bilateral symmetry | Nature is asymmetric; symmetry reads as artificial |
| Scale reference | Include when possible | A known-size element (terrain, structure) grounds the plume |

### Step 4 — Define Pattern Language

The pattern language is a set of recurring visual motifs that create coherence across
the entire visual bible:

**Soot Pattern Language:**

| Pattern | Description | Use |
|---------|-------------|-----|
| The Pillar | Vertical density column, narrow base expanding upward | Emission point emphasis |
| The Anvil | Wide horizontal spread at altitude, dark base | Atmospheric cap, scale |
| The Wisp | Thin tendril detaching from main body | Edge detail, fragility |
| The Void Window | Gap in the plume revealing background | Compositional punctuation |
| The Ground Haze | Low-lying density layer | Depth, environmental context |
| The Scatter Crown | Bright halo at plume top from backlight | Atmospheric beauty, hope |

---

## Parameters

### Keyframe Specification Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `keyframes_exhibition` | int | 12 | 12 - 50 | Minimum keyframes for exhibition tier |
| `keyframes_study` | int | 6 | 6 - 20 | Minimum keyframes for study tier |
| `keyframes_sketch` | int | 3 | 3 - 10 | Minimum keyframes for sketch tier |
| `palette_colors_max` | int | 5 | 3 - 7 | Maximum colors in a single keyframe palette |
| `material_refs_min` | int | 2 | 1 - 5 | Minimum material references per keyframe |

### Material Research Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `albedo_measured` | bool | true | Material albedo must be from measured data |
| `grain_size_recorded` | bool | true | Grain size must be documented |
| `absorption_spectrum` | bool | false | Full absorption spectrum (exhibition only) |
| `scattering_profile` | bool | true | Scattering behavior documented |

### Spatial Grammar Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `plume_frame_ratio_min` | float | 0.40 | 0.2 - 0.6 | Minimum plume-to-frame ratio |
| `plume_frame_ratio_max` | float | 0.70 | 0.5 - 0.9 | Maximum plume-to-frame ratio |
| `horizon_line_min` | float | 0.60 | 0.3 - 0.7 | Minimum horizon placement (fraction from top) |
| `horizon_line_max` | float | 0.80 | 0.6 - 0.9 | Maximum horizon placement (fraction from top) |
| `depth_layers_min` | int | 3 | 2 - 5 | Minimum depth layers per keyframe |
| `bilateral_symmetry_max` | float | 0.15 | 0.0 - 0.25 | Maximum bilateral symmetry score (0=random, 1=mirror) |

---

## Presets

### Soot Bible

Achromatic discipline. Materials drawn from coal geology and combustion chemistry.
No color beyond what carbon physics produces. Warm darks from coal, cool grays from
ash, pure blacks from soot.

```yaml
palette_mode: achromatic
dominant_range: "#020202 - #0A0A0A"
secondary_range: "#0A0808 - #1A1816"  # warm carbon undertone allowed
accent_range: "#1A1A1A - #2E2A24"
background: "#000000"
material_refs:
  - coal_dust:    { albedo: [0.04, 0.08], grain_mm: [0.1, 0.5], temp: warm }
  - volcanic_ash: { albedo: [0.10, 0.15], grain_mm: [0.01, 0.1], temp: cool }
  - charcoal:     { albedo: [0.02, 0.05], grain_mm: irregular, temp: neutral }
  - soot:         { albedo: [0.01, 0.03], grain_mm: submicron, temp: neutral }
pattern_language: [pillar, anvil, wisp, void_window, ground_haze]
```

### Industrial Bible

Metallic, worn, patinated. Materials drawn from heavy industry — rusted steel, oxidized
copper, oil-stained concrete. Color permitted but desaturated and motivated by material
chemistry.

```yaml
palette_mode: desaturated
dominant_range: "#0D0B09 - #1A1614"
secondary_range: "#1A1410 - #2E2620"  # warm oxide tones
accent_range: "#3A2E24 - #4A3E34"     # patina highlight
background: "#000000"
material_refs:
  - rusted_steel: { albedo: [0.12, 0.20], texture: pitted, temp: warm }
  - oil_concrete: { albedo: [0.08, 0.14], texture: mottled, temp: neutral }
  - copper_oxide: { albedo: [0.15, 0.25], texture: layered, temp: cool-green }
pattern_language: [pillar, anvil, wisp, void_window, ground_haze, scatter_crown]
```

---

## Anti-Patterns

### 1. The Mood Board

**Symptom:** A collection of aesthetically pleasing images from Google/Pinterest/Behance
presented as "visual reference" without any material specifications, measured properties,
or spatial rules. The images evoke a feeling but provide no implementable information.

**Cause:** Confusing inspiration with specification. A mood board says "it should feel
like this." A visual bible says "the albedo is 0.04, the grain size is 0.1mm, the
dominant wavelength absorption is 450nm."

**Fix:** For every reference image, extract measurable properties. What is the material?
What is its albedo? What is the grain structure? What is the color temperature of the
illumination? The image is a starting point; the specification is the deliverable.

**Vermette reference:** The BR2049 visual bible contained fabric swatches, paint chips,
material samples, and architectural drawings — not screenshots from other films.

### 2. The Premature Render

**Symptom:** Rendering begins before the visual bible is complete. Early renders
establish a "look" that constrains subsequent design decisions. The tail wags the dog.

**Cause:** Impatience, pressure to show progress, excitement about the tooling. "Let's
just try something and see how it looks." This locks in arbitrary decisions that should
have been deliberate.

**Fix:** Bible completion is a gate. No render configuration is written until the
bible has the required number of keyframes (12 for exhibition, 6 for study, 3 for
sketch). The discipline of specification forces the clarity that produces good renders.

### 3. The Borrowed World

**Symptom:** The visual bible references another project's look — "we want it to look
like Blade Runner 2049" or "like Dune" — without translating that reference into
specific material and spatial specifications for THIS project's data.

**Cause:** Using another film's visual language as a shortcut instead of building an
original vocabulary from the data and subject matter. CO2 plumes have their own material
physics, their own color behavior, their own spatial characteristics. They deserve their
own visual bible.

**Fix:** Use reference films for methodology (HOW Vermette built his bible) not
vocabulary (WHAT his bible contained). Build the CO2 visual bible from combustion
physics, atmospheric science, and geological material references.

### 4. The Incomplete Specification

**Symptom:** Keyframes specify color and composition but omit material properties,
lighting motivation, or emotional intent. The artist implementing the render must guess
at the designer's intention.

**Cause:** Selective specification — documenting the easy parts (color hex values) while
skipping the hard parts (why this color, from what material, with what lighting).

**Fix:** Every keyframe must pass the completeness check: can a different artist, with
no access to the designer, implement a render that belongs in this world? If any field
requires guesswork, the keyframe is incomplete.

### 5. The Static Bible

**Symptom:** The visual bible is created once at the start of the project and never
updated as the data, pipeline, and creative understanding evolve. New renders diverge
from the bible without the bible being amended.

**Cause:** Treating the bible as a pre-production artifact rather than a living document.

**Fix:** The visual bible is versioned alongside the code. When a render intentionally
diverges from a keyframe specification, the bible is updated to reflect the new creative
direction. Divergence without amendment is a continuity error.

---

## Validation Checklist

- [ ] Required number of keyframes created (12/6/3 per tier)
- [ ] Every keyframe has all required fields: id, title, tier, emotional_intent, color_palette, material_reference, spatial_rules, lighting_motivation, camera
- [ ] Material references include measured properties (albedo, grain size)
- [ ] Color palettes limited to 5 colors maximum per keyframe
- [ ] Spatial rules specify plume-to-void ratio, horizon placement, depth layers
- [ ] Pattern language defined with named patterns and descriptions
- [ ] No bilateral symmetry score exceeds threshold (0.15 default)
- [ ] Bible completed before any render configuration is written
- [ ] Every reference image has extracted material specifications (not just "vibes")
- [ ] Bible is version-controlled and updated when creative direction changes
- [ ] Completeness test passed: could another artist implement from this spec alone?
- [ ] Material palette derived from subject-matter physics, not borrowed from other projects
