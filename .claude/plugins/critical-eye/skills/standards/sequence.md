---
name: sequence-standard
user-invocable: false
---

# Sequence Standard — Temporal Coherence Reference

Loaded in addition to the tier standard when `--sequence` flag is present and multiple frames are provided. Evaluates frame-to-frame consistency.

---

## 1. Luminance Stability

### Correct Behavior

- Mean frame luminance varies smoothly between frames — no sudden jumps
- Maximum per-frame luminance change: <= 5% of mean for exhibition, <= 10% for study
- No single-frame flicker (bright frame followed by dark frame)

### Diagnosis

- **Flicker**: Frame N is significantly brighter/darker than frames N-1 and N+1 → temporal instability in TF application or lighting
- **Progressive drift**: Luminance steadily increases or decreases without motivation → accumulation error or camera-dependent lighting
- **Sudden jump**: Abrupt luminance change at a specific frame → discontinuity in animation parameter

---

## 2. Camera Motion Continuity

### Correct Behavior

- Camera position changes smoothly between frames
- Easing function produces expected acceleration profile:
  - Exhibition (`heavy_ease_in`): slow start, very gradual acceleration, glacial pace
  - Study (`smoothstep`): smooth S-curve acceleration/deceleration
- No snap transitions, no teleportation, no direction reversals without motivation

### Diagnosis

- **Jump cut**: Camera position discontinuity between frames → missing interpolation or wrong frame order
- **Jerky motion**: Visible acceleration changes frame-to-frame → easing function not smooth
- **Wrong tempo**: Motion too fast for tier → tempo_multiplier incorrect (exhibition should be 0.3, study 1.0)

---

## 3. Volume Evolution Coherence

### Correct Behavior

- Volume deforms continuously between frames — no popping
- Turbulence field evolves smoothly (if animated)
- Density distribution changes gradually
- Particle dissolution (exhibition) tracks volume boundary continuously

### Diagnosis

- **Volume popping**: Sudden shape change between frames → turbulence seed jumping or interpolation failure
- **Density flash**: Sudden appearance/disappearance of density regions → discontinuous data input
- **Particle teleportation**: Dissolution particles jump position → no temporal coherence in particle system

---

## 4. Motion Tempo

### Tier Expectations

| Tier | Expected Tempo | Motion Character |
|------|---------------|-----------------|
| Exhibition | Glacial (tempo_multiplier: 0.3) | Heavy, inexorable, slow dread |
| Study | Standard (tempo_multiplier: 1.0) | Normal playback speed |
| Sketch | Fast (any speed) | Not evaluated |

### Diagnosis

- **Too fast for exhibition**: Noticeable frame-to-frame changes → tempo_multiplier too high
- **Too slow for study**: Almost no visible change between frames → tempo_multiplier too low
