# Lookdev Bible: Soot Crust

## Exhibition Visual Language Implementation Specification

**Version:** 1.0
**Visual Language:** Soot (see `plan/visual_language.yaml`)
**Subject:** Sasol Secunda 57 Mt/year CO2
**Aesthetic:** Anthropocene industrial dread, achromatic, internal smoldering

---

## Overview

This document specifies seven lookdev techniques that transform VTK-generated CO2 plume data into exhibition-grade volumetric imagery. Each technique targets a specific perceptual quality of the "Soot" visual language. Implementation follows the existing pipeline: VTK generation (oco-viz) to OpenVDB conversion to Houdini/Karma XPU rendering.

All techniques are **exhibition tier only** unless explicitly noted as tier-agnostic. Study tier uses the existing `soot.json` transfer function with basic noise. Exhibition tier uses `soot_exhibition.json` with the full lookdev stack described here.

### Transfer Function References

| Tier | File | Key Characteristics |
|------|------|---------------------|
| Study | `configs/transfer_functions/soot.json` | 6 color stops (0.0-1.0 linear), max opacity 0.85, wider density bands |
| Exhibition | `configs/transfer_functions/soot_exhibition.json` | 14 color stops (finer sampling at low density), max opacity 0.85, peak color 0.680 (dirty grey, never white), 23 opacity stops with steep low-density ramp |

**Key observation:** Exhibition TF has 2.3x more color stops and 3.8x more opacity stops than study, concentrating extra resolution in the low-density range (0.0-0.2) where the human eye is most sensitive to banding. The peak color at density 1.0 is `rgb(0.680, 0.680, 0.680)` -- intentionally suppressed below the study TF's `rgb(1.0, 1.0, 1.0)` to enforce the "dirty near-white, never clean white" principle from the visual language.

---

## Technique 1: Paper Grain Manifold

**Reference:** William Kentridge -- charcoal on black, grain of the substrate visible through the mark.

### Concept

A high-frequency, static 3D noise field subtracted from density before opacity evaluation. The noise does not advect with the plume -- it is a property of the rendering space itself, like the tooth of paper beneath charcoal. At low density the grain dominates, breaking continuous tone into discrete particles. At high density the grain is suppressed and the volume reads as solid soot.

### Implementation

**Noise generation:**

```
grain_field = fbm_3d(shape, octaves=8, lacunarity=2.2, gain=0.45, seed=FIXED)
```

- Uses the existing `fbm_3d` from `src/oco_viz/plume/noise.py` but at **8 octaves** (vs. 6 for plume turbulence) to push energy into higher frequencies.
- `lacunarity=2.2` (slightly above default 2.0) shifts more energy to fine scales.
- Seed is **fixed per shot** -- the grain manifold does not change between frames.

**Application:**

```
grain_weight = 1.0 - clamp(|grad(density)| / grad_max, 0, 1)
effective_density = density - grain_field * grain_amplitude * grain_weight
```

- `grain_amplitude`: 0.03-0.08 (wedge parameter). Higher values produce coarser, more visible grain.
- `grain_weight`: Inverse density gradient magnitude. Where gradient is steep (edges, structure), grain is suppressed. Where gradient is shallow (uniform interior), grain is maximally visible.
- `grad_max`: Maximum expected gradient magnitude, set per-volume (typically 95th percentile of `|grad(density)|`).

**Static property:** The grain field is generated once and does not advect. As the plume moves through the grain manifold, density regions that were previously smooth acquire grain when they enter low-gradient zones. This creates the impression that the rendering medium (the "paper") has texture independent of the content (the "charcoal").

### Wedge Parameters

| Parameter | Range | Default | Lock Criterion |
|-----------|-------|---------|----------------|
| grain_amplitude | 0.02 - 0.12 | 0.05 | Visible grain at density 0.1, invisible at density 0.8 |
| grain_octaves | 6 - 10 | 8 | High-frequency sparkle without aliasing |
| grain_lacunarity | 2.0 - 2.5 | 2.2 | Fine vs. coarse grain character |
| grain_seed | any integer | 7777 | Fixed per shot, varied between shots |

