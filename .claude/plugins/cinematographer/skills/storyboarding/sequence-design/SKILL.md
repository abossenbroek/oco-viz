---
name: sequence-design
user-invocable: false
type: instruction
primary_owner: storyboarder
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Sequence Design — Emotional Arc and Temporal Structure

Think in sequences, not individual shots. A shot is a word; a sequence is a sentence.
The meaning emerges from the relationships between shots — juxtaposition, rhythm,
contrast, progression. Eisenstein understood this in 1925: meaning is created in the
cut, not in the frame. A plume shot following a void shot means something different from
the same plume shot following another plume shot. The storyboarder's job is to design
the sentence, not just the words.

Every sequence has an arc — tension builds, reaches a peak, and resolves. A sequence
without an arc is a slideshow. A sequence with no variation in intensity is a monotone.
The viewer's emotional engagement follows the arc: they lean in as tension builds, hold
their breath at the peak, and exhale as it resolves. Design this breathing.

> "Hold back detail that doesn't serve the story." — Deak Ferrand, Concept Artist, BR2049

---

## Principle

Think in sequences, not individual shots. Every sequence has an arc — tension, release,
revelation. The emotional architecture of a sequence determines its shot count, pacing,
scale progression, and edit rhythm. Individual shots serve the sequence's arc; the arc
does not serve the shots.

In Blade Runner 2049 every sequence was pre-visualized as a complete temporal unit.
Denis Villeneuve and Roger Deakins storyboarded entire scenes — not as individual frames
but as pacing diagrams showing how long each shot would hold, where the cuts would fall,
and how the emotional intensity would rise and fall.

---

## Procedure

### Step 1 — Define the Sequence Arc

Every sequence needs a defined emotional arc before any shots are designed. The arc
is a curve of emotional intensity over time:

```
Intensity
    |         *  *
    |       *      *
    |     *          *
    |   *              *
    | *                  *
    +--------------------------> Time
    Establish  Build  Peak  Resolve
```

Three standard arc types:

| Arc Type | Shape | Use Case | Example |
|----------|-------|----------|---------|
| **Rising** | Low → High | Revelation, discovery | Approaching plume from distance to immersion |
| **Mountain** | Low → High → Low | Complete dramatic beat | Plume emergence, peak density, dissipation |
| **Wave** | Medium → High → Medium → High → Low | Complex emotional journey | Multi-phase plume sequence with secondary climax |

### Step 2 — Beat Mapping

Divide the sequence into emotional beats. Each beat corresponds to one or more shots.

| Beat | Intensity Range | Purpose | Shot Scale Tendency |
|------|----------------|---------|-------------------|
| **Establish** | 0.1 - 0.3 | Ground the viewer in space and context | WS / EWS |
| **Build** | 0.3 - 0.6 | Increase engagement, introduce detail | WS → MS transition |
| **Tension** | 0.5 - 0.8 | Create anticipation, constrict space | MS → CU transition |
| **Peak** | 0.8 - 1.0 | Maximum emotional intensity | CU / ECU |
| **Release** | 0.3 - 0.1 | Decompress, allow reflection | CU → WS expansion |
| **Coda** | 0.1 - 0.2 | Final thought, lingering image | Static WS or EWS |

Map beats to the arc:

```yaml
sequence:
  id: SEQ-003
  title: "Soot Emergence"
  arc_type: mountain
  duration_total: 45s

  beats:
    - { type: establish, intensity: 0.2, duration: 8s, shots: 1 }
    - { type: build,     intensity: 0.4, duration: 7s, shots: 1 }
    - { type: tension,   intensity: 0.7, duration: 6s, shots: 2 }
    - { type: peak,      intensity: 1.0, duration: 5s, shots: 1 }
    - { type: release,   intensity: 0.4, duration: 8s, shots: 1 }
    - { type: coda,      intensity: 0.15, duration: 11s, shots: 1 }
```

### Step 3 — Apply Montage Principles

Sergei Eisenstein's five methods of montage, applied to volumetric sequences:

| Montage Type | Principle | Volumetric Application |
|-------------|-----------|----------------------|
| **Metric** | Cuts at fixed intervals | Rhythmic sequence of plume states at regular intervals — metronome pacing |
| **Rhythmic** | Cuts follow visual rhythm | Cut when the plume's internal motion completes a gesture — organic pacing |
| **Tonal** | Cuts follow emotional tone | Cut when the emotional quality of the shot changes — mood-driven pacing |
| **Overtonal** | Combination of metric, rhythmic, tonal | Complex pacing that operates on multiple levels simultaneously |
| **Intellectual** | Juxtaposition creates meaning | Cut from plume mass to void to industrial source — the sequence argues a point |

