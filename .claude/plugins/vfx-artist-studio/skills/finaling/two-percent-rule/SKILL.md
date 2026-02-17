---
name: two-percent-rule
user-invocable: false
type: instruction
primary_owner: vfx-supe
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# The Two-Percent Rule --- Precision Craftsmanship in the Final Mile

The last 2% of quality takes 50% of the time --- and it is worth every second. In
VFX production the difference between a shot that passes and a shot that transcends
lives entirely in the finaling phase: the systematic elimination of every visible
artifact, discontinuity, and quality shortfall that separates "good enough" from
"exhibition-ready." Finaling is not creative work. It is not lookdev. It is not
art direction. It is precision craftsmanship --- the meticulous verification that every
parameter is locked, every artifact is eliminated, every transition is smooth, and every
frame meets the specification established during creative approval.

The two-percent rule acknowledges a painful truth about quality curves: the first 80%
of quality comes from the first 20% of effort (Pareto), the next 18% comes from another
30% of effort (diminishing returns), and the final 2% requires the remaining 50% of
effort (asymptotic perfection). Most projects stop at 98%. Exhibition-quality work does
not.

> "God is in the details." --- Ludwig Mies van der Rohe

---

## Principle

Shot finaling is the systematic elimination of every visible artifact, discontinuity,
and quality shortfall in the final 2% of the quality curve. It is not creative work ---
it is precision craftsmanship. Finaling begins only after creative approval: the
lookdev is locked, the art direction is approved, the transfer functions are set, and
the continuity ledger is fully populated. During finaling, no creative parameter may
be changed. If a creative issue is discovered during finaling, the shot returns to
lookdev --- finaling does not fix creative problems, it eliminates technical ones.

The finaling checklist is executed in strict order. Each step gates the next. Skipping
a step invalidates all subsequent steps. The checklist is not a suggestion --- it is
the quality specification, and every item must pass before the shot is approved for
delivery.

---

## Procedure

### Step 1 --- Parameter Lock Verification

Before any finaling work begins, verify that all wedge parameters are human-locked in
the continuity ledger. No parameter should be agent-guessed, auto-tuned, or left at
default values. Every value must trace to a human creative decision documented in the
ledger.

```
PARAMETER LOCK VERIFICATION:
For each parameter P in render config:
  1. Look up P in continuity ledger
  2. Verify locked_by == "human" (not "agent", not "default", not "auto")
  3. Verify locked_value matches actual value in render config
  4. Verify variance_tolerance is 0.0 for creative parameters
  5. If ANY parameter fails: STOP finaling, return to lookdev

STATUS: All parameters locked?  [ ] YES  [ ] NO → return to lookdev
```

A single unlocked parameter invalidates the entire finaling pass. There is no
"mostly locked" --- either the creative decisions are fully committed or finaling
has not begun.

### Step 2 --- Black Level Audit

Verify pure black background. The background color must be exactly #000000 with zero
noise floor, zero light leaks, and zero residual density. Any non-zero background
value creates a haze that reduces contrast, reveals compositing boundaries, and
destroys the void-as-negative-space design intent.

```
BLACK LEVEL AUDIT:
1. Sample background at 20 random positions outside plume bounding box
2. For each sample:
   - R channel: must be exactly 0
   - G channel: must be exactly 0
   - B channel: must be exactly 0
3. Compute max(R, G, B) across all samples
4. If max > 0: identify and eliminate source (ambient light, scatter leak, noise floor)
5. After elimination: re-sample and verify

TOLERANCE: 0.0 (exact zero required)
```

Common sources of non-zero background:
- Ambient light contribution (set to 0.0 during finaling)
- Volume scatter bleeding into empty regions (check scatter radius)
- Noise floor from denoising algorithms (verify OIDN produces true zero in empty regions)
- Residual density outside the plume bounding box (verify VDB sparsity)

### Step 3 --- Grain Consistency

The Paper Grain Manifold (from the fraser-shift methodology) must read correctly at
both low and high density regions. Grain is not uniform --- it varies with exposure
and must do so consistently across the entire density range.

