---
name: void-design
user-invocable: false
type: instruction
primary_owner: matte-artist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Void Design -- The Void Is Not Nothing

The void is active negative space with intentional quality. Pure black (#000000) is not
the absence of design -- it is a deliberate material choice that communicates infinite
depth, isolation, and the sublime. The void is not a background. It is a co-protagonist
with the plume, defining the image through absence as much as the density field defines
it through presence.

> "Black is not the absence of light. It is the presence of everything."
> -- Ad Reinhardt

---

## Principle

The void is designed, not defaulted. Every exhibition frame in the oco-viz pipeline
presents a CO2 plume floating in black space. That black space is not a technical
default -- it is a curated material quality with art-historical precedent and perceptual
intent.

Three artists define the void vocabulary:

**Anish Kapoor** used Vantablack (99.965% light absorption) to create sculptures that
appear as holes in reality. The void is not a surface -- it is the absence of surface,
a perceptual impossibility that forces the viewer to confront the limits of vision. For
oco-viz, the void must achieve this same quality: the boundary between plume and void
should feel like the edge of perception, not the edge of a rendering.

**James Turrell** creates light installations where the void defines the aperture. The
viewer perceives depth, form, and volume not from the illuminated surface but from the
shape of the darkness surrounding it. For oco-viz, the void communicates depth: the
plume appears to recede into infinite space because the void offers no depth cues.

**Ad Reinhardt** painted "black paintings" that appear uniformly black until extended
viewing reveals subtle tonal variation. The void has quality even when it appears
absolute. For oco-viz, the void quality (absolute vs. atmospheric vs. textured) is a
deliberate artistic choice per shot.

---

## Procedure

### Step 1 -- Define Void Quality Per Shot

Select the void quality that serves the shot's emotional intent:

| Void Quality | Description | Max Luminance | Use Case |
|-------------|-------------|---------------|----------|
| Absolute | True black, zero variation, infinite depth | 0.0 | Exhibition projection, maximum isolation |
| Atmospheric | Imperceptible gradient suggesting vast depth | 0.005 | Shots requiring spatial hint without context |
| Textured | Micro-noise suggesting material substrate | 0.003 | Shots referencing physical print medium |

**Absolute** is the default for all exhibition work. It produces the maximum perceptual
contrast between the illuminated plume and the void, and it is the only quality that
can be achieved identically across all display technologies.

**Atmospheric** introduces a gradient so subtle that it is below conscious perception but
above absolute zero. The viewer senses depth without seeing it. Use only when the shot
requires a spatial hint that the plume exists within a vast space rather than against a
flat backdrop.

**Textured** mimics the tooth of a physical medium -- the paper grain or canvas weave
visible in the darkest shadows of a print. This quality references the print-making
tradition and is appropriate only when the shot explicitly references the physical
medium. See the paper-grain-manifold skill for the density-space implementation.

### Step 2 -- Specify Boundary Dissolution Behavior

The boundary between plume and void is where the image's character lives. The void
design must specify how the plume dissolves into the void:

| Boundary Style | Void Response | Visual Effect |
|---------------|---------------|---------------|
| Hard clip | Void begins immediately at density = 0 | Industrial, mechanical, artificial |
| Exponential falloff | Void gradual over 5-10 voxels | Atmospheric, organic, natural |
| Stochastic dissolution | Void scattered with ash particles | Ashen, decaying, entropic |
| Grain manifold | Void eroded by paper texture | Material, crafted, printerly |

The void design defines the INTENTION; the boundary-dissolution skill defines the
IMPLEMENTATION; and the effects-td implements the CODE. The matte-artist specifies
what the boundary should feel like, not how to compute it.

### Step 3 -- Validate Against Achromatic Manifesto

For exhibition work, the void must comply with the achromatic manifesto:

- No environmental context: no horizon, no ground plane, no sky, no stars
- No spatial reference: no grid, no axis, no scale bar
- No atmospheric haze extending from the void into the frame
- The void is absolute in all directions -- there is no "up" or "down" in the void

### Step 4 -- Verify Void Luminance

Measure the void luminance in rendered output:

| Void Quality | Max Luminance | Measurement Method |
|-------------|---------------|-------------------|
| Absolute | Exactly 0.0 | All void pixels must be (0,0,0) |
| Atmospheric | <= 0.005 | Sample void regions > 50 pixels from plume boundary |
| Textured | <= 0.003 | Sample void interior (> 100 pixels from boundary) |

For absolute void, any non-zero luminance in the void is a rendering defect -- light
leak, ambient contribution, or renderer bias. Run the pure black test from
karma-render-profiles.yaml before proceeding.

---

## Parameters

### Void Quality Parameters

| Parameter | Type | Default | Allowed Values | Description |
|-----------|------|---------|----------------|-------------|
| `void_quality` | string | absolute | absolute / atmospheric / textured | Void design intent |
| `void_max_luminance` | float | 0.0 | 0.0 - 0.005 | Maximum luminance in void region |
| `void_color` | [float, float, float] | [0.0, 0.0, 0.0] | -- | Void base color (always achromatic) |

### Depth Cue Parameters

| Parameter | Type | Default | Allowed Values | Description |
|-----------|------|---------|----------------|-------------|
| `void_depth_cue` | string | none | none / gradient / parallax | Depth perception mode |
| `void_gradient_direction` | string | none | none / vertical / radial | Gradient direction for atmospheric |
| `void_gradient_magnitude` | float | 0.0 | 0.0 - 0.005 | Gradient luminance range |

### Boundary Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `boundary_style` | string | exponential | Boundary dissolution style |
| `boundary_reference` | string | boundary-dissolution | Skill reference for implementation |

---

## Anti-Patterns

### 1. The Void as Afterthought

**Symptom:** The void is not discussed in the shot brief. It is whatever the renderer
produces by default -- pure black if the background color was set correctly, dark grey
if it was not, ambient-tinted if the light rig leaks.

**Cause:** Treating the void as "just the background" rather than a designed element.
The void quality was never specified because nobody thought it required specification.

**Fix:** The void quality must be specified in the shot brief alongside the plume design,
lighting rig, and camera path. The matte-artist owns the void design. If the void was
not designed, it was not done.

### 2. Adding Environmental Context

**Symptom:** A horizon line, ground plane, sky gradient, star field, or atmospheric haze
is added "for scale" or "for context." The plume no longer floats in the void -- it sits
in an environment.

**Cause:** Anxiety that the viewer will not understand the plume's scale or position
without environmental reference. This is a failure of creative confidence. The
exhibition language demands that the plume communicate scale through its own internal
structure, not through environmental crutches.

**Fix:** Remove all environmental context for exhibition work. The plume communicates
scale through internal detail gradient (dense core vs. wispy halo) and temporal behavior
(glacial mass vs. fast emission crackle). See atmospheric-context skill for the rare
cases where environmental context is appropriate (study tier, editorial formats).

### 3. Visible Gradient in Absolute Void

**Symptom:** The "absolute" void shows a faint gradient when viewed on a calibrated
display in a dark room. The bottom of the frame is imperceptibly lighter than the top,
or the void near the plume is slightly lifted.

**Cause:** Renderer ambient contribution, light rig leak, fog density set above zero,
or the display's own black floor lifting the signal. If the gradient is in the render
(not the display), it is a rendering defect.

**Fix:** Run the pure black test: render a frame with an empty scene (no VDB). All pixels
must be exactly (0,0,0). If any pixel is non-zero, fix the light rig, ambient settings,
or fog density before proceeding. If the gradient is only visible on the display, it is
a display limitation and does not affect the delivery file.

### 4. Void Luminance Exceeding Threshold

**Symptom:** Void regions measure above the specified max luminance (0.0 for absolute,
0.005 for atmospheric). The void reads as dark grey rather than black.

**Cause:** Ambient intensity above zero, scattered light from the plume reaching void
pixels, or grain restoration lifting void pixel values above zero.

**Fix:** Set ambient to exactly 0.0 for exhibition work. Ensure grain restoration does
not apply to void pixels (density = 0 regions must remain untouched). Verify that
volumetric scattering does not reach void pixels -- if the plume's scattering halo
extends into the void, the transfer function or scattering settings need adjustment.

---

## Adjacent Practice Note

**Sondra Perry** — fluid, dynamic void. In *IT'S IN THE GAME '17*, Perry replaces
the static black void with an immersive seascape — shifting, undulating water that
gives the void a living, fluid quality. This is an alternative void approach where
the void is not static absence but active, environmental force. For oco-viz, Perry's
work is a reference point for the "atmospheric" and "textured" void qualities — the
void as a material with its own behavior, not merely a backdrop with a luminance value.

---

## Validation Checklist

- [ ] Void quality explicitly specified per shot (absolute / atmospheric / textured)
- [ ] Void luminance within specified threshold for the chosen quality
- [ ] For absolute void: all void pixels exactly (0,0,0) -- no exceptions
- [ ] No environmental context in exhibition frames (no horizon, ground, sky, stars)
- [ ] Boundary dissolution style specified and consistent with boundary-dissolution skill
- [ ] Pure black test passed (empty scene renders as all-zero pixels)
- [ ] Ambient intensity is 0.0 for exhibition void
- [ ] Grain restoration does not lift void pixel values
- [ ] Void color is achromatic (equal RGB values, never tinted)
- [ ] Void quality serves the shot's emotional intent (documented in shot brief)
- [ ] Depth cue mode consistent with void quality (none for absolute)
- [ ] Output conforms to `void_design_delivery` schema from output-schemas