For Soot-tier sequences, **tonal montage** is the default: the emotional quality of the
density field — its weight, edge character, internal motion — determines when the cut
falls.

### Step 4 — Design Transitions

Transition types between shots within a sequence:

| Transition | Mechanic | Emotional Effect | Use With |
|-----------|----------|-----------------|----------|
| **Hard cut** | Instantaneous | Energy, contrast, confrontation | Peak beats, scale changes |
| **Dissolve** | Cross-fade (0.5-2s) | Connection, transformation, passage of time | Build and release beats |
| **Dip to black** | Fade out → hold → fade in | Separation, chapter break, breath | Between sequence sections |
| **Match cut** | Visual element continues across cut | Continuity in change, surprise | Structure echoes (plume shape matching landscape) |
| **L-cut** | Edit point differs for visual/audio | Anticipation, flow | Atmospheric audio preceding visual |
| **Whip** | Fast pan creating motion blur at cut | Urgency, disorientation | Tension beats only (use sparingly) |

### Step 5 — Validate the Sequence on Paper

Before any rendering, the sequence must work as a written document:

1. Read the beat descriptions in order. Does the intensity arc feel right?
2. Check that shot scales progress logically (no jump from EWS to ECU without
   intermediate steps, unless the jump IS the dramatic point).
3. Verify that each transition supports the emotional shift between beats.
4. Time the sequence by reading each beat description aloud. If it feels rushed or
   dragging on paper, it will feel worse on screen.

---

## Parameters

### Sequence Structure Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `arc_type` | enum | mountain | rising, mountain, wave, falling, flat | Emotional arc shape |
| `total_duration` | float | 45.0 | 15.0 - 180.0 | Total sequence duration in seconds |
| `beat_count` | int | 6 | 3 - 12 | Number of emotional beats |
| `shot_count` | int | 7 | 3 - 20 | Total shots in sequence |
| `intensity_min` | float | 0.1 | 0.0 - 0.3 | Minimum emotional intensity in arc |
| `intensity_max` | float | 1.0 | 0.7 - 1.0 | Maximum emotional intensity in arc |

### Pacing Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `montage_type` | enum | tonal | metric, rhythmic, tonal, overtonal, intellectual | Primary montage method |
| `avg_shot_duration` | float | 6.5 | 3.0 - 15.0 | Average shot duration in seconds |
| `min_shot_duration` | float | 2.0 | 1.0 - 5.0 | Minimum single shot duration |
| `max_shot_duration` | float | 15.0 | 8.0 - 30.0 | Maximum single shot duration |
| `pacing_acceleration` | float | 0.0 | -1.0 - 1.0 | Shot duration trend (-1 = accelerating, +1 = decelerating) |

### Transition Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `default_transition` | enum | hard_cut | hard_cut, dissolve, dip_to_black, match_cut | Default transition between shots |
| `dissolve_duration` | float | 1.0 | 0.3 - 3.0 | Cross-dissolve duration in seconds |
| `dip_black_hold` | float | 1.5 | 0.5 - 4.0 | Hold duration in black for dip transitions |
| `max_consecutive_hard_cuts` | int | 3 | 2 - 6 | Maximum hard cuts before a softer transition |

---

## Presets

### The Contemplative Arc

Slow, meditative sequence with long holds and dissolve transitions. The plume as
meditation object. Evokes the Zen garden sequences that Villeneuve envisioned for
BR2049's interstitial moments.

```yaml
arc_type: mountain
total_duration: 60.0
beat_count: 5
shot_count: 5
montage_type: tonal
avg_shot_duration: 12.0
min_shot_duration: 8.0
max_shot_duration: 15.0
pacing_acceleration: 0.0  # uniform pacing
default_transition: dissolve
dissolve_duration: 2.0
intensity_min: 0.15
intensity_max: 0.7  # moderate peak — contemplation, not confrontation
```

### The Confrontation Arc

Fast-paced sequence building to a peak with hard cuts and compressed shot durations.
The plume as threat. Evokes the Harkonnen attack sequences in Dune — overwhelming force
demanding attention.

```yaml
arc_type: rising
total_duration: 30.0
beat_count: 6
shot_count: 8
montage_type: rhythmic
avg_shot_duration: 3.75
min_shot_duration: 2.0
max_shot_duration: 6.0
pacing_acceleration: -0.5  # accelerating toward peak
default_transition: hard_cut
intensity_min: 0.3
intensity_max: 1.0
```

### The Revelation Arc

Two-phase sequence: long contemplative first half dissolves into a compressed second
half. The plume reveals its full nature. Evokes K's discovery of the wooden horse in
BR2049 — quiet patience rewarded with sudden understanding.

