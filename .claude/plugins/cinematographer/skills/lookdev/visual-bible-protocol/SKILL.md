---
name: visual-bible-protocol
user-invocable: false
type: methodology
primary_owner: production-designer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Visual Bible Protocol — Contract Between Vision and Execution

The visual bible is the contract between creative vision and technical execution. Every
pixel answers to it. No render proceeds without a signed-off bible. No creative decision
survives without a keyframe that specifies it. The bible is not inspiration — it is
engineering documentation for the eye.

> "We designed everything. Every object in every room. Nothing was accidental."
> — Patrice Vermette, Production Designer, BR2049

---

## Principle

The visual bible is the single source of truth for every creative and technical decision
in a sequence. It bridges the gap between artistic intent and render implementation by
encoding color palettes, material references, emotional intent, spatial configurations,
and narrative purpose into machine-readable YAML. The bible must be complete before any
render configuration is authored. Completeness means: any team member can implement a
conforming render from the bible alone, without asking the production designer a single
question.

---

## Procedure

### Step 1 — Determine Tier and Keyframe Requirements

Establish the delivery tier first. Keyframe density scales with tier quality:

| Tier | Minimum Keyframes | Purpose |
|------|-------------------|---------|
| Exhibition | 12 | Gallery-quality, every shot fully specified |
| Study | 6 | Pre-visualization, major beats covered |
| Sketch | 3 | Proof of concept, core idea validated |

Each keyframe represents a distinct rendered view — not a variation, not a crop, not a
color grade of another keyframe. If two keyframes could be produced from the same render
pass with only post-processing changes, they count as one keyframe.

### Step 2 — Assemble Material Research

For every material in the visual vocabulary, collect measured physical properties. This
is material research, not a mood board. Each material entry must include:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Material identifier (e.g. "coal_dust") |
| `physical_reference` | string | Real-world source with measurement context |
| `albedo_range` | [float, float] | Measured reflectance range |
| `grain_size` | string | Particle/surface grain with units (e.g. "10-50um") |
| `scattering_behavior` | string | Dominant scattering mode (absorption, scatter, mixed) |
| `density_range` | string | Physical density with units (e.g. "1.3 g/cm3") |
| `shader_params` | object | VTK volume property mappings derived from measurements |

### Step 3 — Author Keyframe Specifications

Each keyframe is a complete render specification conforming to this structure:

```yaml
keyframe:
  id: string               # unique identifier (e.g. "KF-001")
  title: string            # descriptive title
  tier: string             # exhibition | study | sketch
  emotional_intent: string # what the viewer should feel

  color_palette:
    dominant: string       # hex — largest area of frame
    secondary: string      # hex — supporting tonal area
    accent: string         # hex — edge/highlight/detail
    background: string     # hex — void / negative space

  material_reference:
    primary: string        # material name + visual description
    secondary: string      # material name + visual description

  spatial_config:
    - element: string      # scene element identifier
      position: [float, float, float]  # world-space meters
      narrative_intent: string         # why this element is here

  lighting_motivation: string  # physical source of illumination
  camera: string               # camera behavior description
  narrative_purpose: string    # what this keyframe communicates in the sequence
```

### Step 4 — Validate Cross-Keyframe Coherence

Review the full keyframe set as a sequence:

- Do color palettes share a parent vocabulary (same material family)?
- Do spatial rules create a consistent world (same scale, same gravity)?
- Does the emotional arc across keyframes build a narrative?
- Are material references consistent — same coal dust in keyframe 3 and keyframe 11?

### Step 5 — Compile Visual Bible Document

Assemble the final `visual_bible_delivery` YAML conforming to the output-schemas
specification. Include:

- All keyframes in sequence order
- Complete material preset definitions
- Spatial configuration for every referenced element
- Tier designation
- Audit trail documenting research sources and creative decisions

---

## Parameters

### Keyframe Density Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `keyframes_exhibition` | int | 12 | 12 - 50 | Minimum keyframes for exhibition tier |
| `keyframes_study` | int | 6 | 6 - 20 | Minimum keyframes for study tier |
| `keyframes_sketch` | int | 3 | 3 - 10 | Minimum keyframes for sketch tier |

### Material Research Depth Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `material_refs_per_keyframe` | int | 2 | 1 - 5 | Minimum material references per keyframe |
| `albedo_measured` | bool | true | -- | Albedo must come from measured data |
| `grain_size_documented` | bool | true | -- | Grain size must be recorded with units |
| `scattering_profile_required` | bool | true | -- | Scattering behavior must be documented |
| `physical_density_required` | bool | false | -- | Physical density in g/cm3 (exhibition only) |

