---
name: shot-grammar
user-invocable: false
type: instruction
primary_owner: storyboarder
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Shot Grammar — The Language of Camera and Composition

Every shot has a purpose — emotional, narrative, compositional. The camera is not a
spectator; it is a participant in the storytelling. A dolly-in conveys approach and
intimacy. A static wide frame conveys observation and detachment. A low angle conveys
power and menace. These are not stylistic choices — they are grammatical constructions
in the visual language. Use them with the same precision you would use words in a
sentence.

Deak Ferrand, concept artist on BR2049, described his philosophy: "Remove the software
from yourself. What's the story? What's the feeling?" The same applies to shot design
for volumetric sequences — the technology (VTK, keyframes, easing curves) is invisible
to the viewer. They see only the emotional content of the shot.

> "What's the story? What's the feeling?" — Deak Ferrand, Concept Artist, BR2049

---

## Principle

Design confrontations, not pretty frames. Every shot is a confrontation between the
viewer and the subject. The camera's position, movement, scale, and duration determine
the nature of that confrontation — whether it is intimate or distant, aggressive or
contemplative, empowering or diminishing. A shot with no confrontation is a shot with
no purpose.

For volumetric plume sequences, the "subject" is not a human face — it is a mass of
particulate matter with density, edge, scale, and temporal behavior. The camera must
find the drama in this subject: the tension between core density and void, the fragility
of the halo edge, the oppressive mass of a plume at full scale.

---

## Procedure

### Step 1 — Define Shot Intent

Before specifying any technical parameter, answer three questions:

1. **What should the viewer feel?** (oppression, awe, curiosity, unease, revelation)
2. **What is the narrative beat?** (establish, approach, confront, reveal, release)
3. **What is the visual confrontation?** (scale vs. detail, mass vs. void, stasis vs. motion)

Document these in the shot specification:

```yaml
shot:
  id: SH-015
  feel: "oppression — the plume as an unavoidable presence"
  beat: confront
  confrontation: "mass vs. viewer — the plume fills the frame, no escape"
```

### Step 2 — Select Camera Move

Camera movement vocabulary with emotional associations for volumetric subjects:

| Move | Mechanic | Emotional Association | Volumetric Application |
|------|----------|----------------------|----------------------|
| **Static** | No movement | Observation, contemplation, dread | Let the plume's internal motion be the only movement |
| **Dolly in** | Camera advances toward subject | Approach, intimacy, discovery | Moving into the plume — from overview to immersion |
| **Dolly out** | Camera retreats from subject | Retreat, revelation, scale | Pulling back to reveal the plume's full extent |
| **Crane up** | Camera rises vertically | Transcendence, overview, power shift | Rising above the plume to reveal its structure from above |
| **Crane down** | Camera descends vertically | Descent, oppression, grounding | Descending into the plume base — approaching the source |
| **Orbit** | Camera circles subject | Examination, fascination, unveiling | Circling the plume to reveal three-dimensional structure |
| **Truck** | Camera moves laterally | Context, journey, lateral reveal | Traversing the plume's extent — revealing scale |
| **Push** | Slow dolly in with zoom hold | Intensification, focus, psychological pressure | Slow approach to plume core — building tension |
| **Handheld** | Controlled shake | Immediacy, documentary, urgency | Conveys human witness — this is a real event |
| **Steady** | Smooth mechanical glide | Precision, control, omniscience | Conveys scientific observation — measured and authoritative |

### Step 3 — Select Shot Scale

Shot scale vocabulary with narrative meaning for volumetric subjects:

| Scale | Abbreviation | Frame Content | Narrative Meaning |
|-------|-------------|---------------|-------------------|
| **Extreme Close-Up** | ECU | Density texture fills frame | Material intimacy — the substance of the plume |
| **Close-Up** | CU | Plume edge or core detail | Detail study — wisp behavior, scatter patterns |
| **Medium Shot** | MS | Plume section with context | Structural analysis — how the plume is built |
| **Wide Shot** | WS | Full plume with environment | Scale and context — the plume in its world |
| **Extreme Wide Shot** | EWS | Plume as element in landscape | Perspective and proportion — human scale vs. plume scale |

### Step 4 — Determine Duration

Duration per emotional beat. These are guidelines, not rules — extend for contemplation,
compress for urgency.