### Tier Behavior

- **Exhibition:** Full grain manifold, 8 octaves.
- **Study:** No grain (smooth volume falloff per `soot.json`).
- **Sketch:** No grain.

---

## Technique 2: Sedimentary Motion

**Reference:** Geological strata, coal seam layers, sediment deposition.

### Concept

Stratified noise with compressed vertical scale creates horizontal "shelves" of density variation within the plume. The plume reads as accumulated sediment layers rather than turbulent gas. Viscosity is mapped to density so that dense regions resist motion (heavy, geological) while sparse regions flow more freely (atmospheric dispersal).

### Implementation

**Noise field:**

```
sed_noise = fbm_3d(shape, octaves=5, lacunarity=2.0, gain=0.5, seed=SED_SEED)
```

Applied with anisotropic scaling before evaluation:

```
sample_coords = (x * 1.0, y * 0.1, z * 1.0)
```

The `0.1` Y-axis compression stretches noise vertically by 10x, creating horizontal bands/shelves.

**Viscosity mapping:**

```
viscosity = density^2.0
velocity_damped = velocity * (1.0 - viscosity * viscosity_strength)
```

- `viscosity_strength`: 0.3-0.7 (wedge). Controls how much dense regions resist deformation.
- Squared density exponent ensures viscosity increases non-linearly -- only truly dense regions become "geological". Sparse halos remain fluid.

**Shelf structure:** The compressed-Y noise creates banding visible in the plume's vertical cross-section. Combined with the viscosity damping, dense bands hold their shape while sparse inter-band regions shear and deform, producing the visual impression of sedimentary strata.

### Wedge Parameters

| Parameter | Range | Default | Lock Criterion |
|-----------|-------|---------|----------------|
| y_compression | 0.05 - 0.2 | 0.1 | Visible horizontal banding without obvious repetition |
| viscosity_strength | 0.2 - 0.8 | 0.5 | Dense regions hold shape for 3-5 seconds of motion |
| sed_octaves | 3 - 6 | 5 | Visible stratification at multiple scales |
| sed_amplitude | 0.1 - 0.4 | 0.25 | Subtle shelving, not overwhelming plume shape |

### Tier Behavior

- **Exhibition:** Full sedimentary motion with viscosity.
- **Study:** Optional reduced version (y_compression=0.2, 3 octaves).
- **Sketch:** Disabled.

---

## Technique 3: Curvature-Driven Emission

**Reference:** Replaces the naive `density * noise` emission model. Industrial combustion where oxygen availability at surfaces drives visible glow.

### Concept

Emission originates where fuel meets oxygen. In a dense plume, oxygen is depleted in the interior but available at surfaces and in vortex cores where mixing occurs. The emission field is:

```
emission = fuel * oxygen
```

Where:

- `fuel` = density (the CO2/soot itself is the fuel analog for visual purposes).
- `oxygen` = max(vorticity_magnitude, surface_curvature) -- regions of high rotational mixing OR high surface curvature where atmospheric oxygen can reach the fuel.

### Implementation

**Oxygen proxy via vorticity:**

```
vorticity = curl(velocity)
vorticity_mag = |vorticity|
```

Uses the existing `curl_noise_3d` from `src/oco_viz/plume/noise.py` or the actual velocity field vorticity if available from HYSPLIT/simulation data.

**Oxygen proxy via surface curvature:**

```
grad_d = gradient(density)
curvature = divergence(grad_d / |grad_d|)
```

Mean curvature of isodensity surfaces. High curvature = convex features (tips, filaments) where atmospheric mixing occurs.

**Combined oxygen field:**

```
oxygen = max(normalize(vorticity_mag), normalize(curvature))
```

**Emission calculation:**

```
emission = fuel * oxygen * emission_intensity
```

**Arrhythmic pulse (temporal modulation):**

