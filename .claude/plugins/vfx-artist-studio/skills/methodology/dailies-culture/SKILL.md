---
name: dailies-culture
user-invocable: false
type: instruction
primary_owner: vfx-supe
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Dailies Culture --- Structured Shot Review in Sequence Context

In every major VFX studio --- ILM, Weta, DNEG, Framestore --- the dailies session is
the heartbeat of production. Not a status meeting, not a demo, not a critique circle.
Dailies is a disciplined review protocol where rendered frames are evaluated in their
sequence context, emotional reactions are recorded before technical analysis begins,
and every note is actionable. On Blade Runner 2049, John Nelson ran dailies with a rule
that became legendary in the VFX department: "Play it in the cut or do not play it at
all." A shot that looked stunning in isolation but disrupted the sequence rhythm was
rejected. A shot with visible artifacts that served the emotional arc was approved
with targeted fix notes. The sequence is the unit of quality.

> "Every frame tells you something about the shot, and every shot tells you something
> about the sequence." --- VFX dailies wisdom

---

## Principle

Review rendered frames in sequence context, not in isolation. Every frame tells you
something about the shot, and every shot tells you something about the sequence. The
emotional read at playback speed is the primary signal; technical analysis is secondary
and exists only to diagnose issues identified during the emotional pass. Notes without
frame numbers are opinions. Notes without actionable fixes are complaints. Notes
without severity levels are noise. The dailies protocol structures all three into a
review system that produces convergence toward the final image.

The three-pass review protocol separates emotional response from technical analysis
from comparative assessment. This separation is critical because technical analysis
contaminates emotional response --- once you know there is a noise artifact in the
upper-left corner, you cannot unsee it, and your emotional read of the frame is
permanently altered. The emotional pass must come first, uncontaminated by pixel-level
knowledge.

---

## Procedure

### Step 1 --- Context Assembly

Before reviewing any individual frame, assemble the full sequence or at minimum the
adjacent shots. Load them in temporal order with correct timing (frame rate, hold
frames, transitions). The minimum reviewable unit is 3 consecutive shots; the preferred
unit is the complete sequence from opening beat to closing beat.

```
ASSEMBLY CHECKLIST:
1. Load all shots in sequence order
2. Verify frame rate matches target (24fps for exhibition, 12fps for study)
3. Verify shot transitions are correctly timed
4. Load previous approved version (if any) for comparison
5. Load reference photography for comparative pass
6. Set display to target output format (resolution, color space)
```

If any shot in the sequence is missing or placeholder, note it but review anyway ---
gaps in the sequence are themselves review findings because they reveal where continuity
cannot yet be verified.

### Step 2 --- First Pass (Emotional)

Play the sequence at speed. Do not pause. Do not scrub. Do not zoom. Watch it as a
viewer would experience it. Record gut reactions with timestamps:

```
FIRST PASS NOTES FORMAT:
  [timestamp] [reaction]

Example:
  00:02.3  "Something feels heavy here --- oppressive, good"
  00:04.1  "Pop! Something changed between shots --- distracting"
  00:06.8  "Lost the plume --- where did it go?"
  00:09.2  "Beautiful dissolution --- the edge work is right"
  00:11.0  "Ending feels abrupt --- needs one more beat to settle"
```

Rules for the emotional pass:
- No pausing, scrubbing, or zooming
- No technical vocabulary (do not say "the grain is too coarse" --- say "it feels gritty")
- No referencing previous versions or reference photography
- Record reactions within 2 seconds of feeling them
- Play through the full sequence at least twice

The emotional pass produces the primary review signal. Everything that follows is
diagnostic --- figuring out WHY you felt what you felt.

### Step 3 --- Second Pass (Technical)

Now scrub frame by frame through the sequence. For each reaction noted in the emotional
pass, locate the specific frame(s) and diagnose the technical cause:

| Emotional Reaction | Frame(s) | Technical Diagnosis | Root Cause |
|-------------------|----------|--------------------| -----------|
| "Pop between shots" | 97-98 | Shadow density jumps 0.85 to 0.92 | Continuity ledger not applied to shot 4 |
| "Lost the plume" | 163-170 | Density drops below visibility threshold | Transfer function too aggressive in low-density range |
| "Feels gritty" | 35-50 | Grain amplitude 0.12 (target: 0.05) | Grain parameter not locked |

For each diagnosis, verify by toggling the suspected cause:
- If removing the suspected parameter change eliminates the emotional reaction, the
  diagnosis is confirmed
