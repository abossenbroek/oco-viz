---
name: review-in-the-cut
user-invocable: false
type: methodology
primary_owner: dp
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Review in the Cut — Sequence-Context Dailies

John Nelson's cardinal rule for VFX review on Blade Runner 2049: never evaluate a shot
in isolation. A frame that looks perfect on its own may feel wrong in the cut —
lighting continuity breaks, temporal pacing stutters, emotional arc collapses. The
reverse is equally true: a frame that looks slightly off may be exactly right when the
sequence breathes around it. This methodology ensures every rendered frame is evaluated
in its sequence context, never as a standalone hero image.

> "Review in the Cut." — John Nelson, VFX Supervisor, BR2049

---

## Principle

Never evaluate a shot in isolation. Always review in sequence context. A rendered frame
is not a photograph — it is a beat in a temporal sequence, and its quality can only be
judged relative to the frames that precede and follow it. The eye forgives individual
imperfections that serve the temporal flow. The eye punishes individual perfection that
breaks the temporal flow.

On BR2049 every VFX shot was reviewed in the editorial timeline, never as a standalone
turntable or beauty render. Denis Villeneuve insisted that the emotional rhythm of the
cut was the only valid context for judging technical quality. If a shot looked stunning
but disrupted the sequence's breathing, it failed.

---

## Procedure

### Step 1 — Assemble Full Sequence

Before reviewing any individual frame, assemble the complete rendered sequence in
temporal order. Minimum review length: 3 consecutive shots. Preferred: the full
sequence from opening beat to closing beat.

```
sequence/
  shot_001.exr   # opening beat — establish spatial context
  shot_002.exr   # development — deepen engagement
  shot_003.exr   # turning point — shift energy
  shot_004.exr   # climax — peak intensity
  shot_005.exr   # resolution — release and settle
```

### Step 2 — Review Temporal Continuity

Play the sequence at intended frame rate. Do NOT pause on individual frames. Evaluate:

| Continuity Axis | Check | Failure Indicator |
|-----------------|-------|-------------------|
| Lighting direction | Key direction consistent across cuts | Shadow jumps between frames |
| Color temperature | Grade progression smooth | Sudden warmth/cool shift at cut |
| Density character | Volume structure reads as same plume | Shape or texture pops between frames |
| Exposure level | Consistent brightness baseline | Flash or dip at transitions |
| Atmospheric depth | Haze/fog consistent | Depth compression changes abruptly |

### Step 3 — Check Lighting Consistency

For each cut point (transition between shots), verify:

1. **Key light direction** — Does the key maintain consistent motivation across the cut?
   A 10-degree shift in key azimuth across a cut is usually acceptable. Beyond 15
   degrees the eye registers a discontinuity.

2. **Shadow density** — Do shadows maintain the same depth? If shot A has 0.92 shadow
   density and shot B has 0.80, the cut will feel like a light was turned on.

3. **Color temperature drift** — Is the grade shifting intentionally (motivated by
   narrative arc) or accidentally (inconsistent config)?

### Step 4 — Evaluate Emotional Pacing

With the sequence assembled, assess the emotional arc. Each shot should contribute a
distinct beat:

```
Shot 1: ESTABLISH  — wide, atmospheric, the plume in its environment
Shot 2: APPROACH   — closer, details emerge, tension builds
Shot 3: CONFRONT   — intimate, the plume fills the frame, peak intensity
Shot 4: REVEAL     — new angle, context shift, understanding deepens
Shot 5: RELEASE    — pull back, breathe, let the image settle
```

If two consecutive shots have the same emotional intensity and scale, one of them is
redundant. If the sequence lacks an arc (same intensity throughout), the pacing is flat.

### Step 5 — Document Review Notes in Edit Context

All review notes must reference the sequence position, not just the frame:

```
REVIEW: shot_003 — in cut between 002 and 004, the key direction shifts 20 degrees
        causing a visible lighting pop. Suggest matching 002's key azimuth.
        Viewed at: 24fps playback, full sequence context.
        Emotional beat: CONFRONT — intensity peak feels right but the lighting
        discontinuity undercuts it.
```

---

## Parameters

### Sequence Review Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `min_sequence_length` | int | 3 | 3 - 20 | Minimum shots for valid sequence review |
| `review_framerate` | float | 24.0 | 12.0 - 60.0 | Playback framerate for sequence review |
| `max_key_azimuth_shift` | float | 15.0 | 5.0 - 30.0 | Max key light azimuth change across cut (degrees) |
| `max_key_elevation_shift` | float | 10.0 | 3.0 - 20.0 | Max key light elevation change across cut (degrees) |
| `max_shadow_density_delta` | float | 0.05 | 0.02 - 0.10 | Max shadow density change across cut |
| `max_color_temp_delta` | int | 300 | 100 - 500 | Max unmotivated color temperature shift (Kelvin) |
| `max_exposure_delta_ev` | float | 0.3 | 0.1 - 0.5 | Max exposure difference across cut (EV stops) |

