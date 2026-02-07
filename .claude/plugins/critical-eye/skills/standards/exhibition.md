---
name: exhibition-standard
user-invocable: false
---

> **Renderer guard:** This standard applies to **Karma XPU production renders** only.
> VTK pre-visualization output should be evaluated against the
> [VTK Preview Standard](vtk-preview.md) instead. Check the frame sidecar
> `pipeline.renderer` field to determine which standard applies.

# Exhibition Tier — VFX Technical Standard

Gallery-quality output. Every pixel must withstand 4K projection in a dark room. No compromises.

Source of truth: `configs/tiers/exhibition.yaml` + `plan/visual_language.yaml`

---

## 1. Transfer Function / Density-to-Luminance

### Physics

Beer-Lambert attenuation: denser regions absorb more light, but self-illumination means dense cores glow brighter. The TF maps density to luminance via the Soot palette.

### Correct Appearance

- Peak luminance is dirty near-white (`#c8c8c8`, RGB 200/200/200) — never clean white
- Opacity never exceeds 0.85 — volume depth is always visible through the densest core
- Low-density regions (0.0-0.2) have near-zero opacity — soot emerges gradually, not abruptly
- Tonal rolloff is smooth — no banding between density steps
- The periphery onset is gradual: trace wisps at `#1a1a1a` fade into black without a visible boundary

### Diagnosis

- **Clipping to white**: Peak pixel values > 210 in any channel → TF peak too high or exposure too hot
- **Hard opacity cutoff**: Visible boundary where volume starts → opacity ramp too steep at low density
- **Banding**: Visible steps in the grey gradient → insufficient TF sample points or quantization
- **Dead periphery**: Plume has a sharp outline with no wispy halo → opacity at low density is too high

### Adjustment Levers

- `transfer_function.color_points` — control density-to-luminance mapping
- `transfer_function.opacity_points` — control density-to-opacity mapping
- `postprocess.exposure` — global brightness multiplier (exhibition: 1.5)

---

## 2. Lighting: Internal Smoldering

### Physics

No external lights exist. The volume is its own light source. Dense regions scatter more internal light and appear brighter. Sparse regions are dim. This is self-illumination via ambient scattering, not directional lighting.

### Correct Appearance

- Zero visible directional shadow or specular highlight
- Dense core glows brighter than sparse periphery (inverse of external lighting)
- Uniform ambient quality — no hot spots, no directional bias
- The volume appears to smolder from within, as if containing trapped heat

### Config Reference

```yaml
scattering:
  ambient: 0.85
  diffuse: 0.0
  specular: 0.0
lighting:
  mode: smoldering
```

### Ghost Light (Anisotropic Forward Scatter)

Exhibition tier uses `scattering_anisotropy = 0.8` (strong forward scattering) to
create a "ghost rim-light" effect. Internal emission scatters preferentially toward
the camera from volume edges, producing subtle directional bias that solves the
"Floating Cotton Ball" problem (volumes reading as flat, featureless blobs).

This directional bias is **intentional** and must NOT be flagged as a failure.

**How to distinguish ghost light from external lighting:**
- **Ghost light (PASS)**: Directional bias varies with camera angle (it follows the
  emission-to-camera vector). Brightest at volume silhouette edges. No shadow cast.
  Source is internal emission scattered by anisotropic phase function.
- **External lighting (FAIL)**: Directional bias is fixed regardless of camera angle.
  One side consistently brighter. Shadow cast on opposite side. Source is a light
  prim or environment light.

### Diagnosis

- **Directional shading from external light**: One side consistently brighter across all camera angles → diffuse > 0 or external light present (FAIL)
- **Ghost rim-light at silhouette edges**: Subtle brightness at volume edges that shifts with camera → scattering_anisotropy working correctly (PASS)
- **Specular highlights**: Any bright spot that isn't density-correlated → specular > 0
- **Flat illumination**: No luminance variation between dense/sparse → ambient too low or TF not mapping density to brightness
- **Dark core with bright shell**: Interior darker than surface → lighting model inverted (external, not self-illumination)
- **No edge definition (cotton ball)**: Volume reads as featureless blob → scattering_anisotropy too low (< 0.6)

### Adjustment Levers

- `scattering.ambient` — self-illumination intensity (exhibition: 0.85)
- `scattering.diffuse` — must be 0.0 for exhibition
- `scattering.specular` — must be 0.0 for exhibition
- `scattering.anisotropy` — Henyey-Greenstein phase function (exhibition: 0.8, forward scatter)
- `lighting.mode` — must be `smoldering`

---

## 3. Turbulence / Volume Structure

### Physics

Multi-octave noise deforms the volume field, creating geological folding: large-scale folds with high-frequency grit at every scale. This is sedimentary layering, not atmospheric turbulence.

### Correct Appearance

- Visible multi-scale structure: large folds containing smaller folds containing fine grit
- 6 octaves of detail: from whole-plume deformation to sub-pixel texture
- Heavy, thick, sedimentary character — not wispy, not ethereal, not cloudlike
- Internal structure visible through semi-transparent regions
- Folding patterns suggest geological compression, not wind shear

### Diagnosis

