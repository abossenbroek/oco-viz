---
name: lambert-invisible-vfx
user-invocable: false
type: instruction
primary_owner: vfx-supe
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Lambert Invisible VFX --- If You Notice It, It Failed

Paul Lambert supervised visual effects on Blade Runner 2049 and Dune with a philosophy
that inverts the typical VFX artist's ambition: the goal is not to create spectacular
effects but to create invisible ones. The best visual effects are the ones nobody sees.
When a viewer watches a plume dissolve into atmosphere and thinks "that looks real," the
VFX succeeded. When they think "that looks amazing," it failed --- because they noticed
it. For volumetric CO2 visualization the same discipline applies: every enhancement,
every post-processing step, every parameter choice must serve physical plausibility.
The moment the render draws attention to its own technique, it has broken the illusion.

> "If you notice the VFX, it failed." --- Paul Lambert, VFX Supervisor, BR2049/Dune

---

## Principle

The best visual effects are the ones nobody sees. Every VFX decision starts with
physical reference photography, every enhancement must be consistent across the full
sequence, and every stylized choice must obey plausible physics. Subtraction is always
preferred over addition --- remove artifacts before adding enhancements. The final
composite must be indistinguishable from a single-capture image. If a non-expert viewer
can point to the VFX, the work is not finished.

Lambert's invisible-VFX philosophy is not minimalism --- it is integration discipline.
On BR2049 his team created massive digital environments (the Las Vegas ruins, the
Wallace Corporation water effects, the Joi hologram) that audiences accepted as
photographed reality because every synthetic element obeyed the optical physics of the
practical camera system. The CG rain fell with physically correct refraction. The
digital fog scattered light at physically correct angles. The holographic artifacts
matched the chromatic aberration of the Alexa 65's Hasselblad optics. Nothing was
perfect; everything was plausible.

For our volumetric pipeline this means: VTK renders must look as though a physical
camera captured a physical plume in a physical atmosphere. The density field, lighting,
post-processing, and composition must conspire to create an image that a viewer accepts
without question --- not because it is photorealistic, but because it is physically
coherent.

---

## Procedure

### Step 1 --- Reference Photography First

Before touching any render parameter, assemble physical reference photography for the
effect you are creating. Every VFX decision starts with a real-world counterpart:

| Effect | Reference Source | Key Properties to Match |
|--------|----------------|------------------------|
| Plume density | Industrial stack photography | Density gradient shape, edge character, internal structure |
| Atmospheric scatter | Sunrise/sunset fog photography | Light falloff through particulate, color shift with depth |
| Emission glow | Furnace/combustion photography | Temperature-color relationship, falloff rate, core-halo ratio |
| Plume boundary | Cloud edge photography | Fractal dimension, wisp formation, dissolution character |
| Ground interaction | Fog bank photography | Density pooling, surface-following behavior, clearance height |

Store references in the visual bible with measured properties where possible:
estimated albedo, observed scatter angles, density falloff profiles. The reference is
not inspirational --- it is a specification to match.

### Step 2 --- Continuity Check Across Sequence

Effects must be consistent across the sequence, not just within a single frame. Before
finalizing any parameter, verify it holds across the continuity window:

```
For each parameter P in render config:
  For each frame F in [current - continuity_window, current + continuity_window]:
    Render frame F with parameter P
    Compare against reference photography
    Compare against adjacent frames
    Flag: does P produce a visible discontinuity at any cut point?
```

A parameter that looks correct in frame 47 but produces a pop at frame 48 is wrong in
frame 47. The sequence is the unit of quality, not the frame.

### Step 3 --- Physical Grounding

Even stylized effects must obey plausible physics. For each enhancement, verify:

| Physical Law | Check | Failure Mode |
|-------------|-------|--------------|
| Conservation of energy | Light entering the volume cannot exceed light exiting + absorbed | Plume glows brighter than light sources |
| Inverse-square falloff | Light intensity decreases with distance squared | Uniform illumination across volume |
| Beer-Lambert absorption | Opacity increases exponentially with density path length | Linear opacity ramp |
| Mie/Rayleigh scattering | Forward scatter dominates for large particles, isotropic for small | Scattering behavior inconsistent with particle size |
| Thermal emission | Color temperature follows blackbody curve for hot gas | Arbitrary emission colors |

If a parameter violates plausible physics, it must be justified with an explicit
creative override documented in the continuity ledger --- and the override must be
subtle enough to remain invisible.

### Step 4 --- Subtraction Over Addition

Before adding any enhancement, remove existing artifacts. The subtraction pass is
always first:

```
SUBTRACTION PRIORITY (execute in order):
1. Remove noise floor --- background must be pure black (#000000)
2. Remove banding --- smooth density quantization artifacts
3. Remove aliasing --- anti-alias hard voxel edges
4. Remove temporal flicker --- stabilize frame-to-frame variance
5. Remove color casts --- neutralize unintended hue shifts

Only after ALL subtractions are complete:
6. Add enhancements (bloom, grain, atmospheric effects)
```

The logic: adding enhancements on top of artifacts amplifies the artifacts. A bloom
pass on a noisy background creates glowing noise. A grain pass on a banded gradient
creates grainy bands. Clean first, enhance second.

### Step 5 --- Integration Pass

The final integration pass evaluates whether the composite reads as a single-capture
image. This is the invisible-VFX litmus test:

```
INTEGRATION CHECKLIST:
- [ ] Can you identify the boundary between plume and background?
      If yes: boundary dissolution needs work
- [ ] Does the plume edge have a different noise character than the interior?
      If yes: noise coherence needs work
- [ ] Does the lighting on the plume match the lighting on the environment?
      If yes: the question is wrong (there should be no visible "matching")
- [ ] Does the bloom respond to plume density or sit as a flat overlay?
      If flat overlay: bloom must be density-aware
- [ ] Does the grain structure vary with luminance?
      If uniform: grain must be exposure-dependent (see fraser-shift)
```

The integration pass is binary: the image either reads as a unified capture or it does
not. There is no partial integration.

---

## Parameters

### Reference Matching Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `reference_tolerance` | float | 0.15 | 0.05 - 0.30 | Maximum deviation from physical reference (normalized) |
| `reference_match_channels` | list | [density, edge, scatter] | --- | Which properties to match against reference |
| `reference_priority` | enum | physical | physical, artistic | Whether to prioritize physical match or artistic intent |

### Continuity Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `continuity_window` | int | 5 | 3 - 15 | Number of adjacent frames to check for continuity |
| `max_parameter_drift` | float | 0.02 | 0.005 - 0.05 | Maximum allowed parameter change between adjacent frames |
| `cut_point_tolerance` | float | 0.05 | 0.02 - 0.10 | Maximum visible discontinuity at cut points (normalized) |

### Subtraction Priority Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `subtraction_priority` | list | [noise, banding, aliasing, flicker, color_cast] | --- | Order of artifact removal |
| `noise_floor_threshold` | float | 0.001 | 0.0 - 0.005 | Maximum background noise level (normalized) |
| `banding_max_steps` | int | 0 | 0 - 3 | Maximum visible quantization steps in smooth gradients |
| `flicker_max_variance` | float | 0.005 | 0.001 - 0.01 | Maximum frame-to-frame luminance variance in static regions |

### Integration Assessment Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `integration_pass_required` | bool | true | --- | Whether the integration pass is mandatory before approval |
| `boundary_visibility_max` | float | 0.0 | 0.0 | Visible boundary between plume and background (must be zero) |
| `noise_coherence_required` | bool | true | --- | Noise character must be consistent across the image |
| `bloom_density_aware` | bool | true | --- | Bloom must respond to density, not sit as overlay |

---

## Presets

### Exhibition Invisible

Maximum invisibility standard. Every artifact eliminated, every enhancement physically
grounded, integration pass must survive scrutiny at 4K projection scale. This is the
"projected on a gallery wall" standard.

```yaml
reference_tolerance: 0.08
continuity_window: 10
max_parameter_drift: 0.005
cut_point_tolerance: 0.02
noise_floor_threshold: 0.0005
banding_max_steps: 0
flicker_max_variance: 0.002
integration_pass_required: true
boundary_visibility_max: 0.0
```

### Study Invisible

Relaxed tolerance for pre-visualization. Artifacts should still be invisible at
normal viewing distance but may be detectable at pixel-peep scale.

```yaml
reference_tolerance: 0.20
continuity_window: 5
max_parameter_drift: 0.02
cut_point_tolerance: 0.05
noise_floor_threshold: 0.002
banding_max_steps: 2
flicker_max_variance: 0.008
integration_pass_required: true
boundary_visibility_max: 0.0
```

### Scout Quick Check

Fast validation for creative direction approval. Only the most egregious visibility
failures are flagged. Integration pass runs but is advisory, not blocking.

```yaml
reference_tolerance: 0.30
continuity_window: 3
max_parameter_drift: 0.05
cut_point_tolerance: 0.10
noise_floor_threshold: 0.005
banding_max_steps: 3
flicker_max_variance: 0.01
integration_pass_required: false
```