| Beat | Minimum Duration | Typical Duration | Maximum Duration | Notes |
|------|-----------------|------------------|------------------|-------|
| Establish | 4s | 6-8s | 12s | Hold long enough for spatial comprehension |
| Approach | 3s | 5-7s | 10s | Movement creates its own timing |
| Confront | 2s | 4-6s | 8s | Intensity limits duration — too long becomes numb |
| Reveal | 3s | 5-8s | 12s | Needs time for the new information to register |
| Release | 4s | 6-10s | 15s | Hold for emotional decompression |

### Step 5 — Compose the Frame

Composition rules for volumetric subjects:

| Rule | Specification | Rationale |
|------|---------------|-----------|
| **Rule of thirds** | Place density mass at third-line intersections | Natural visual weight distribution |
| **Leading lines** | Use gradient direction as implicit leading lines | Guides viewer's eye through the volume |
| **Negative space** | Void is compositional — use it intentionally | Gives the plume room to breathe and establishes scale |
| **Depth layering** | Separate foreground, mid, and background density | Creates dimensionality in a single frame |
| **Asymmetry** | Offset the plume from center | Tension and visual interest — centered = static |
| **Headroom** | If plume rises, give it room to rise into | Conveys direction and potential energy |

---

## Parameters

### Camera Move Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `move_type` | enum | static | static, dolly_in, dolly_out, crane_up, crane_down, orbit, truck, push, handheld, steady | Camera movement type |
| `move_speed` | float | 1.0 | 0.1 - 5.0 | Movement speed multiplier (1.0 = natural pace) |
| `move_easing` | enum | ease_in_out | linear, ease_in, ease_out, ease_in_out, ease_expo | Easing function for movement |
| `handheld_intensity` | float | 0.3 | 0.1 - 1.0 | Handheld shake amplitude (only for handheld move) |

### Shot Scale Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `shot_scale` | enum | WS | ECU, CU, MS, WS, EWS | Shot scale |
| `focal_length_mm` | float | 50.0 | 14.0 - 200.0 | Lens focal length |
| `depth_of_field` | float | 1.0 | 0.1 - 1.0 | DOF intensity (1.0 = maximum, 0.0 = disabled) |
| `aperture` | float | 5.6 | 1.4 - 22.0 | Aperture f-stop (affects DOF and exposure) |

### Duration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `duration_seconds` | float | 6.0 | 2.0 - 15.0 | Shot duration in seconds |
| `framerate` | float | 24.0 | 12.0 - 60.0 | Render framerate |
| `hold_start` | float | 0.5 | 0.0 - 3.0 | Static hold at start before movement begins (seconds) |
| `hold_end` | float | 0.5 | 0.0 - 3.0 | Static hold at end after movement completes (seconds) |

### Composition Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `subject_position` | vec2 | [0.38, 0.40] | [0.2-0.8, 0.2-0.8] | Subject placement in frame (x, y normalized) |
| `horizon_line` | float | 0.67 | 0.3 - 0.85 | Horizon vertical position (fraction from top) |
| `negative_space_ratio` | float | 0.40 | 0.2 - 0.6 | Fraction of frame that is void/negative space |
| `tilt_angle` | float | 0.0 | -15.0 - 15.0 | Camera tilt in degrees (Dutch angle) |

---

## Presets

### The Contemplation

Static wide shot with long duration. The plume exists in the frame, and the viewer has
time to find their own eye path through it. Evokes the vast desert landscapes of Dune
where the camera simply observes.

```yaml
move_type: static
shot_scale: WS
focal_length_mm: 35
duration_seconds: 10.0
hold_start: 0.0
hold_end: 0.0
subject_position: [0.38, 0.45]
negative_space_ratio: 0.45
```

### The Approach

Slow dolly-in from wide to medium, with exponential easing. The viewer is drawn toward
the plume — curiosity becomes confrontation. Evokes the approach to the Wallace
Corporation pyramid in BR2049.

```yaml
move_type: dolly_in
move_speed: 0.5
move_easing: ease_expo
shot_scale: WS  # starts wide, ends medium
focal_length_mm: 50
duration_seconds: 8.0
hold_start: 1.0
hold_end: 1.5
```

### The Immersion

Close-up orbit around plume detail with shallow depth of field. The viewer is inside
the plume's world, examining its material character. Evokes the sandworm-eye-view
sequences in Dune.