### Spatial Annotation Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `narrative_intent_required` | bool | true | -- | Every spatial element must state its narrative purpose |
| `position_units` | string | meters | -- | World-space coordinates in meters |
| `depth_layers_min` | int | 3 | 2 - 5 | Minimum distinct depth layers per keyframe |

### Keyframe Completeness Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `palette_colors_max` | int | 5 | 3 - 7 | Maximum colors in a single keyframe palette |
| `emotional_intent_required` | bool | true | -- | Every keyframe must declare emotional intent |
| `narrative_purpose_required` | bool | true | -- | Every keyframe must declare narrative purpose |
| `camera_specified` | bool | true | -- | Camera behavior must be described |
| `lighting_motivation_required` | bool | true | -- | Lighting must cite a physical source |

---

## Anti-Patterns

### 1. The Incomplete Bible

**Symptom:** Bible has fewer than the required number of keyframes for the declared
tier. Key beats in the sequence are unspecified — the implementer must invent creative
decisions that should have been designed.

**Cause:** Rushing to render before the bible is finished. Treating the bible as a
formality rather than a gate.

**Fix:** Enforce the keyframe count gate. Exhibition = 12 minimum. No render
configuration is authored until the bible passes the count check. Missing keyframes are
not a debt item — they are a blocking defect.

### 2. The Undocumented Material

**Symptom:** A material appears in keyframes with a name and a vague description ("dark
smoky texture") but no measured physical properties. The shader artist must guess at
albedo, grain size, and scattering behavior.

**Cause:** Skipping material research in favor of aesthetic intuition. The material
"looks right" on the mood board but has no physical basis.

**Fix:** Every material must have a `physical_reference` field pointing to a real-world
measurement source. If the albedo cannot be stated as a number, the material research is
incomplete. "Looks dark" is not a specification; "albedo 0.04 measured from bituminous
coal sample" is.

### 3. The Disconnected Keyframe

**Symptom:** A keyframe uses materials, palettes, or spatial rules that contradict other
keyframes in the same bible. The sequence feels like it was designed by different people
for different projects.

**Cause:** Authoring keyframes in isolation without cross-referencing the established
vocabulary. Each keyframe was internally consistent but externally incoherent.

**Fix:** After authoring all keyframes, perform a cross-coherence review (Step 4). Every
material, palette color, and spatial rule must trace to the shared vocabulary defined in
the bible's material and pattern sections.

### 4. The Unanchored Spatial Element

**Symptom:** A scene element is placed at a position without any explanation of why it
occupies that location. The composition works visually but has no narrative logic.

**Cause:** Spatial decisions driven by visual balance alone, without asking "what does
this placement tell the viewer?"

**Fix:** Every entry in `spatial_config` must include a `narrative_intent` field. "Plume
base at origin" is insufficient. "Plume base at origin — emission source is the story's
anchor, viewer orients to it as ground truth" gives the implementer context.

### 5. The Version-Frozen Bible

**Symptom:** The visual bible was completed in pre-production and never updated as
rendering revealed new possibilities or constraints. Renders diverge from the bible
without the bible being amended.

**Cause:** Treating the bible as a one-time deliverable rather than a living document
that evolves with the project.

**Fix:** Version the bible alongside the code. When a render intentionally diverges from
a keyframe, update the keyframe. Undocumented divergence is a continuity error.

---

## Validation Checklist

- [ ] Keyframe count meets tier threshold (exhibition >= 12, study >= 6, sketch >= 3)
- [ ] Every keyframe has all required fields: id, title, tier, emotional_intent, color_palette, material_reference, spatial_config, lighting_motivation, camera, narrative_purpose
- [ ] Every material has a `physical_reference` with measured properties
- [ ] Every material has documented albedo range (numeric, not descriptive)
- [ ] Every material has documented grain size with units
- [ ] Every spatial element has `narrative_intent` explaining its placement
- [ ] Color palettes limited to 5 colors maximum per keyframe
- [ ] Cross-keyframe coherence reviewed — shared vocabulary, consistent world
- [ ] Emotional arc across keyframe sequence builds a narrative
- [ ] Bible compiled as valid `visual_bible_delivery` YAML conforming to output-schemas
- [ ] Audit trail documents research sources and creative decision provenance
- [ ] Bible authored and approved before any render configuration is written