---

## Anti-Patterns

### 1. Visible CG

**Symptom:** The plume has unnaturally clean edges, perfect bilateral symmetry, or
uniform noise characteristics. It reads as "computed" rather than "captured." A
technical artist immediately identifies it as CG; a general viewer feels something is
off without being able to articulate why.

**Cause:** Insufficient physical reference. The render was designed to look correct
according to the mathematical model rather than according to how physical plumes
actually appear. Physical plumes have fractal edges, asymmetric internal structure,
and noise that varies with density and viewing angle.

**Fix:** Return to Step 1. Compare the render against physical reference photography
side by side. Identify every property where the render is cleaner, more regular, or
more uniform than the reference. Add physical imperfection until the two are
indistinguishable at viewing distance: irregular edge breakup, asymmetric density
distribution, view-dependent noise character.

**Lambert reference:** On BR2049 the digital Las Vegas ruins were deliberately
degraded --- CG dust was added to CG surfaces, CG weathering patterns varied
stochastically, CG lighting had physical lens artifacts --- until set photographers
could not distinguish digital and practical elements in dailies.

### 2. Overworked Effects

**Symptom:** Too much detail in some areas and too little in others. The plume core has
exquisite density variation while the edge dissolves into nothing. Or conversely, the
edge has beautiful wispy tendrils while the core is a featureless blob. The eye is
drawn to the detailed area, breaking the illusion of a unified physical phenomenon.

**Cause:** Artist focus on the "interesting" part of the effect while neglecting the
mundane parts. Physical plumes have consistent detail density relative to their mass
density --- more detail where there is more stuff, less where there is less, but never
zero-to-maximum jumps.

**Fix:** Evaluate detail distribution relative to density distribution. Map the spatial
frequency content of the render and overlay it against the density field. Where the
ratio of detail-to-density deviates by more than 2x from the median, the effect is
overworked (or underworked). Equalize the ratio.

### 3. Continuity Breaks

**Symptom:** A parameter drifts between shots in a sequence. The grain amplitude in
shot 3 is 0.05, in shot 4 it is 0.08, and by shot 7 it has crept to 0.12. Each frame
looks acceptable in isolation, but played in sequence the drift creates a subliminal
unease --- the viewer senses something changing but cannot identify what.

**Cause:** Parameters tuned per-shot without checking the continuity ledger. Each shot
was worked on independently, and small "improvements" accumulated into visible drift.

**Fix:** Lock all parameters in the continuity ledger before finaling begins. During
finaling, verify actual values against locked values with zero tolerance for creative
parameters. Parameter drift is the silent killer of invisible VFX --- by the time you
notice it in the sequence, it has been accumulating for dozens of frames.

### 4. The Showcase Render

**Symptom:** The render is designed to demonstrate the pipeline's capabilities rather
than to serve the story. Effects are turned up to show off: bloom is brighter than
needed, scatter is more dramatic than physics suggests, the transfer function is more
colorful than the material warrants.

**Cause:** Optimizing for the demo reel instead of the final output. The artist wants
the render to be impressive rather than invisible. This is the fundamental tension of
invisible VFX: the better you do your job, the less credit you receive.

**Fix:** Apply the Lambert test: show the render to a non-expert. If they say "wow,
cool effects," dial everything back by 30%. If they say "is that a photograph?" you
are in the right territory. The compliment you want is "I did not realize that was CG."

---

## Validation Checklist

- [ ] Physical reference photography assembled before any render configuration
- [ ] Every reference has measurable properties extracted (not just visual impression)
- [ ] Continuity window checked: parameters consistent across adjacent frames
- [ ] No parameter drift exceeds `max_parameter_drift` between adjacent frames
- [ ] Cut points checked: no visible discontinuity exceeds `cut_point_tolerance`
- [ ] Physical grounding verified: all enhancements obey plausible physics
- [ ] Subtraction pass completed before any enhancement pass
- [ ] Background is pure black (#000000) with no noise floor
- [ ] No visible banding in smooth density gradients
- [ ] No temporal flicker in static regions
- [ ] Integration pass completed: image reads as unified single-capture
- [ ] Boundary between plume and background is invisible (no hard edge)
- [ ] Noise character is consistent across the entire image
- [ ] Bloom is density-aware (not a flat overlay)
- [ ] Non-expert viewer cannot identify where the VFX are
- [ ] No bilateral symmetry in plume structure
- [ ] Detail distribution is proportional to density distribution