### Emotional Pacing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `beat_types` | list | [establish, approach, confront, reveal, release] | Valid emotional beat labels |
| `max_consecutive_same_beat` | int | 1 | Maximum consecutive shots with identical beat type |
| `arc_required` | bool | true | Sequence must have intensity variation |
| `min_intensity_range` | float | 0.4 | Minimum difference between lowest and highest beat intensity (0-1 scale) |

---

## Presets

### Exhibition Sequence Review

Maximum strictness for gallery/exhibition sequences where every temporal discontinuity
will be visible on a large projection surface with attentive viewers.

```yaml
min_sequence_length: 5
review_framerate: 24.0
max_key_azimuth_shift: 8.0
max_key_elevation_shift: 5.0
max_shadow_density_delta: 0.03
max_color_temp_delta: 150
max_exposure_delta_ev: 0.15
arc_required: true
min_intensity_range: 0.5
```

### Study Sequence Review

Relaxed parameters for study-quality pre-visualization where temporal coherence matters
but pixel-level consistency is not required.

```yaml
min_sequence_length: 3
review_framerate: 24.0
max_key_azimuth_shift: 20.0
max_key_elevation_shift: 12.0
max_shadow_density_delta: 0.08
max_color_temp_delta: 400
max_exposure_delta_ev: 0.4
arc_required: true
min_intensity_range: 0.3
```

### Quick Check

Fast review for iterative development. Catches only severe discontinuities.

```yaml
min_sequence_length: 3
review_framerate: 24.0
max_key_azimuth_shift: 30.0
max_shadow_density_delta: 0.10
max_color_temp_delta: 500
max_exposure_delta_ev: 0.5
arc_required: false
```

---

## Anti-Patterns

### 1. The Hero Frame

**Symptom:** An enormous amount of time spent perfecting a single frame — adjusting
lighting, tweaking the transfer function, dialing in the exact post-processing — while
the rest of the sequence is ignored or treated as secondary.

**Cause:** The natural human tendency to focus on a single beautiful image. Social media
culture rewards single frames, not sequences. The artist optimizes for the screenshot,
not the experience.

**Fix:** Ban single-frame review entirely until the full sequence has been assembled and
played at speed. The hero frame may turn out to be the weakest shot in context because
it was over-optimized at the expense of sequence coherence.

**Nelson reference:** On BR2049, individual VFX shot reviews were forbidden until the
editorial department confirmed the cut. Shots were always reviewed in their editorial
position, never as standalone beauty passes.

### 2. The Technical Review

**Symptom:** Review notes focus entirely on technical metrics — noise levels, resolution,
render time, memory usage — without mentioning emotional impact, pacing, or narrative
contribution.

**Cause:** Engineers reviewing art. The metrics are correct but irrelevant. A shot can
have perfect PSNR and zero emotional contribution.

**Fix:** Structure review notes to always begin with emotional assessment: "This shot
feels [tense/calm/oppressive/revelatory]." Technical notes come second and only matter
if they affect the emotional read. A noisy frame that feels right trumps a clean frame
that feels wrong.

### 3. The Isolated Fix

**Symptom:** A shot is flagged in review, pulled from the sequence, fixed in isolation,
and re-inserted without re-reviewing the full sequence. The fix may introduce a new
discontinuity with its neighbors.

**Cause:** Efficiency-driven workflow that treats shots as independent units. Fix the
flagged frame, move on. But a lighting change in shot 3 may now mismatch shots 2 and 4.

**Fix:** After any change to any shot, re-review the full sequence. Minimum: the
changed shot plus its immediate neighbors (shot before, shot after). Preferred: the
complete sequence from beginning to end.

### 4. The Freeze-Frame Judge

**Symptom:** Pausing the sequence on individual frames during review and evaluating them
as still images. Scrubbing back and forth frame-by-frame to check technical quality.

**Cause:** Misunderstanding the medium. These are temporal sequences, not photography.
Frame-by-frame evaluation catches artifacts the eye will never see at playback speed
while missing temporal artifacts (pops, stutters, pacing breaks) that the eye absolutely
will see.

**Fix:** First pass is always at playback speed, no pausing. Second pass may scrub but
only to locate issues identified during playback. Never evaluate a frame that was not
first seen in motion.

---

## Validation Checklist

- [ ] Full sequence assembled before any individual frame review
- [ ] Sequence contains minimum 3 shots (5+ for exhibition tier)
- [ ] First review pass done at playback speed without pausing
- [ ] Lighting direction continuity checked at every cut point
- [ ] Key azimuth shift across cuts within threshold (15 degrees default)
- [ ] Shadow density variation across cuts within threshold (0.05 default)
- [ ] Color temperature drift across cuts within threshold (300K default)
- [ ] Exposure variation across cuts within threshold (0.3 EV default)
- [ ] Emotional beat assigned to each shot
- [ ] No two consecutive shots share the same emotional beat
- [ ] Sequence has identifiable intensity arc (not flat)
- [ ] All review notes reference sequence position, not just frame number
- [ ] Fixed shots re-reviewed in sequence context (minimum: shot + neighbors)
- [ ] No shot was approved based solely on single-frame evaluation
