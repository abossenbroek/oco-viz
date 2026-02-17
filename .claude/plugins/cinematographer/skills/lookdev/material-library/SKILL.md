---
name: material-library
user-invocable: false
type: instruction
primary_owner: production-designer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Material Library — Physically Referenced Soot Presets

Material research, not mood boards. Every material parameter cites a physical
measurement. Every albedo value traces to a published source or laboratory sample. Every
grain size is stated in micrometers with a plausible distribution. If a parameter cannot
be grounded in physical reality, it does not belong in the library.

> "The difference between a material and a texture is measurement."

---

## Principle

Materials in volumetric rendering are not surface descriptions — they are volume
interaction specifications. A soot material defines how photons are absorbed, scattered,
and transmitted through a particulate cloud. These behaviors are determined by physical
properties: particle size distribution, complex refractive index, mass density, and
morphology. The material library encodes these properties as shader parameters with full
provenance, so that every rendered voxel can be traced back to a real-world substance.

---

## Procedure

### Step 1 — Select Material from Library

Choose a preset that matches the creative intent for the sequence. Each preset
represents a real-world carbonaceous material with measured optical and physical
properties.

### Step 2 — Verify Physical Reference

Confirm the `physical_reference` field against the source. If the source is unavailable
or the measurements are disputed, flag the material for re-measurement. Do not use a
material whose physical reference cannot be verified.

### Step 3 — Map to VTK Volume Properties

Translate physical properties to VTK shader parameters using the `shader_params` block.
The mapping is:

| Physical Property | VTK Parameter | Conversion |
|-------------------|---------------|------------|
| Albedo | `diffuse_color` (RGB) | Uniform gray = [albedo, albedo, albedo] |
| Scattering behavior | `scattering_anisotropy` | Forward = positive g, isotropic = 0 |
| Mass density | `density_scale` | Scaled to volume resolution |
| Grain size | `noise_frequency` | Smaller grain = higher frequency |
| Absorption | `extinction_coefficient` | Higher absorption = higher extinction |

### Step 4 — Validate Against Reference Renders

Render a 128-cubed scout pass with the material applied. Compare against the physical
reference photograph:

- Does the overall brightness match the expected albedo?
- Does the scattering character match the expected behavior (forward vs isotropic)?
- Does the grain texture match the documented particle size?

---

## Material Presets

### Coal Dust

**Physical reference:** Bituminous coal particulate, 10-50 um grain, sampled from
mining dust collection systems. Warm-tinted due to trace iron oxide content.

| Property | Value | Source |
|----------|-------|--------|
| Albedo | 0.04 - 0.06 | Single-scatter albedo measurement, Bond & Bergstrom (2006) |
| Grain size | 10 - 50 um | Particle size distribution, mining safety literature |
| Scattering behavior | Absorption dominant | SSA < 0.1 at visible wavelengths |
| Mass density | ~1.3 g/cm3 | Bulk density of bituminous coal dust |
| Morphology | Angular, irregular fragments | SEM imagery of crushed coal |
| Undertone | Warm (trace Fe2O3) | Spectral reflectance shows 600-700nm shoulder |

```yaml
shader_params:
  diffuse_color: [0.05, 0.048, 0.044]   # warm-shifted achromatic
  density_scale: 1.3
  scattering_anisotropy: 0.15            # weakly forward
  extinction_coefficient: 12.0
  noise_frequency: 0.8                   # medium grain
  noise_amplitude: 0.15                  # moderate variation
```

### Volcanic Ash

**Physical reference:** Rhyolitic volcanic ash, 1-100 um grain, collected from
eruption fallout deposits. Cool gray with broad size distribution.

| Property | Value | Source |
|----------|-------|--------|
| Albedo | 0.08 - 0.12 | Reflectance measurements, Patterson (1981) |
| Grain size | 1 - 100 um | Broad distribution, tephra grain-size analysis |
| Scattering behavior | Mixed scatter/absorb | SSA 0.3-0.5, size-dependent |
| Mass density | 0.5 - 1.0 g/cm3 | Loose deposit bulk density |
| Morphology | Vesicular, pumice fragments | SEM shows gas bubble inclusions |
| Undertone | Cool neutral | Flat spectral reflectance, no chromatic shoulder |

```yaml
shader_params:
  diffuse_color: [0.10, 0.10, 0.10]     # neutral gray
  density_scale: 0.75
  scattering_anisotropy: 0.30            # moderately forward
  extinction_coefficient: 8.0
  noise_frequency: 1.5                   # fine + coarse mixed
  noise_amplitude: 0.25                  # high variation from broad distribution
```

### Charcoal Powder

**Physical reference:** Hardwood charcoal, ground to 5-200 um, laboratory grade.
Pure achromatic black with irregular grain structure.

| Property | Value | Source |
|----------|-------|--------|
| Albedo | 0.03 - 0.05 | Diffuse reflectance, Bohren & Huffman (1983) |
| Grain size | 5 - 200 um | Sieve analysis of ground charcoal |
| Scattering behavior | Absorption dominant | SSA < 0.08 at visible wavelengths |
| Mass density | 0.3 - 0.5 g/cm3 | Bulk density of powdered charcoal |
| Morphology | Porous, fractured cellular | Retains wood cellular structure |
| Undertone | Pure achromatic | No measurable chromatic reflectance |

