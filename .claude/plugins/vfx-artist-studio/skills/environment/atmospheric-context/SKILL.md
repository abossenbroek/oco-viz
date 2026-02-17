---
name: atmospheric-context
user-invocable: false
type: instruction
primary_owner: matte-artist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Atmospheric Context -- Scale Through Absence

Scale Through Absence -- emptiness communicates scale more effectively than detail. No
Environmental Context in Exhibition -- no horizon, no ground plane, no sky. The void is
absolute. The plume communicates its massive industrial scale (57 Mt/year CO2) not
through environmental reference but through its own internal structure and temporal
behavior. Adding a horizon "for scale" is the visual equivalent of explaining a joke.

> "Architecture is the thoughtful making of space." -- Louis Kahn

---

## Principle

The central paradox of the oco-viz exhibition: the plume must communicate massive
industrial scale without any environmental reference. A single OCO-3 target emits
approximately 57 megatons of CO2 per year -- a quantity so vast that it exceeds human
intuition. No environmental reference can make this quantity comprehensible. A horizon
line would shrink the plume to a thing-in-a-landscape; a ground plane would reduce it
to a column-above-a-surface; a sky would domesticate it as weather.

Instead, scale is communicated through three internal mechanisms:

**Internal detail gradient** -- The plume's internal structure spans multiple scales:
dense opaque core (meters), translucent halo (tens of meters), wispy boundary
(hundreds of meters). The viewer's eye traverses these scales and infers that the
object is large enough to contain them all. This is the same mechanism by which a
photograph of a mountain communicates scale without including a human figure -- the
internal texture gradient (rock face, snow field, atmospheric haze) implies scale.

**Temporal behavior** -- The plume moves at two timescales: glacial bulk mass transport
(slow, heavy, inevitable) and fast emission crackle at the source point (turbulent,
energetic, violent). The contrast between these timescales communicates mass. A small
object that moves slowly looks slow. A large object that moves slowly looks massive.
The temporal signature communicates what the spatial signature alone cannot.

**Viewer projection** -- In the absence of environmental reference, the viewer projects
their own sense of scale onto the void. The plume could be a wisp of smoke or an
atmospheric colossus. The void's infinity allows the viewer to choose the scale that
is most emotionally resonant. This ambiguity is a feature, not a limitation.

---

## Context Levels

### Exhibition Context (context_level: none)

No environmental context whatsoever. This is the default and required level for all
exhibition deliverables.

| Element | Status | Rationale |
|---------|--------|-----------|
| Horizon | **Never** | Domesticates the plume into landscape |
| Ground plane | **Never** | Reduces plume to column-above-surface |
| Sky | **Never** | Adds atmospheric context that competes with void |
| Stars | **Never** | Implies night sky, specific time, specific location |
| Grid | **Never** | Implies measurement, scientific diagram, not art |
| Scale bar | **Never** | Explicitly destroys scale ambiguity |
| Light source | **Never** | Motivated light exists but the source is never visible |
| Other objects | **Never** | Any reference object domesticates the void |

### Study Context (context_level: minimal)

Minimal environmental context for spatial orientation during lookdev and technical
review. The study tier exists for artists and technical directors to evaluate the
plume's behavior in a spatial context before stripping that context for exhibition.

| Element | Status | Conditions |
|---------|--------|------------|
| Ground plane | Allowed | Neutral grey, no texture, no shadow receiving |
| Grid (faint) | Allowed | 10% opacity, world-space aligned, for spatial reference |
| Axis indicator | Allowed | RGB axis gizmo in corner for orientation |
| Horizon | **Not allowed** | Still too much environmental context for study |
| Sky | **Not allowed** | Study needs spatial, not atmospheric, context |

### Editorial Context (context_level: reference)

Environmental context appropriate for non-exhibition contexts such as scientific
communication, editorial review, or documentation. The plume is presented with enough
context for the viewer to understand its physical setting.

| Element | Status | Conditions |
|---------|--------|------------|
| Ground plane | Allowed | May include terrain reference |
| Horizon | Allowed | May include atmospheric gradient |
| Source location | Allowed | May include schematic of emission source |
| Scale reference | Allowed | May include distance/altitude markers |
| Satellite path | Allowed | May include OCO-3 orbital reference |