- If the reaction persists after the fix, the diagnosis is wrong --- dig deeper

### Step 4 --- Third Pass (Comparative)

Compare the current render against two references:

**A. Physical reference photography:**
Place the reference and the render side by side. Match-compare:
- Edge character (fractal dimension, dissolution rate)
- Density gradient profile (core-to-halo transition)
- Scatter behavior (angle-dependent brightness)
- Atmospheric depth (how the plume reads in space)

**B. Previous approved version (if any):**
A/B comparison at the same frame number. Identify:
- Intentional improvements (documented in change notes)
- Unintentional regressions (not documented --- these are bugs)
- Parameter drift (values that have crept from their locked positions)

### Step 5 --- Notes Format

Every review note must follow the structured format. Notes that lack any required field
are returned for completion before being entered into the review log:

```
NOTE FORMAT:
  Frame:    [frame number or range]
  Severity: [info | concern | fail]
  Pass:     [emotional | technical | comparative]
  Observation: [specific, factual description]
  Fix:      [actionable instruction for the artist]

Example:
  Frame:    97-98
  Severity: fail
  Pass:     emotional (confirmed in technical)
  Observation: Shadow density discontinuity at cut point between
               shots 3 and 4. Shadow jumps from 0.85 to 0.92,
               visible as a "lighting pop" at playback speed.
  Fix:      Match shot 4 shadow density to shot 3 value (0.85).
            Verify in continuity ledger. Re-review in sequence
            context after fix.
```

---

## Parameters

### Review Session Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `review_cadence` | enum | daily | daily, weekly, per_milestone | How often dailies are conducted |
| `min_sequence_length` | int | 3 | 3 - 20 | Minimum shots for valid sequence review |
| `review_framerate` | float | 24.0 | 12.0 - 60.0 | Playback framerate for sequence review |
| `emotional_pass_count` | int | 2 | 1 - 5 | Minimum times the emotional pass is played |
| `sequence_context_range` | int | 3 | 1 - 10 | Number of adjacent shots loaded as context |

### Note Severity Levels

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_severity_levels` | list | [info, concern, fail] | Available severity levels for review notes |
| `info_action` | enum | track | Action for info-level notes: track, defer, or ignore |
| `concern_action` | enum | schedule | Action for concern-level notes: schedule fix in current sprint |
| `fail_action` | enum | block | Action for fail-level notes: block approval until resolved |

### Continuity Thresholds

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_shadow_density_delta` | float | 0.05 | 0.02 - 0.10 | Maximum shadow density change at cut points |
| `max_color_temp_delta` | int | 300 | 100 - 500 | Maximum unmotivated color temperature shift (K) |
| `max_exposure_delta_ev` | float | 0.3 | 0.1 - 0.5 | Maximum exposure difference at cut points (EV) |
| `max_grain_amplitude_delta` | float | 0.02 | 0.005 - 0.05 | Maximum grain amplitude change at cut points |

---

## Presets

### Exhibition Dailies

Full three-pass protocol with maximum scrutiny. Every note requires actionable fix.
Fail-severity notes block shot approval. Used for final-tier exhibition renders.

```yaml
review_cadence: daily
min_sequence_length: 5
review_framerate: 24.0
emotional_pass_count: 3
sequence_context_range: 5
max_shadow_density_delta: 0.03
max_color_temp_delta: 150
max_exposure_delta_ev: 0.15
max_grain_amplitude_delta: 0.01
fail_action: block
```

### Working Dailies

Standard production dailies for active development. Two-pass protocol (emotional +
technical). Comparative pass runs weekly rather than daily. Concern-severity notes
are tracked but do not block.

```yaml
review_cadence: daily
min_sequence_length: 3
review_framerate: 24.0
emotional_pass_count: 2
sequence_context_range: 3
max_shadow_density_delta: 0.05
max_color_temp_delta: 300
max_exposure_delta_ev: 0.3
max_grain_amplitude_delta: 0.02
fail_action: block
concern_action: track
```

### Weekly Sequence Review

Less frequent but broader review for sequences in early development. Full three-pass
protocol but relaxed thresholds. Focus is on sequence-level arc and emotional pacing
rather than per-frame technical quality.

```yaml
review_cadence: weekly
min_sequence_length: 3
review_framerate: 24.0
emotional_pass_count: 2
sequence_context_range: 10
max_shadow_density_delta: 0.08
max_color_temp_delta: 400
max_exposure_delta_ev: 0.4
max_grain_amplitude_delta: 0.03
fail_action: block
concern_action: schedule
```

---

## Anti-Patterns