```yaml
shader_params:
  diffuse_color: [0.04, 0.04, 0.04]     # pure achromatic
  density_scale: 0.4
  scattering_anisotropy: 0.10            # near-isotropic
  extinction_coefficient: 14.0
  noise_frequency: 0.5                   # coarse porous grain
  noise_amplitude: 0.30                  # high variation from porous structure
```

### Industrial Soot

**Physical reference:** Diesel exhaust particulate, 0.1-2 um primary particles
aggregating into fractal clusters. Strongest absorber of all presets.

| Property | Value | Source |
|----------|-------|--------|
| Albedo | 0.02 - 0.04 | Bond et al. (2013), black carbon review |
| Grain size | 0.1 - 2 um (primary), 10-500 um (aggregates) | TEM particle sizing |
| Scattering behavior | Strong absorption | SSA 0.15-0.25, dominated by absorption |
| Mass density | ~1.8 g/cm3 | Effective density of soot aggregates |
| Morphology | Fractal aggregates of nanospheres | TEM shows chain-like clusters |
| Undertone | Neutral to slightly cool | Absorption increases toward blue wavelengths |

```yaml
shader_params:
  diffuse_color: [0.03, 0.03, 0.032]    # near-black, faint cool shift
  density_scale: 1.8
  scattering_anisotropy: 0.45            # forward-biased (Mie regime)
  extinction_coefficient: 18.0
  noise_frequency: 3.0                   # very fine grain (sub-micron primary)
  noise_amplitude: 0.10                  # low variation at macro scale
```

---

## Parameters

### Per-Material Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `diffuse_color` | [float, float, float] | [0.0, 0.0, 0.0] - [0.15, 0.15, 0.15] | Linear RGB base reflectance |
| `density_scale` | float | 0.1 - 3.0 | Volume density multiplier |
| `scattering_anisotropy` | float | -0.5 - 0.8 | Henyey-Greenstein g parameter |
| `extinction_coefficient` | float | 1.0 - 25.0 | Combined absorption + scattering per unit density |
| `noise_frequency` | float | 0.1 - 5.0 | Procedural grain frequency (higher = finer) |
| `noise_amplitude` | float | 0.0 - 0.5 | Grain variation strength |

### Library Management Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `physical_reference_required` | bool | true | Every preset must cite a physical source |
| `albedo_tolerance` | float | 0.02 | Maximum deviation from measured albedo |
| `grain_size_units` | string | um | Micrometers as standard unit |
| `scattering_source_required` | bool | true | SSA must cite a measurement source |

---

## Anti-Patterns

### 1. The Digital Material

**Symptom:** A material preset has no `physical_reference` field or references a digital
source ("inspired by Blender soot preset"). Shader parameters were tuned by eye without
grounding in measured data.

**Cause:** Treating material authoring as a creative exercise rather than a translation
of physical measurement into shader parameters.

**Fix:** Every material must trace to a published measurement or laboratory sample. If a
measured source cannot be found for the desired look, find the closest real material and
document the artistic deviation explicitly.

### 2. The Clean Surface

**Symptom:** Material renders as perfectly uniform — no grain variation, no density
fluctuation, no surface imperfection. The volume looks synthetic and CG.

**Cause:** Setting `noise_amplitude` to 0 or near-zero, ignoring the physical reality
that all particulate materials have heterogeneous structure.

**Fix:** Consult the physical reference. Real soot, ash, and coal dust have measurable
grain size distributions. Set `noise_frequency` and `noise_amplitude` to match the
documented particle size range and morphology.

### 3. The Uncalibrated Albedo

**Symptom:** Material appears too bright or too dark relative to its physical reference.
The rendered volume does not match the expected visual density of the real-world substance.

**Cause:** Setting `diffuse_color` by visual intuition rather than mapping from the
measured albedo range.

**Fix:** Start with the midpoint of the measured albedo range as all three RGB channels.
Render a scout pass. Compare rendered brightness against the reference photograph under
similar illumination. Adjust within the measured range only.

### 4. The Universal Soot

**Symptom:** A single "soot" material is used for all sequences regardless of the
specific carbonaceous material being visualized. Coal dust and diesel exhaust render
identically despite having different optical properties.

**Cause:** Treating "soot" as a monolithic category instead of a family of materials
with distinct measured properties.

**Fix:** Select the specific preset that matches the emission source. Industrial soot
(diesel) has different albedo, grain size, and scattering behavior than coal dust or
volcanic ash. The library exists to encode these differences.

---

## Validation Checklist

- [ ] Every material preset has a `physical_reference` field citing a real-world source
- [ ] Albedo values fall within the documented measured range
- [ ] Grain size is stated in micrometers with a plausible distribution
- [ ] Scattering behavior (SSA) cites a measurement source
- [ ] Mass density is documented with units (g/cm3)
- [ ] Morphology is described from electron microscopy or equivalent observation
- [ ] `shader_params` values are derived from physical properties, not tuned by eye
- [ ] Scout-tier render compared against physical reference photograph
- [ ] No material uses `noise_amplitude` of 0.0 (all real materials have grain)
- [ ] Undertone (warm/cool/neutral) is justified by spectral reflectance data
- [ ] Library management: no duplicate presets for the same physical material