```
pulse = sin(2*pi*0.2*t) * sin(2*pi*0.05*t)
emission *= (1.0 + pulse * pulse_amplitude)
```

The two-frequency beat creates an irregular, unsettling pulsation. The 0.2 Hz and 0.05 Hz frequencies are incommensurable, so the pattern never exactly repeats. `pulse_amplitude` controls how pronounced the flicker is (0.1-0.3 for subtle arrhythmia, 0.3-0.6 for visible throbbing).

### Wedge Parameters

| Parameter | Range | Default | Lock Criterion |
|-----------|-------|---------|----------------|
| emission_intensity | 0.5 - 3.0 | 1.5 | Visible glow at surfaces without blowout |
| pulse_amplitude | 0.05 - 0.6 | 0.2 | Arrhythmia perceptible but not distracting |
| freq_a | 0.1 - 0.3 | 0.2 | Slow beat frequency |
| freq_b | 0.03 - 0.08 | 0.05 | Ultra-slow modulation frequency |
| curvature_weight | 0.0 - 1.0 | 0.5 | Balance vorticity vs. curvature |

### MaterialX Starting Point

```xml
<standard_volume name="soot_emission">
  <input name="emission_color" type="color3" value="0.68, 0.68, 0.68" />
  <input name="emission" type="float" interfacename="emission_intensity" />
  <!-- emission driven by fuel*oxygen computed upstream in VEX/VOPs -->
</standard_volume>
```

Emission color is achromatic `(0.68, 0.68, 0.68)` matching the exhibition TF peak. No color -- only luminance variation.

### Tier Behavior

- **Exhibition:** Full curvature-driven emission with arrhythmic pulse.
- **Study:** Simple `density * noise` emission (current behavior).
- **Sketch:** No emission.

---

## Technique 4: Stochastic Ash Culling

**Reference:** Ash falling from industrial stacks, particles that appear and vanish stochastically.

### Concept

In the low-density "crumble zone" (density 0.0-0.2), voxels are not smoothly faded but instead undergo binary alpha culling against a blue noise threshold. Each voxel either fully exists or fully vanishes, producing the appearance of discrete ash particles rather than continuous fog.

### Implementation

**Blue noise threshold:**

```
blue_noise = load_blue_noise_3d(shape)  # pre-computed, tiled
threshold = remap(density, 0.0, 0.2, 1.0, 0.0)
alpha = 1.0 if blue_noise < threshold else 0.0
```

- For density < 0.0: alpha = 0 (fully transparent).
- For density 0.0-0.2: stochastic culling. Lower density = higher threshold = more culling.
- For density > 0.2: alpha = 1 (fully opaque to the normal TF pipeline). The TF opacity curve takes over.

**Blue noise properties:**

- Spatially uniform distribution (no clumping or voids at any scale).
- 3D tiled texture, 128^3 resolution, pre-computed.
- Temporally stable: same noise texture used every frame (no flickering).
- Can use Owen-scrambled Sobol or similar low-discrepancy sequence projected to 3D.

**Crumble zone width:** The 0.0-0.2 density range is chosen based on the exhibition TF, where opacity ramps steeply from 0.0 at density=0.0 to 0.30 at density=0.2. The culling replaces this smooth ramp with stochastic binary decisions.

### Wedge Parameters

| Parameter | Range | Default | Lock Criterion |
|-----------|-------|---------|----------------|
| crumble_low | 0.0 | 0.0 | Fixed (zero density = invisible) |
| crumble_high | 0.1 - 0.3 | 0.2 | Ash particles visible at expected boundary width |
| blue_noise_resolution | 64 - 256 | 128 | No visible tiling at exhibition resolution |
| temporal_jitter | 0.0 - 0.02 | 0.0 | 0 for stable ash, >0 for firefly sparkle |

### Tier Behavior

- **Exhibition:** Full stochastic ash culling with blue noise.
- **Study:** Smooth opacity ramp (no culling).
- **Sketch:** Binary threshold at density 0.05 (simple on/off).

---

## Technique 5: Three Chords of Dread