### 1. Single-Frame Review

**Symptom:** A rendered frame is pulled up on screen, evaluated for technical quality,
and approved or rejected in isolation. No adjacent shots are loaded. No playback at
speed. The frame is judged as a photograph, not as a beat in a sequence.

**Cause:** Time pressure, tooling friction (loading a full sequence is harder than
loading a single frame), and the screenshot culture of social media. The single frame
is the fundamental unit of CG presentation --- and it is the wrong unit for
temporal media.

**Fix:** Ban single-frame approval entirely. No frame receives a status (info, concern,
fail) until it has been seen in its sequence context at playback speed. The emotional
pass must precede the technical pass. A frame that cannot be reviewed in context cannot
be reviewed at all.

**Studio reference:** At Weta Digital (now Weta FX), the dailies theater has no "pause"
button accessible to reviewers. The projectionist controls playback. Shots are always
seen in motion first.

### 2. Opinion Without Reference

**Symptom:** Review notes contain subjective preferences without grounding in physical
reference or the visual bible. "I think the grain should be finer." "The plume feels
too dark." "Can we make it more dramatic?" These are feelings, not notes.

**Cause:** Reviewers have not internalized the reference photography or the visual
bible's material specifications. Without a shared standard, every review becomes a
negotiation of personal taste.

**Fix:** Every review note must reference either physical reference photography or
the visual bible. "The grain amplitude is 0.12; reference photography shows
approximately 0.05 at this density" is a note. "I think the grain is too coarse" is
an opinion. Opinions are welcome in the emotional pass; they are banned from the
technical and comparative passes.

### 3. Severity Inflation

**Symptom:** Everything is marked as "fail." The review produces 30 fail-severity notes
for a 5-shot sequence, blocking all progress. The team spends three days addressing
notes that should have been info or concern level, while genuine fail-level issues
receive the same priority as cosmetic preferences.

**Cause:** Reviewers have not calibrated their severity scale. The distinction between
info (tracking), concern (schedule fix), and fail (blocks approval) is not enforced.
When everything is urgent, nothing is urgent.

**Fix:** Enforce severity definitions with examples:
- **info:** "Grain reads slightly heavier in the upper-left quadrant" --- track it,
  fix if time permits, does not block
- **concern:** "Shadow density drifts 0.04 across the sequence" --- schedule fix in
  current sprint, blocks final tier but not working renders
- **fail:** "Shadow density jumps 0.12 at cut point, visible as lighting pop at
  playback speed" --- blocks approval, must be fixed before next review

A review with more than 3 fail-severity notes per shot should trigger a review of the
review: are all fails genuinely playback-visible at speed?

### 4. Notes Without Actionable Fixes

**Symptom:** Review notes identify problems but do not specify solutions. "The transition
feels wrong." "Something is off about shot 4." "The lighting is not working." The
artist receiving these notes must guess what the reviewer wants.

**Cause:** Reviewers identify emotional reactions (valid) but do not complete the
diagnostic cycle to determine root cause and prescribe a fix. The emotional pass is
delivered as final output rather than as input to the technical pass.

**Fix:** Every note must include a Fix field with a specific, actionable instruction.
If the reviewer cannot diagnose the technical cause, the note must be flagged as
"diagnosis needed" and the technical pass must be performed collaboratively with the
artist. A note without a fix is not a note --- it is a complaint.

---

## Validation Checklist

- [ ] Full sequence assembled before individual frame review
- [ ] Sequence contains minimum required shots (3 default, 5 for exhibition)
- [ ] Emotional pass played at speed without pausing (minimum 2 times)
- [ ] Emotional reactions recorded with timestamps within 2 seconds
- [ ] Technical pass completed: every emotional reaction diagnosed to root cause
- [ ] Comparative pass completed: current vs reference photography
- [ ] Comparative pass completed: current vs previous approved version (if any)
- [ ] All notes follow structured format (Frame, Severity, Pass, Observation, Fix)
- [ ] No notes lack actionable Fix field
- [ ] Severity levels calibrated: fail means playback-visible at speed
- [ ] Shadow density delta at cut points within threshold (0.05 default)
- [ ] Color temperature delta at cut points within threshold (300K default)
- [ ] Exposure delta at cut points within threshold (0.3 EV default)
- [ ] Grain amplitude delta at cut points within threshold (0.02 default)
- [ ] All fail-severity notes resolved before shot approval
- [ ] Fixed shots re-reviewed in sequence context (not in isolation)
- [ ] Review notes entered into the review log with date and reviewer