```
GRAIN CONSISTENCY CHECK:
1. Select region at density ~0.1 (low-density halo)
   - Measure grain amplitude
   - Measure grain spatial frequency
   - Compare against locked grain parameters for low-density range

2. Select region at density ~0.8 (high-density core)
   - Measure grain amplitude
   - Measure grain spatial frequency
   - Compare against locked grain parameters for high-density range

3. Verify grain_amplitude(0.8) < grain_amplitude(0.1)
   (exposure-dependent grain: less grain in brighter/denser regions)

4. Verify grain has per-channel variation (R, G, B patterns are independent)

5. Verify temporal stability: grain at frame N partially persists at frame N+1
   (correlation coefficient > 0.2, < 0.5)
```

### Step 4 --- Crust Integrity

The dual-state crust shader (if active) creates a transition between the plume core
material and the plume edge material. This transition must be smooth --- no hard edges,
no visible boundary between states, no aliasing at the transition zone.

```
CRUST INTEGRITY CHECK:
1. Identify crust transition zone (density threshold where shader state changes)
2. Sample opacity and color at 10 points across the transition:
   - 5 points on the interior side (descending density)
   - 5 points on the exterior side (ascending density)
3. Verify monotonic transition: no sudden jumps in opacity or color
4. Verify gradient smoothness: first derivative is continuous (no corners)
5. Verify aliasing: no stair-step artifacts at any viewing angle
6. Verify consistency: transition reads the same from all camera angles
```

### Step 5 --- Emission Behavior

If the plume has self-emission (thermal glow, hot gas visualization), verify that the
arrhythmic pulse behavior is perceptible but not distracting. The emission should
breathe --- not flash, not strobe, not cycle with mechanical regularity.

```
EMISSION BEHAVIOR CHECK:
1. Measure emission intensity over 120 frames (5 seconds at 24fps)
2. Compute FFT of intensity curve
3. Verify: no dominant frequency peak (arrhythmic, not periodic)
4. Verify: amplitude variation between 5% and 15% of mean
   - Below 5%: pulse is imperceptible, looks static
   - Above 15%: pulse is distracting, looks like flicker
5. Verify: no zero-crossing (emission never turns fully off)
6. Verify: rate of change is smooth (no sudden jumps)
```

### Step 6 --- Temporal Stability

Verify that the rendered sequence is temporally stable: no flicker, no popping, and
denoising is effective without introducing temporal artifacts.

```
TEMPORAL STABILITY CHECK:
1. For each pixel position P in a grid (100 sample points):
   - Measure luminance at P across all frames in the shot
   - Compute frame-to-frame variance: var(L[n+1] - L[n])
   - If variance > flicker_max_variance: flag as flicker

2. For static regions (no plume motion):
   - Variance must be < 0.001 (essentially zero)
   - Any non-zero variance in static regions indicates render instability

3. OIDN temporal denoising check:
   - Compare denoised vs raw in a motion region
   - Verify denoising does not introduce ghosting (trailing edge artifacts)
   - Verify denoising does not introduce temporal lag (smoothed motion)

4. Overall temporal coherence:
   - Play at 2x speed: no visible flicker or popping
   - Play at 0.5x speed: no visible artifacts that are masked at normal speed
```

### Step 7 --- Boundary Dissolution

The plume-to-void boundary must dissolve rather than clip. There should be no visible
edge where the plume "ends" --- the density should attenuate smoothly to zero, and the
opacity transition should be imperceptible.

```
BOUNDARY DISSOLUTION CHECK:
1. Identify plume boundary contour (density = visibility threshold)
2. At 20 points along the boundary:
   - Measure density gradient (should be gradual, not steep)
   - Measure opacity gradient (should follow density smoothly)
   - Verify no hard edge visible at 200% zoom
3. Check for clipping artifacts:
   - Transfer function maps density to opacity: verify no step function
   - Opacity must reach 0.0 before density reaches 0.0 (dissolve, not clip)
4. Verify boundary reads as atmospheric dissolution, not as a surface
```

### Step 8 --- Cross-Shot Parameter Match

Final verification that all parameters match the continuity ledger across every shot
in the sequence. This is the last gate before delivery approval.