```yaml
move_type: orbit
move_speed: 0.3
move_easing: ease_in_out
shot_scale: CU
focal_length_mm: 85
depth_of_field: 0.8
duration_seconds: 6.0
hold_start: 0.5
hold_end: 0.5
subject_position: [0.45, 0.40]
negative_space_ratio: 0.25
```

---

## Anti-Patterns

### 1. The Arbitrary Move

**Symptom:** The camera moves — orbits, dollies, cranes — but the movement does not
serve the narrative beat. It moves because static shots feel "boring," not because the
movement communicates something specific.

**Cause:** Defaulting to motion as visual interest. In VFX demo reels the camera always
moves because the goal is to showcase the asset, not tell a story. In narrative work the
camera moves only when the movement itself communicates.

**Fix:** For every camera move, answer: "What does this movement make the viewer feel
that a static camera would not?" If the answer is "it looks more dynamic," the movement
is arbitrary. Remove it. A static shot of a plume with internal motion is more powerful
than an orbiting camera around a lifeless volume.

**Ferrand reference:** Deak Ferrand's concept art for BR2049 was mostly static
compositions. The drama was in the content, not the camera.

### 2. The Safe Frame

**Symptom:** Subject centered in frame with equal space on all sides. Symmetrical
composition. The image is balanced, comfortable, and completely devoid of tension.

**Cause:** Defaulting to centered composition as "correct" framing. In technical
visualization, centering is standard. In narrative work, centering removes the spatial
tension that makes an image engaging.

**Fix:** Offset the subject. Place the plume mass at a rule-of-thirds intersection.
Let negative space dominate one side of the frame. Create asymmetry. The viewer's eye
should have to work — that work is engagement.

### 3. The Turntable

**Symptom:** A 360-degree orbit around the plume, showcasing it from all angles like
a product on a rotating platform. This is a technical demonstration, not a shot.

**Cause:** Inheriting CG asset review conventions into narrative work. Turntables are
useful for evaluating models and volumes — they are never appropriate as delivered shots.

**Fix:** If an orbit is needed, make it partial (90-120 degrees maximum). Give it an
emotional reason: the viewer is circling the plume the way they would circle a sculpture
in a gallery — discovering form, not inventorying geometry. Start the orbit at the
least interesting angle and end at the most revealing.

### 4. The Zoom Substitution

**Symptom:** Using zoom (focal length change) as a substitute for dolly movement. The
perspective does not change — only the field of view does. The result feels flat and
disconnected because the spatial relationship between viewer and subject does not
actually change.

**Cause:** Confusing "getting closer" with "changing focal length." A dolly-in changes
parallax and spatial relationship. A zoom-in only crops the existing view. They feel
completely different to the viewer.

**Fix:** Use camera position changes (dolly, crane, truck) rather than focal length
changes for emotional movement. Focal length changes are valid for very specific effects
(the Hitchcock "Vertigo" dolly-zoom, for example) but should never substitute for
physical camera motion.

### 5. The Marathon Shot

**Symptom:** Shots that run 20+ seconds without an edit point, attempting to communicate
everything in a single continuous take. The viewer's attention wanders because the shot
overstays its emotional welcome.

**Cause:** Fear of editing. The temptation to show "the whole thing" in one shot rather
than constructing a sequence of purposeful cuts.

**Fix:** Long takes must earn their duration by continuously offering new visual
information — a camera move that reveals new structure, a lighting change that shifts
mood, a density event that alters the plume's character. A 15-second hold on a static
frame is only justified if the subject's internal motion provides sufficient visual
change to sustain attention.

---

## Validation Checklist

- [ ] Shot intent documented: feel, beat, confrontation
- [ ] Camera move has explicit emotional justification (not "looks dynamic")
- [ ] Shot scale matches narrative meaning (ECU for intimacy, EWS for scale)
- [ ] Duration matches emotional beat (see duration table)
- [ ] Composition uses asymmetry (subject not centered)
- [ ] Negative space used intentionally (not accidentally)
- [ ] Hold at start and end provides breathing room for cuts
- [ ] Easing function selected (no linear movement unless intentional)
- [ ] No turntable orbits (partial orbits with purpose only)
- [ ] No zoom substitution for dolly movement
- [ ] Every frame in the shot serves the confrontation — no dead time
- [ ] Shot would make sense to a viewer with no technical context
