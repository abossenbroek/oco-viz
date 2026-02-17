---
name: derived-formats
user-invocable: false
type: instruction
primary_owner: matte-artist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Derived Formats -- Recomposition, Not Crop

Derived Formats Are Not Crops. A gallery print, a projection, and an installation each
require recomposition for the specific medium. Cropping a 4K frame to 13x19" print is
not a derived format -- it is a failure of composition. Each derived format demands that
the relationship between plume, void, and frame edge be reconsidered for the specific
viewing context: distance, ambient lighting, display technology, and perceptual scale.

> "The frame is not a window. It is a decision." -- Henri Cartier-Bresson

---

## Principle

A derived format is a recomposition of the image for a specific medium and viewing
context. The same plume data may appear in five different contexts -- dark-room
projection, gallery wall print, multi-screen installation, editorial review monitor,
and archival storage. Each context imposes different constraints on how the image should
be composed:

**Viewing distance** changes the perceptual resolution of detail. A projection viewed
from 3 meters compresses fine boundary detail into texture. A print viewed from 50 cm
reveals individual grain structure. The composition must account for what will be
visible at the intended viewing distance.

**Ambient lighting** changes the perceived dynamic range. A projection in a dark room
has infinite contrast ratio (limited only by the projector's black level). A print on
a gallery wall under D50 illumination has a dynamic range limited by the paper's Dmax.
The void quality and boundary contrast must be adjusted for the ambient conditions.

**Display technology** changes the color gamut, black level, and luminance range. A
P3-D65 projector reproduces different blacks than a sRGB monitor, which reproduces
different blacks than ink on paper. The void-to-plume transition must be verified on
each target display.

**Perceptual scale** changes the emotional impact. A 4K projection fills the visual
field -- the plume is enormous, overwhelming. A 13x19" print is intimate -- the plume
is held in the hands, contemplated closely. The composition must serve the intended
emotional relationship between viewer and image.

---

## Procedure

### Step 1 -- Identify Target Formats

List all derived formats required for the exhibition. From the exhibition-delivery-spec:

| Format Type | Resolution | Display | Viewing Distance | Ambient |
|-------------|-----------|---------|-----------------|---------|
| Projection | 4K DCI (4096x2160) | P3-D65 projector | 3-5 meters | Dark room |
| Print A3+ | 3900x5700 at 300 DPI | Paper (13x19") | 50 cm | D50 gallery |
| Print A1 | 7200x10800 at 300 DPI | Paper (24x36") | 100 cm | D50 gallery |
| Editorial | 2K (2048x1080) | sRGB monitor | 60 cm | Office lighting |
| Installation | Variable (multi-screen) | Multiple displays | Variable | Variable |

### Step 2 -- Evaluate Composition Per Format

For each derived format, evaluate whether the master composition serves the viewing
context:

| Question | If No | Action |
|----------|-------|--------|
| Is the plume correctly sized for the viewing distance? | Too small at 3m, lost detail at 50cm | Adjust framing (zoom, reposition) |
| Is the void balance appropriate? | Too much void for intimate print | Adjust void-to-plume ratio |
| Does the boundary quality survive the format? | Fine wisps lost at 2K | Increase boundary width or adjust falloff |
| Is the density range appropriate for the display? | Paper Dmax insufficient | Adjust density mapping for print |
| Does the void read correctly under the ambient? | Gallery lighting lifts blacks | Adjust black point for print |

### Step 3 -- Recompose for Each Format

**Projection (4K, dark room, 3-5m):**
- Full-width composition with generous void framing
- Void is absolute (0,0,0) -- dark room maximizes perceived contrast
- Boundary detail at full resolution -- viewer distance compresses fine detail
- Plume centered or offset per shot choreography

**Print A3+ (13x19", gallery wall, 50cm):**
- Tighter framing than projection -- the intimate format rewards closer plume-to-frame
  relationship
- Void balance adjusted: less void than projection (print is contemplative, not
  overwhelming)
- Boundary detail increased -- close viewing reveals grain, ash, and dissolution texture
- Black point absolute -- Hahnemuhle Photo Rag Baryta Dmax is the target
- ICC profile matched to printer/paper combination

**Print A1 (24x36", gallery wall, 100cm):**
- Moderate framing between projection and A3+
- Void generous but not overwhelming
- Boundary detail visible but not dominant at 1-meter viewing
- Same paper and black point as A3+, different composition

**Editorial (2K, monitor, 60cm):**
- Functional composition -- plume visible, structure readable
- Display transform applied (Rec.709 or ACES SDR)
- May include more void for context (editorial is not exhibition)
- Boundary detail may be simplified at 2K

**Installation (multi-screen, variable):**
- Composition spans multiple displays -- requires careful edge alignment
- Void continuous across screens -- no visible seam in the black
- Each screen receives a different crop of a wider composition
- Synchronization and color calibration across all displays

### Step 4 -- Generate Recomposed Frames

For each derived format, generate the recomposed output. This is NOT a resize-and-crop
operation. Recomposition may involve:

- Rendering at a different resolution or aspect ratio
- Adjusting the virtual camera framing
- Modifying the void balance (negative space around the plume)
- Adjusting density range for the display technology
- Applying display-specific color management

### Step 5 -- Validate Per Format

Each derived format must be validated in its intended viewing context:

| Format | Validation Method |
|--------|------------------|
| Projection | Review on calibrated P3-D65 projector in dark room |
| Print A3+ | Proof print on Hahnemuhle, review under D50 at 50 cm |
| Print A1 | Proof print at full size, review under D50 at 1 m |
| Editorial | Review on calibrated sRGB monitor at 60 cm |
| Installation | On-site review with synchronized multi-screen setup |

---

## Parameters

### Per-Format Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format_type` | string | projection | projection / print / installation / editorial |
| `viewing_distance` | float | 3.0 | Intended viewing distance in meters |
| `ambient_lighting` | string | dark | dark / controlled / office |
| `display_technology` | string | P3-D65 | P3-D65 / sRGB / paper / multi-screen |

### Composition Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `void_balance` | float | 0.6 | 0.3 - 0.8 | Fraction of frame occupied by void |
| `plume_scale` | float | 1.0 | 0.5 - 2.0 | Relative plume size within frame |
| `plume_offset` | [float, float] | [0.0, 0.0] | -- | Plume position offset from center |
| `recomposition_notes` | string | -- | -- | Human-readable recomposition rationale |

### Print-Specific Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `print_size` | string | A3+ | A3+ / A1 / custom |
| `dpi` | int | 300 | Print resolution |
| `paper` | string | Hahnemuhle Photo Rag Baryta 315 gsm | Paper stock |
| `black_point` | string | absolute | absolute / relative |
| `icc_profile` | string | matched | ICC profile for printer/paper |

---

## Anti-Patterns

### 1. Crop-and-Deliver

**Symptom:** The 4K projection frame is resized to fit the print dimensions. The
composition that worked for dark-room projection at 3 meters is used unchanged for a
gallery print at 50 cm. Fine boundary detail is lost at 2K editorial. The void balance
is wrong for the intimate print format.

**Cause:** Treating derived formats as resolution variants of a single composition
instead of independent compositions for different viewing contexts.

**Fix:** Recompose for each format. Evaluate the plume-void-frame relationship for each
viewing context. Adjust framing, void balance, and density range as needed. A derived
format is a new composition, not a rescale.

### 2. Same Composition for All Formats

**Symptom:** The projection, print, and editorial formats all show the same framing --
same void balance, same plume position, same boundary character. The print looks like
a screenshot of the projection. The editorial proxy looks like a compressed print.

**Cause:** Using a single composition and generating all formats from it without
considering that each format imposes different perceptual constraints.

**Fix:** Each format gets its own composition pass. The projection may use generous void
for the overwhelming scale of dark-room viewing. The print may use tighter framing for
the intimate scale of close viewing. The editorial may use functional framing for
readability. The compositions share the same source data but differ in framing and
treatment.

### 3. Ignoring Viewing Distance

**Symptom:** Fine boundary detail that is visible on the artist's monitor is invisible
in the projection (too far from screen). Or, boundary artifacts that were invisible
at projection distance are distractingly visible in the gallery print (too close).

**Cause:** Not accounting for the angular resolution of the intended viewing context.
At 3 meters from a 4K projection, a single pixel subtends approximately 0.3 arcminutes.
At 50 cm from a 300 DPI print, a single dot subtends approximately 1.2 arcminutes --
four times the angular resolution.

**Fix:** Evaluate boundary detail, grain visibility, and artifact visibility at the
intended viewing distance. If detail is too fine for projection, increase its scale.
If artifacts are too coarse for print, refine them. The viewing distance is a design
parameter, not an afterthought.

### 4. Ignoring Ambient Lighting

**Symptom:** Gallery prints look washed out under gallery lighting. The void reads as
dark grey instead of black. The perceived dynamic range of the print is insufficient
for the density range of the plume.

**Cause:** Designing and proofing the print under different ambient conditions than the
exhibition venue. The gallery's D50 illumination lifts the apparent black level of the
paper, reducing the perceived contrast between plume and void.

**Fix:** Proof prints under the intended viewing conditions (D50 illumination at the
expected viewing distance). Use absolute black point rendering to achieve the paper's
maximum density (Dmax). Accept that print blacks are not as deep as projection blacks --
the composition must account for this by ensuring the void-to-plume transition is robust
enough to survive the reduced contrast.

---

## Adjacent Practice Note

**Jacolby Satterwhite** — 3D-to-physical fabrication. Satterwhite translates digital
renders into physical sculptural objects (resin casts, CNC-milled forms, AR overlays
on gallery pieces), treating the derived physical artifact as a first-class recomposition
rather than a reproduction. This practice is a precedent for thinking about derived
formats as creative acts with their own material logic, not mechanical conversions.

---

## Validation Checklist

- [ ] All required derived formats identified from exhibition-delivery-spec.yaml
- [ ] Each format has its own composition (not a crop of the master)
- [ ] Viewing distance accounted for in composition decisions
- [ ] Ambient lighting accounted for in void quality and density range
- [ ] Display technology validated for each format
- [ ] Print proofed on correct paper (Hahnemuhle Photo Rag Baryta 315 gsm) under D50
- [ ] Print uses absolute black point (not relative)
- [ ] Projection reviewed on calibrated P3-D65 display in dark room
- [ ] Editorial proxy reviewed on calibrated sRGB monitor
- [ ] Void balance appropriate for each format's viewing context
- [ ] Boundary detail visible and artifact-free at intended viewing distance
- [ ] Recomposition notes documented per format explaining framing decisions
- [ ] Color management correct per format (ACEScg for projection/archive, Rec.709 for editorial, sRGB+ICC for print)
- [ ] Each derived format conforms to exhibition-delivery-spec.yaml