**Reference:** Sunn O))) -- three sustained notes create an entire world.

### Concept

The plume animation operates on three temporal frequencies simultaneously, each with its own noise character. These are not mixed randomly but layered like musical chords, each with distinct spatial and temporal properties.

### The Three Chords

#### Chord 1: Drone (HYSPLIT)

The base plume shape derived from HYSPLIT transport model data. Moves at atmospheric/geological timescales.

| Property | Value |
|----------|-------|
| Source | HYSPLIT trajectory data |
| Motion | Glacial drift, 0.001-0.01 units/frame |
| Noise character | Very low frequency, continent-scale structure |
| Visual role | Defines the mass, direction, and gravity of the plume |
| Temporal scale | Minutes to hours of real time per animation second |

#### Chord 2: Churn (Convective)

Convective rolls and turbulent mixing within the plume body. Fluid dynamics timescale.

| Property | Value |
|----------|-------|
| Source | Curl noise advection (existing `curl_noise_3d`) |
| Motion | Fluid, rolling, 0.05-0.2 units/frame |
| Noise character | Mid-frequency, scale of plume cross-section |
| Visual role | Internal structure, roiling and folding |
| Temporal scale | Seconds of real time per animation second |
| Octaves | 4-6 from existing `apply_turbulence` |

#### Chord 3: Spark (Emission)

The curvature-driven emission crackles (Technique 3). Fire-speed temporal variation.

| Property | Value |
|----------|-------|
| Source | Emission field + arrhythmic pulse |
| Motion | Fast flicker, 0.5-2.0 units/frame |
| Noise character | High frequency, localized to surfaces and vortex cores |
| Visual role | Life, danger, heat -- the only thing that moves "fast" |
| Temporal scale | Sub-second real time per animation frame |

### Layering

The three chords sum (not multiply) in their respective domains:

```
final_density = drone_density + churn_displacement(drone_density)
final_emission = spark_emission(final_density, velocity)
```

Drone provides mass. Churn deforms mass. Spark adds energy. The viewer perceives a single heavy, slow, glowing entity with three distinct temporal rhythms experienced simultaneously, like a sustained musical chord.

### Lock Criterion

Each chord is wedged independently. Lock when:

1. **Drone** feels heavy and directional (not random, not floating).
2. **Churn** creates visible internal folding without destroying the drone shape.
3. **Spark** crackles at surfaces, pulses arrhythmically, does not overwhelm the achromatic palette.
4. All three together read as "one thing with depth," not "three effects layered."

---

## Technique 6: The Soot Crust

**Reference:** Industrial slag, cooling lava, formation of crust on molten material.

### Concept

A dual-state shader that switches behavior based on density gradient magnitude. Where the gradient is steep (surface/boundary), the material becomes opaque matte black -- absorbing all light like a crust. Where the gradient is shallow (interior), the material is translucent with high scattering, revealing depth and internal luminosity.

### Implementation

**Crust field:**

```
crust = |grad(density)|
crust_norm = crust / percentile(crust, 95)  # normalize to [0, ~1]
```

**Dual-state shader:**

```
if crust_norm > crust_threshold:
    # CRUST STATE: matte black surface
    absorption = 1.0
    scattering = 0.0
    emission = 0.0
    albedo = 0.02  # near-black
else:
    # INTERIOR STATE: translucent grey with scattering
    absorption = 0.1
    scattering = 0.8
    emission = emission_field  # from Technique 3
    albedo = 0.85
```

**Blending:** In practice the transition is not binary but smoothly interpolated over a narrow band around `crust_threshold`:

```
crust_factor = smoothstep(crust_threshold - blend_width, crust_threshold + blend_width, crust_norm)
absorption = lerp(0.1, 1.0, crust_factor)
scattering = lerp(0.8, 0.0, crust_factor)
```

### MaterialX Starting Point