```yaml
arc_type: wave
total_duration: 50.0
beat_count: 7
shot_count: 8
montage_type: overtonal
avg_shot_duration: 6.25
min_shot_duration: 2.5
max_shot_duration: 12.0
pacing_acceleration: -0.3  # gentle acceleration
default_transition: dissolve  # first half
# transition_override at beat 4: switch to hard_cut for second half
intensity_min: 0.1
intensity_max: 1.0
```

---

## Anti-Patterns

### 1. The Slideshow

**Symptom:** A series of shots played in sequence but with no emotional arc. Each shot
has roughly the same intensity, the same scale, the same pacing. The viewer sees a
collection of images, not a narrative.

**Cause:** Designing shots individually rather than as a sequence. Each shot was
optimized on its own merit without considering its role in the temporal structure. The
storyboard is a gallery, not a film.

**Fix:** Map the emotional arc FIRST, then design shots to serve it. If three
consecutive shots have intensity within 0.1 of each other, at least one needs to change.
The arc must be visible in the beat map before any shot design begins.

**Villeneuve reference:** Denis Villeneuve famously edits "in-camera" — he shoots only
what will be in the film, in the order it will appear. Every shot exists because the
arc demands it.

### 2. The Monotone

**Symptom:** Same emotional intensity throughout the sequence. The viewer is engaged at
the beginning (because everything is new) but attention decays because the sequence
offers no variation. By the midpoint, the viewer is numb.

**Cause:** Fear of the low-intensity beat. The storyboarder believes every shot must be
impressive, so the sequence runs at 0.8 intensity throughout. The result is that nothing
feels intense because there is no contrast.

**Fix:** Embrace the valley. The intensity of the peak is defined by the depth of the
valley that precedes it. A sequence that drops to 0.2 intensity before climbing to 1.0
feels more powerful than one that maintains 0.8 throughout. Silence makes the next note
louder.

### 3. The Jump-Cut Cascade

**Symptom:** Rapid cuts between dramatically different shot scales (EWS → ECU → WS → CU)
without spatial continuity. The viewer cannot maintain a mental model of where they are
in relation to the subject.

**Cause:** Using scale changes as a substitute for emotional progression. Each cut
should shift the viewer's spatial relationship by one or two levels (WS → MS → CU),
not teleport them across the scale spectrum.

**Fix:** Scale changes of more than two levels require a narrative justification (it IS
the dramatic moment) or an intermediate bridging shot. Sequential cuts should progress
through adjacent scales unless the jump itself is the confrontation.

### 4. The Endless Dissolve

**Symptom:** Every transition is a slow dissolve. The sequence flows like warm syrup —
smooth, continuous, and utterly without punctuation. Hard cuts are avoided because they
feel "jarring."

**Cause:** Confusing smoothness with quality. Dissolves are beautiful transitions but
they reduce contrast between shots. A sequence of dissolves removes all editorial
punctuation — there are no sentences, only a continuous murmur.

**Fix:** Hard cuts are punctuation. They create emphasis, surprise, and energy. Use them
at beat transitions where the emotional quality changes. Reserve dissolves for
transitions within the same beat where continuity serves the mood.

### 5. The Clock Sequence

**Symptom:** All shots have identical duration — 5 seconds each, or 8 seconds each.
The sequence has a metronome regularity that reads as mechanical rather than organic.

**Cause:** Defaulting to uniform shot duration for simplicity. In metric montage
(Eisenstein's simplest form), uniform duration is intentional — but even Eisenstein
varied within metrics. Pure uniformity is a machine; variation is life.

**Fix:** Vary shot duration based on emotional content. Tension beats compress (shorter
shots). Release beats expand (longer shots). The peak shot may be the shortest or the
longest, depending on whether the arc serves confrontation (short, sharp) or immersion
(long, held).

---

## Validation Checklist

- [ ] Sequence arc defined before any individual shots designed
- [ ] Arc type selected (rising, mountain, wave) with justification
- [ ] Every beat has assigned intensity value (0.0 - 1.0)
- [ ] Intensity range spans at minimum 0.4 (difference between lowest and highest beat)
- [ ] No three consecutive beats within 0.1 intensity of each other
- [ ] Shot count appropriate for total duration (no shot < 2s or > 15s default)
- [ ] Scale progression between adjacent shots spans at most 2 levels (unless intentional)
- [ ] Montage type selected with justification
- [ ] Transition types vary — not all hard cuts, not all dissolves
- [ ] Hard cuts placed at beat transitions for punctuation
- [ ] Dissolves reserved for within-beat continuity
- [ ] Sequence validated on paper before any rendering
- [ ] Read-aloud pacing test passed (no beats feel rushed or dragging)
- [ ] Each shot serves the arc — no shots exist only for visual interest