---

## Procedure

### Step 1 -- Determine Context Level

Every shot must have an explicitly declared context level. The context level is
determined by the deliverable type:

| Deliverable | Context Level | Override Possible |
|-------------|--------------|-------------------|
| Exhibition projection | none | No |
| Exhibition print | none | No |
| Study / lookdev | minimal | No |
| Editorial / documentation | reference | Yes (can be reduced to minimal) |
| Archive master | none | No (preserves exhibition intent) |

### Step 2 -- Verify No Environmental Context (Exhibition)

For exhibition context (context_level: none), verify that no environmental element
has been introduced at any stage of the pipeline:

```
Check list:
  - Renderer background: must be (0,0,0), no environment map
  - Light rig: no visible light source geometry
  - Post-processing: no fog extending beyond plume boundary
  - Comp: no background plate, no matte painting
  - Camera: no ground-level framing that implies horizon
```

### Step 3 -- Add Minimal Context (Study)

For study context (context_level: minimal), add only the elements needed for spatial
orientation:

```yaml
study_context:
  ground_plane:
    visible: true
    color: [0.15, 0.15, 0.15]  # neutral grey
    opacity: 0.3
    shadow_receiving: false
    texture: none
  grid:
    visible: true
    spacing_m: 1.0
    opacity: 0.1
    color: [0.3, 0.3, 0.3]
  axis:
    visible: true
    position: corner
    size: 50px
```

### Step 4 -- Add Reference Context (Editorial)

For editorial context (context_level: reference), add environmental elements that
serve communication:

```yaml
editorial_context:
  ground_plane:
    visible: true
    type: terrain_schematic
  horizon:
    visible: true
    type: atmospheric_gradient
  source_marker:
    visible: true
    type: emission_point_indicator
  scale_reference:
    visible: true
    type: altitude_markers
```

### Step 5 -- Validate Scale Communication (Exhibition)

For exhibition work, verify that scale is communicated through internal mechanisms
rather than environmental context:

| Mechanism | Check | Expected |
|-----------|-------|----------|
| Internal detail gradient | Visible transition from dense core to wispy halo | Yes -- at least 3 distinct density zones visible |
| Temporal behavior | Slow bulk transport vs. fast emission crackle | Yes -- 2+ timescales visible in animation |
| Boundary dissolution | Wispy edges dissolving into void | Yes -- boundary reads as atmospheric, not clipped |
| Void quality | Black surroundings create depth perception | Yes -- void reads as infinite, not flat |

---

## Parameters

### Context Parameters

| Parameter | Type | Default | Allowed Values | Description |
|-----------|------|---------|----------------|-------------|
| `context_level` | string | none | none / minimal / reference | Environmental context level |
| `horizon_visible` | bool | false | -- | Always false for exhibition |
| `ground_plane` | bool | false | -- | Always false for exhibition |
| `sky_visible` | bool | false | -- | Always false for exhibition |

### Study Context Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `study_ground_color` | [float, float, float] | [0.15, 0.15, 0.15] | -- | Neutral grey ground plane color |
| `study_ground_opacity` | float | 0.3 | 0.1 - 0.5 | Ground plane opacity |
| `study_grid_spacing` | float | 1.0 | 0.5 - 5.0 | Grid spacing in meters |
| `study_grid_opacity` | float | 0.1 | 0.05 - 0.2 | Grid line opacity |

### Scale Communication Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `density_zones_min` | int | 3 | Minimum distinct density zones for scale gradient |
| `timescale_contrast` | bool | true | Verify multi-timescale temporal behavior |
| `boundary_atmospheric` | bool | true | Verify boundary reads as atmospheric |

---

## The Scale Paradox

57 megatons per year. That is the CO2 output of a single large industrial target
observed by OCO-3. To visualize this quantity requires confronting a paradox: any
visual reference that attempts to communicate this scale will necessarily fail because
the quantity exceeds environmental intuition.

**A skyscraper next to the plume?** The plume is orders of magnitude larger. The
skyscraper becomes a speck. The viewer sees a speck next to a blob, not a mountain
of CO2 next to a building.