```
CROSS-SHOT PARAMETER MATCH:
For each shot S in the sequence:
  For each parameter P in the continuity ledger:
    actual = read_parameter(S, P)
    locked = ledger.get(P).locked_value
    tolerance = ledger.get(P).variance_tolerance
    IF abs(actual - locked) > tolerance:
      FAIL: "Shot {S}, parameter {P}: actual={actual}, locked={locked}, delta={delta}"

All parameters must pass. A single mismatch blocks delivery.
```

---

## Parameters

### Black Level Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `black_level_tolerance` | float | 0.0 | 0.0 | Maximum background value (must be exact zero) |
| `black_sample_count` | int | 20 | 10 - 50 | Number of background sample positions |
| `ambient_intensity_final` | float | 0.0 | 0.0 | Ambient light during finaling (must be zero) |

### Grain Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_check_densities` | list | [0.1, 0.8] | --- | Density values at which grain is verified |
| `grain_temporal_correlation_min` | float | 0.2 | 0.1 - 0.4 | Minimum grain temporal persistence |
| `grain_temporal_correlation_max` | float | 0.5 | 0.3 - 0.7 | Maximum grain temporal persistence |
| `grain_channel_independence` | bool | true | --- | RGB channels must have independent grain patterns |

### Temporal Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `flicker_max_variance` | float | 0.005 | 0.001 - 0.01 | Maximum frame-to-frame luminance variance |
| `static_region_max_variance` | float | 0.001 | 0.0 - 0.002 | Maximum variance in regions with no plume motion |
| `temporal_check_speeds` | list | [0.5, 1.0, 2.0] | --- | Playback speeds at which temporal stability is checked |

### Boundary Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `boundary_sample_count` | int | 20 | 10 - 50 | Number of points sampled along plume boundary |
| `boundary_gradient_max` | float | 0.3 | 0.1 - 0.5 | Maximum density gradient at boundary (normalized/voxel) |
| `boundary_hard_edge_tolerance` | float | 0.0 | 0.0 | Hard edges at boundary (must be zero) |

### Emission Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `emission_amplitude_min` | float | 0.05 | 0.02 - 0.08 | Minimum emission pulse amplitude (fraction of mean) |
| `emission_amplitude_max` | float | 0.15 | 0.10 - 0.25 | Maximum emission pulse amplitude (fraction of mean) |
| `emission_dominant_freq_max` | float | 0.0 | 0.0 | Maximum dominant frequency in pulse FFT (must be arrhythmic) |

---

## Presets

### Exhibition Final

Maximum precision. Every check at its strictest tolerance. No waivers, no exemptions.
This is the "projected on a gallery wall at 4K" standard.

```yaml
black_level_tolerance: 0.0
black_sample_count: 50
grain_check_densities: [0.1, 0.3, 0.5, 0.8]
grain_temporal_correlation_min: 0.2
grain_temporal_correlation_max: 0.5
flicker_max_variance: 0.002
static_region_max_variance: 0.0005
boundary_sample_count: 40
boundary_gradient_max: 0.2
emission_amplitude_min: 0.05
emission_amplitude_max: 0.12
```

### Preview Final

Standard precision for preview-tier renders. Tolerances slightly relaxed to account
for lower resolution and faster iteration cycles. Still catches all playback-visible
artifacts.

```yaml
black_level_tolerance: 0.0
black_sample_count: 20
grain_check_densities: [0.1, 0.8]
grain_temporal_correlation_min: 0.15
grain_temporal_correlation_max: 0.6
flicker_max_variance: 0.005
static_region_max_variance: 0.001
boundary_sample_count: 20
boundary_gradient_max: 0.3
emission_amplitude_min: 0.03
emission_amplitude_max: 0.18
```

### Scout Validation

Minimal finaling checks for scout-tier renders. Only catches critical failures that
would invalidate the creative direction. Parameter lock verification is advisory,
not blocking.

```yaml
black_level_tolerance: 0.0
black_sample_count: 10
grain_check_densities: [0.1, 0.8]
flicker_max_variance: 0.01
static_region_max_variance: 0.005
boundary_sample_count: 10
boundary_gradient_max: 0.5
```

---

## Anti-Patterns

### 1. Creative Changes During Finaling

**Symptom:** The artist discovers a "better" transfer function, lighting setup, or
grain texture during finaling and implements the creative change. The shot now looks
different from its neighbors, the continuity ledger is out of date, and the finaling
checklist must restart from step 1.