- **Smooth blob**: No visible internal structure → insufficient turbulence octaves or amplitude
- **Wispy/ethereal**: Volume reads as smoke or cloud → turbulence weight too low, needs heavier falloff
- **Uniform noise**: All detail at same scale → single-octave noise, missing multi-scale structure
- **Chaotic/noisy**: No coherent large-scale form → high-frequency octaves dominating

### Adjustment Levers

- Turbulence octave count (target: 6)
- Octave amplitude falloff (heavier = more geological)
- Base frequency (lower = larger folds)
- Turbulence field seed

---

## 4. Edge Treatment: Granular Dissolution

### Physics

Volume boundaries do not fade smoothly. The continuous dense interior breaks into progressively smaller clumps, then individual soot particles that scatter outward like disintegrating ash.

### Correct Appearance

- Three-zone boundary: continuous interior → clumps/filaments → scattered particles
- No smooth alpha gradient at edges — the boundary is granular
- Individual particles visible at outer edge (at sufficient resolution)
- Particles inherit local motion with slight outward drift
- The dissolution feels physical — like ash crumbling, not digital fadeout

### Diagnosis

- **Smooth alpha fade**: Edge transitions smoothly from solid to transparent → no particle dissolution system active
- **Hard cutoff**: Plume has a sharp defined edge → opacity ramp too steep, no dissolution zone
- **Floating particles disconnected from volume**: Particles not following volume boundary → emission zone misconfigured
- **Too few particles**: Dissolution zone looks sparse → particle count too low for surface area

### Adjustment Levers

- Particle dissolution system enable/disable
- Dissolution zone width
- Particle count scaling
- Particle size distribution
- Outward drift velocity

---

## 5. Composition

### Physics

Camera placement, frame fill, and spatial arrangement. Exhibition tier mandates deliberate composition.

### Correct Appearance

- Frame fill: 60-80% of frame area occupied by non-black plume content
- Asymmetric off-center mass — plume is NOT centered in frame
- Vertical emphasis — composition suggests rising emissions, industrial stacks
- Pure black void surrounds the plume — no ground plane, no sky, no context
- Frame edges are absolute black to blend with dark room walls at gallery projection

### Config Reference

```yaml
composition:
  enabled: true
  asymmetric_offset: [0.05, 0.02]
  vertical_emphasis: true
```

### Diagnosis

- **Centered plume**: Mass of plume at frame center → asymmetric_offset too small or composition disabled
- **Underfilled frame**: Plume occupies < 60% → camera too distant or plume too small
- **Overfilled frame**: Plume > 80% or clipped at edges → camera too close
- **Non-black background**: Any pixel in the void registers above #000000 → background contamination or fog enabled
- **Horizontal emphasis**: Plume reads as spreading sideways → vertical_emphasis not applied

### Adjustment Levers

- `composition.asymmetric_offset` — [x, y] offset from center
- `composition.vertical_emphasis` — boolean
- Camera distance and field of view
- Volume scale

---

## 6. Color Purity

### Physics

Soot is achromatic. R = G = B at every pixel. The palette is strictly greyscale on black. Any color is contamination.

### Correct Appearance

- Every pixel satisfies: |R - G| <= 2, |R - B| <= 2, |G - B| <= 2 (tolerance: 2 levels)
- Background is pure `#000000` — no color cast in the void
- No warmth, no coolness — only density, texture, and luminance
- Peak pixels are grey, not tinted

### Diagnosis

- **Color cast in plume**: Channel divergence > 2 levels → fog color tinting, or post-processing introducing color
- **Colored background**: Void pixels not `#000000` → fog/bloom bleeding color into background
- **Warm peak**: Peak pixels have R > G or R > B → transfer function has color contamination

### Adjustment Levers

- `postprocess.fog_enabled` — must be false for exhibition
- `postprocess.bloom_enabled` — must be false for exhibition
- Transfer function color points — all channels must be equal
- `postprocess.fog_color` — irrelevant if fog disabled

---

## 7. Post-Processing

### Physics

Exhibition tier uses ACES tonemapping only. No fog. No bloom. The volume stands alone.

ACES can be applied via Narkowicz approximation (current VTK pipeline) or OCIO-driven
transforms (exhibition Karma/Nuke pipeline). Both produce equivalent visual results
(< 2% dE2000 difference in achromatic range). The critical-eye review evaluates the
visual result, not the implementation mechanism.

### Correct Appearance

- ACES tonemap produces smooth rolloff in highlights — no hard clipping
- No fog haze in the void — background remains pure black
- No bloom glow around bright regions — edges stay sharp
- Exposure at 1.5 — provides headroom without crushing shadows

### Config Reference

```yaml
postprocess:
  fog_enabled: false
  bloom_enabled: false
  exposure: 1.5
```

### Diagnosis

- **Haze in void**: Background pixels > #000000 in non-plume regions → fog enabled
- **Glow around plume edges**: Bloom halo visible → bloom enabled
- **Crushed shadows**: Low-density regions have no visible detail → exposure too low
- **Blown highlights**: Peak regions at #ffffff → exposure too high or tonemap not applied
- **Harsh tonal transitions**: Abrupt brightness changes → tonemap not ACES or not applied

### Adjustment Levers

- `postprocess.fog_enabled` — must be false
- `postprocess.bloom_enabled` — must be false
- `postprocess.exposure` — exhibition: 1.5
- Tonemapping operator selection