**A map of the region?** The plume covers hundreds of square kilometers. The map
becomes abstract geography. The viewer sees a colored overlay on a map, not a
choking mass of carbon.

**Numbers?** 57,000,000 tons. The viewer reads the number, understands it
intellectually, and feels nothing. Numbers do not produce the visceral response that
exhibition art requires.

The void is the solution. By presenting the plume in infinite black space with no
reference, the viewer is freed from intellectual scale estimation and left with
only the perceptual and emotional response to the form itself. The plume is as large
as the void allows it to be, which is to say, as large as the viewer's imagination
makes it.

---

## Anti-Patterns

### 1. Adding Horizon "For Scale"

**Symptom:** A horizon line is added at the bottom of the frame to "ground" the plume
and "give the viewer a sense of scale." The plume now reads as a cloud in a landscape
rather than an isolated sculptural form.

**Cause:** Anxiety that the viewer will not understand the plume without spatial
reference. This is a failure of confidence in the visual language.

**Fix:** Remove the horizon. Trust the internal detail gradient and temporal behavior
to communicate scale. If the plume reads as "too small" without a horizon, the problem
is the density field or the camera framing, not the absence of environmental context.

### 2. Ground Plane "For Grounding"

**Symptom:** A ground plane is added to "give the plume something to sit on." The plume
now terminates at a visible surface rather than dissolving into the void. The
exhibition language of isolation and the sublime is replaced with terrestrial familiarity.

**Cause:** Compositional discomfort with floating forms. In most visual storytelling,
objects exist in environments. The exhibition language deliberately rejects this
convention.

**Fix:** Remove the ground plane. The plume does not "sit on" anything. It exists in
the void. If the base of the plume looks wrong without a ground plane, adjust the
boundary dissolution at the base to create a more intentional termination -- crumbling
ash, wispy thinning, or emission-point glow.

### 3. Sky "For Context"

**Symptom:** A sky gradient or HDRI is added as an environment map. The plume is now
lit by environmental light (which may be physically motivated) but the void is
compromised. The background is no longer pure black.

**Cause:** Lighting motivation conflict. The DP wants motivated lighting (which implies
an environment) but the exhibition language demands no visible environment. This
conflict must be resolved in favor of the exhibition language: light is motivated by
implied sources, but those sources are never visible.

**Fix:** Remove the environment map. Light the plume with explicit light sources that
are motivated but not visible. The light comes from an implied furnace, an implied
atmosphere, an implied sun -- but none of these are rendered. The background remains
(0,0,0).

### 4. Any Environmental Element in Exhibition Tier

**Symptom:** Stars, terrain features, atmospheric haze beyond the plume boundary,
satellite paths, measurement annotations, or any other environmental element appears
in an exhibition-tier deliverable.

**Cause:** Environmental context was added during the study or editorial phase and not
removed before exhibition delivery. Or, a conscious decision was made to add context
for "clarity" -- which is always wrong for exhibition work.

**Fix:** Exhibition tier has context_level: none. No exceptions. If environmental
context is needed for communication, create a separate editorial or study deliverable
with the appropriate context level. The exhibition deliverable must be pure: plume and
void, nothing else.

---

## Validation Checklist

- [ ] Context level explicitly declared per shot (none / minimal / reference)
- [ ] Exhibition deliverables: context_level is none -- no exceptions
- [ ] No horizon visible in any exhibition frame
- [ ] No ground plane visible in any exhibition frame
- [ ] No sky, stars, or environment map in any exhibition frame
- [ ] No grid, scale bar, or measurement annotation in exhibition frames
- [ ] No visible light source geometry in exhibition frames
- [ ] Background is exactly (0,0,0) in exhibition frames
- [ ] Scale communicated through internal detail gradient (3+ density zones)
- [ ] Scale communicated through temporal behavior (2+ timescales)
- [ ] Boundary dissolution reads as atmospheric, not clipped
- [ ] Study context uses only neutral grey elements at low opacity
- [ ] Editorial context includes only elements that serve communication
- [ ] Context level recorded in shot_context.yaml
- [ ] Void quality consistent with void-design skill specification