```xml
<standard_volume name="soot_crust">
  <!-- Interior state -->
  <input name="absorption" type="float" value="0.1" />
  <input name="scattering" type="color3" value="0.8, 0.8, 0.8" />
  <input name="scattering_anisotropy" type="float" value="0.8" />
  <input name="emission_color" type="color3" value="0.68, 0.68, 0.68" />

  <!-- Crust state overrides via VEX/MaterialX graph -->
  <!-- crust_factor drives lerp between interior and crust parameters -->
</standard_volume>
```

**Scattering anisotropy:** Exhibition tier uses `0.8` (strong forward scattering) compared to study tier's `0.35`. This creates the "ghost light" effect where light bleeds through the translucent interior but is blocked by the opaque crust, producing visible depth cues even in achromatic imagery.

### Wedge Parameters

| Parameter | Range | Default | Lock Criterion |
|-----------|-------|---------|----------------|
| crust_threshold | 0.2 - 0.6 | 0.4 | Visible crust at plume boundaries, not interior |
| blend_width | 0.02 - 0.15 | 0.05 | Smooth transition, no visible hard edge |
| crust_absorption | 0.8 - 1.0 | 1.0 | Surfaces read as matte black |
| interior_scattering | 0.5 - 0.95 | 0.8 | Visible depth, translucent grey interior |
| scattering_anisotropy | 0.6 - 0.9 | 0.8 | Forward scattering creates ghost light |

### Tier Behavior

- **Exhibition:** Full dual-state shader with scattering_anisotropy 0.8.
- **Study:** Single-state shader, scattering_anisotropy 0.35, no crust behavior.
- **Sketch:** No volumetric shading.

---

## Technique 7: Contact Sheet Bible

**Reference:** Photographer's contact sheet -- print everything, circle the winners, lock before animating.

### Concept

Before animating any shot, render a contact sheet of 100 variations of a single representative frame. The variations wedge the key lookdev parameters from Techniques 1-6. Print the best 5 on Hahnemuhle Photo Rag Baryta (glossy fiber, 315 gsm) at 13x19" and evaluate on paper under controlled lighting. Lock the lookdev on paper, then press play.

### Process

#### Step 1: TOPs Wedge Graph (Houdini)

Configure a PDG/TOPs wedge that varies the following parameters across 100 iterations:

| Parameter | Wedge Range | Steps |
|-----------|-------------|-------|
| grain_amplitude | 0.02 - 0.10 | 5 |
| viscosity_strength | 0.2 - 0.6 | 4 |
| emission_intensity | 0.8 - 2.5 | 5 |
| crust_threshold | 0.25 - 0.55 | (derived from remaining combinations) |
| scattering_anisotropy | 0.65 - 0.85 | (paired with crust_threshold) |

Total: 5 x 4 x 5 = 100 variations.

Each wedge renders a single frame at Final tier settings (1024^3, 512 spp + OIDN, 4K resolution). Total render time: ~100 x 22 min = ~37 GPU-hours on RTX 6000 Ada.

#### Step 2: Review and Select

1. Generate a contact sheet mosaic (10x10 grid) at screen resolution.
2. Eliminate obvious failures (blowout, banding, invisible grain, no crust).
3. Circle top 10 candidates.
4. Render top 10 at full resolution.
5. Select best 5 for print.

#### Step 3: Print and Lock

Print specifications:

| Property | Value |
|----------|-------|
| Paper | Hahnemuhle Photo Rag Baryta 315 gsm |
| Size | 13x19" (A3+) |
| Profile | ICC profile matched to printer/paper |
| Color space | sRGB (achromatic, so gamut is irrelevant) |
| Resolution | 300 DPI native |
| Black point | Absolute (no compensation -- the void must be true black) |

Evaluation:

- View under D50 illuminant at 50 cm viewing distance.
- Paper grain visible? (Technique 1)
- Sedimentary banding present but not overwhelming? (Technique 2)
- Emission visible at surfaces, arrhythmic, not uniform? (Technique 3)
- Ash particles visible at boundaries? (Technique 4)
- Crust reads as matte black, interior as translucent grey? (Technique 6)
- Overall: would this hold on a gallery wall at 4K projection?

