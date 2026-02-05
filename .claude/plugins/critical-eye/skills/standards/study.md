---
name: study-standard
user-invocable: false
---

# Study Tier — VFX Technical Standard

MVP density/TF refinement quality. Functional rendering for iteration. Relaxed standards compared to exhibition — fog, bloom, and directional lighting are expected.

Source of truth: `configs/tiers/study.yaml` + `plan/visual_language.yaml`

---

## 1. Transfer Function / Density-to-Luminance

### Correct Appearance

- Full Soot palette applied via soot.json transfer function
- Peak luminance is dirty near-white (`#c8c8c8`) — same as exhibition
- Opacity ramp should produce visible volume depth — not opaque blobs
- Smooth tonal rolloff — banding is still a defect at study tier

### Acceptable Relaxations

- Opacity can reach up to 0.90 (vs 0.85 for exhibition)
- Periphery onset may be slightly more abrupt than exhibition

### Blocking Defects

- No transfer function applied (single flat grey)
- Opacity at 1.0 — completely opaque, no depth
- Severe banding visible in smooth gradients

---

## 2. Lighting

### Correct Appearance

- Basic 3-point or directional volume shading
- Diffuse response creates visible depth cues — one side brighter than other is acceptable
- Ambient fills shadow regions — no completely black interior zones

### Config Reference

```yaml
scattering:
  ambient: 0.12
  diffuse: 0.75
```

### Acceptable Relaxations

- External directional light is expected (diffuse = 0.75)
- Specular may be present at low levels
- Directional shading is a feature, not a defect

### Blocking Defects

- Completely flat illumination (no depth cues at all)
- Harsh specular highlights that distract from volume structure
- Lighting so strong it washes out density variation

---

## 3. Turbulence / Volume Structure

### Correct Appearance

- Basic noise deformation (2-3 octaves)
- Some visible internal structure — not a smooth blob
- Geological folding not required — basic turbulent variation sufficient

### Acceptable Relaxations

- Single-scale noise is acceptable
- Wispy/ethereal character not penalized
- Less weight/heaviness than exhibition

### Blocking Defects

- Perfectly smooth sphere/ellipsoid with zero structure
- Turbulence so extreme the form is unrecognizable

---

## 4. Edge Treatment

### Correct Appearance

- Smooth volume falloff at boundaries
- No particle dissolution required
- Edges should still be soft, not hard-clipped

### Acceptable Relaxations

- Smooth alpha gradient is the expected edge treatment
- No granular dissolution, no particle system

### Blocking Defects

- Hard binary edge (fully opaque to fully transparent in 1 pixel)
- No visible edge transition at all

---

## 5. Composition

### Correct Appearance

- Default camera position acceptable
- Plume visible and roughly centered or slightly off-center
- No deliberate composition required

### Acceptable Relaxations

- Centered plume is fine
- Frame fill can range from 30-90%
- No asymmetric offset required
- No vertical emphasis required

### Blocking Defects

- Camera pointing at nothing (plume not in frame)
- Plume occupies < 10% of frame
- Plume severely clipped (> 50% outside frame)

---

## 6. Color Purity

### Correct Appearance

- Base palette is Soot achromatic grey scale
- Slight color tint from fog is acceptable

### Config Reference

```yaml
postprocess:
  fog_color: [0.08, 0.08, 0.12]
```

### Acceptable Relaxations

- Channel divergence up to 5 levels acceptable (fog introduces slight blue tint)
- Fog color in near-neutral dark range — slight tinting expected

### Blocking Defects

- Vivid color in the plume (strong hue saturation)
- Background strongly colored (not near-black)
- Rainbow or multi-colored artifacts

---

## 7. Post-Processing

### Correct Appearance

- Fog + bloom + ACES tonemap pipeline active
- Fog adds atmospheric depth without drowning the volume
- Bloom adds gentle glow around bright regions
- ACES tonemap provides smooth highlight rolloff

### Config Reference

```yaml
postprocess:
  fog_enabled: true
  bloom_enabled: true
  exposure: 1.3
  fog_color: [0.08, 0.08, 0.12]
```

### Acceptable Relaxations

- Fog haze in the void is expected (background won't be pure black)
- Bloom glow around plume edges is expected
- Exposure range 1.0-1.5 acceptable

### Blocking Defects

- Fog so thick the plume is invisible
- Bloom so strong it creates a white halo
- No tonemapping applied (raw HDR values causing extreme contrast)
- Exposure so high the image is washed out
