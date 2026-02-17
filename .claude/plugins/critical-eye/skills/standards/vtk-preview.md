---
name: vtk-preview-standard
user-invocable: false
---

# VTK Preview — Pre-Visualization Quality Standard

Pre-visualization output from the VTK renderer (Stage 0). These images validate
creative direction, timing, composition, and transfer function design. They are
NOT exhibition-quality — that requires the Karma XPU production renderer.

Source of truth: `configs/tiers/study.yaml` + `plan/visual_language.yaml`

---

## What to Evaluate

VTK pre-viz images should be judged on whether they communicate the intended
creative direction, not on final rendering quality.

### Pass Criteria

1. **Transfer function reads correctly**: Soot palette visible — trace wisps
   at low density, dirty near-white at peak. No banding, no clipping.
2. **Volume structure is legible**: Turbulence creates visible multi-scale
   folding. The plume is not a smooth blob.
3. **Composition communicates intent**: Frame fill, camera distance, and
   vertical emphasis match the shot design.
4. **Achromatic discipline**: R = G = B within tolerance (+/- 5 levels for study tier).
5. **Post-processing appropriate for tier**: Study tier uses fog + bloom + ACES.
   Exhibition-tier post-processing (ACES only) is acceptable but not required.

### Known VTK Limitations (Do NOT Fail)

These are inherent VTK renderer limitations. They are expected in pre-viz
and will be resolved by the Karma XPU production renderer:

- **No true path-traced scattering**: VTK uses emission mode, not physical
  scattering. Volumes may look flatter than production renders.
- **Limited edge dissolution**: VTK cannot render particle dissolution at
  volume boundaries. Smooth falloff is acceptable.
- **No ghost light rim**: The scattering_anisotropy=0.8 ghost light effect
  requires path tracing. VTK images may lack edge definition.
- **Banding in near-black**: 8-bit or 16-bit PNG output may show quantization
  in very low-density regions. This is acceptable for pre-viz.
- **No motion blur**: VTK does not support motion blur. Static frames only.

### Fail Criteria

These indicate actual problems that need fixing regardless of renderer:

- **Non-achromatic pixels**: Color contamination (hue visible in plume)
- **Empty frame**: No visible plume content
- **Clipped to white**: Peak pixels at pure white (#ffffff) instead of dirty near-white
- **Inverted lighting**: Surface brighter than interior (external light present)
- **Numerical artifacts**: NaN/Inf values visible as black holes or white spots

---

## Tier Mapping

| Tier | Expected Renderer | Standard |
|------|-------------------|----------|
| Sketch | VTK | Minimal — form and timing only |
| Study | VTK | This document (VTK Preview) |
| Exhibition | Karma XPU | [Exhibition Standard](exhibition.md) |