#### Step 4: Lock and Animate

The winning parameter set becomes the locked lookdev for the shot. All subsequent frames of the shot use these exact parameters. No further lookdev iteration during animation rendering.

### Time Box

**3 calendar days maximum** from wedge submission to locked lookdev. If no satisfactory result after 3 days, escalate to creative director for scope reduction.

| Day | Activity |
|-----|----------|
| Day 1 | Submit wedge, generate contact sheet, initial triage |
| Day 2 | Full-resolution renders of top 10, print top 5 |
| Day 3 | Paper evaluation, parameter lock, sign-off |

---

## Existing Codebase References

### Noise Generation (`src/oco_viz/plume/noise.py`)

- `fbm_3d(shape, octaves, lacunarity, gain, seed)` -- multi-octave fractal Brownian motion, returns `[0, 1]` float32 array.
- `fbm_4d(shape, time_slices, ...)` -- temporally coherent 4D fBm via seed blending.
- `curl_noise_3d(shape, ...)` -- divergence-free displacement field via curl of three fBm potentials.

Techniques 1 (grain), 2 (sedimentary), and 5 (churn chord) build on `fbm_3d`. Technique 3 (emission) and 5 (churn) use `curl_noise_3d` for vorticity/displacement.

### Turbulence Application (`src/oco_viz/plume/turbulent.py`)

- `apply_turbulence(base_conc, turb_cfg, grid_cfg, time_index)` -- curl noise displacement + fBm density modulation + distance falloff. This is the study-tier turbulence pipeline.
- Exhibition tier extends this with Techniques 1-6 applied in sequence after the base turbulence pass.

### Tone Mapping (`src/oco_viz/postprocess/tonemap.py`)

- `aces_tonemap(rgb, exposure)` -- Narkowicz ACES filmic approximation. Exhibition tier uses this as the sole post-process (no bloom, no fog per visual language spec).
- The `exposure` parameter provides the mood control lever: values below 1.0 darken toward industrial dread, above 1.0 pushes toward the dirty near-white peak.

### Transfer Functions

| File | Color Stops | Opacity Stops | Peak Color | Max Opacity |
|------|-------------|---------------|------------|-------------|
| `soot.json` | 6 | 7 | rgb(1.0, 1.0, 1.0) | 0.85 |
| `soot_exhibition.json` | 14 | 23 | rgb(0.680, 0.680, 0.680) | 0.85 |

Exhibition TF key differences:
- Peak color 0.680 (not 1.0) -- "dirty near-white" enforced.
- Dense opacity sampling at low density (0.005, 0.01, 0.02, 0.04, 0.07 scalar values) -- critical for Technique 4 (ash culling) to have enough opacity resolution in the crumble zone.
- Steeper initial opacity ramp (0.15 at scalar 0.1 vs. study's 0.0 at 0.1) -- exhibition makes low-density features more visible.

---

## Summary: Lock Criteria Per Technique

| # | Technique | Lock Criterion |
|---|-----------|----------------|
| 1 | Paper Grain Manifold | Grain visible at density 0.1, invisible at density 0.8, no aliasing |
| 2 | Sedimentary Motion | Horizontal shelving visible, dense regions hold shape 3-5 sec |
| 3 | Curvature-Driven Emission | Surface glow without blowout, arrhythmic pulse perceptible |
| 4 | Stochastic Ash Culling | Discrete particles at boundary, no visible tiling |
| 5 | Three Chords of Dread | Drone/Churn/Spark read as single entity with temporal depth |
| 6 | The Soot Crust | Matte black surfaces, translucent grey interior, ghost light |
| 7 | Contact Sheet Bible | 5 prints pass gallery-wall test, locked within 3-day box |

---

**Document Type:** Lookdev Specification
**Depends On:** `plan/visual_language.yaml`, `plan/coding_guide_2026.md`
**Feeds Into:** `plan/render_farm_spec.md`, `plan/finishing_spec.md`, Waves 10-14 ticket YAMLs