**Cause:** Finaling reveals the image at its highest scrutiny. Details that were
invisible during lookdev become visible during the finaling microscope. The temptation
to "improve" is irresistible --- but finaling is not lookdev.

**Fix:** Hard boundary between lookdev and finaling. If a creative issue is discovered
during finaling, the shot returns to lookdev with a formal change request. The
continuity ledger is updated. Creative approval is re-obtained. Only then does
finaling restart. No creative changes are permitted within the finaling phase.

### 2. Skipping Parameter Lock Verification

**Symptom:** Finaling begins with unlocked parameters. The artist assumes the values
are correct because "they looked right in the last render." During the finaling process,
subtly wrong parameters go undetected because there is no locked reference to compare
against.

**Cause:** Parameter lock verification is perceived as bureaucratic overhead. It adds
time and does not produce visible improvement --- until the moment an unlocked parameter
drifts and a shot fails continuity in the sequence review.

**Fix:** Step 1 is a gate. If any parameter is unlocked, finaling does not begin.
There is no partial finaling. The verification takes 5 minutes and prevents days of
rework.

### 3. Finaling Single Shots

**Symptom:** Each shot is finaled independently. The artist spends 4 hours perfecting
shot 3, then 4 hours on shot 4, then discovers they do not match when assembled. The
cross-shot parameter match (step 8) catches the mismatch, but 8 hours of work must be
partially redone.

**Cause:** Working on shots independently rather than in sequence context. The
finaling checklist is correct for each shot in isolation but does not catch inter-shot
issues until the final step.

**Fix:** Final in sequence context, always. Steps 1-7 are performed per-shot, but
after every 2-3 shots, play the sequence at speed and verify continuity. Step 8
(cross-shot match) should confirm what the sequence review already established, not
reveal new problems.

### 4. Tolerating Near-Zero

**Symptom:** The background reads #010101 instead of #000000. The grain variance is
0.006 instead of 0.005. The boundary gradient is 0.31 instead of 0.30. Each value is
"close enough" and individually imperceptible. But five "close enough" values compound:
the image has a subtle haze, a slight grittiness, and a faint edge --- none visible in
isolation, all visible in combination.

**Cause:** Confusing "imperceptible" with "zero." In the asymptotic 2% of the quality
curve, tolerances are exact for a reason. Near-zero is not zero. The tolerance exists
because values within tolerance genuinely do not compound; values outside tolerance do.

**Fix:** Tolerances are not suggestions. They are specifications. If the parameter is
`black_level_tolerance: 0.0`, the value must be 0.0 --- not 0.001, not "approximately
zero." If a tolerance seems unreasonable, challenge the specification in lookdev, not
during finaling.

---

## Validation Checklist

- [ ] All wedge parameters verified as human-locked in continuity ledger (Step 1)
- [ ] No parameters have `locked_by` of "agent", "default", or "auto"
- [ ] Background is exactly #000000 at all sample positions (Step 2)
- [ ] No ambient light contribution during finaling render
- [ ] Grain reads correctly at density 0.1 (low-density region) (Step 3)
- [ ] Grain reads correctly at density 0.8 (high-density region) (Step 3)
- [ ] Grain amplitude decreases with increasing density (exposure-dependent)
- [ ] Grain has per-channel independence (R, G, B patterns differ)
- [ ] Grain temporal correlation within range (0.2-0.5)
- [ ] Crust transitions are smooth with no hard edges (Step 4)
- [ ] Crust transitions are monotonic (no sudden jumps)
- [ ] Emission pulse is arrhythmic (no dominant frequency in FFT) (Step 5)
- [ ] Emission amplitude between 5% and 15% of mean intensity
- [ ] No temporal flicker exceeding variance threshold (Step 6)
- [ ] Static regions have near-zero variance (< 0.001)
- [ ] OIDN temporal denoising verified: no ghosting or lag
- [ ] Plume boundary dissolves rather than clips (Step 7)
- [ ] No hard edges visible at 200% zoom along boundary
- [ ] Opacity reaches 0.0 before density reaches 0.0
- [ ] All parameters match continuity ledger across all shots (Step 8)
- [ ] Cross-shot parameter match: zero failures
- [ ] No creative changes were made during the finaling phase
