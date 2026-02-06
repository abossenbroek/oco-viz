---
name: rendering-quality
user-invocable: false
---

# Rendering Quality -- Stage 4: Rendering Gate

Technical quality of the rendered output. VTK prototype and production
renderer (RenderMan/Arnold) share common quality criteria.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Sample distance | <= grid_spacing / 10 (exhibition) | Render setting verification |
| Banding | None visible (jittering enabled) | Visual inspection of smooth gradients |
| Background purity | #000000 (exhibition), <= #0f0f0f (study) | Corner pixel value measurement |
| TF control points | >= 14 color, >= 25 opacity (exhibition) | Transfer function point count |
| TF peak | #c8c8c8 max (dirty near-white) | TF color ramp endpoint check |
| Max opacity | 0.85 (exhibition), 0.90 (study) | TF opacity curve maximum |
| Deep output validity | Per-sample position + density correct | Deep file inspection (production only) |
| AOV completeness | beauty + emission + absorption + residual | Render output layer check (production only) |
| Emission mode | ShadeOff() active (VTK) or equivalent | Render mode verification |
| Noise/grain | No render noise in final output | Visual inspection at 100% zoom |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | Sample distance meets threshold. No banding. Background pure black. TF meets point count and range requirements. Deep output valid (production). All AOVs present. No render noise. |
| CONCERN | Sample distance adequate but not optimal. Minor banding in extreme gradients. Background near-black. TF close to thresholds. Deep output present but missing one AOV. |
| FAIL | Sample distance too large (visible stepping). Banding in smooth regions. Background contaminated. TF below minimum points (contouring visible). Deep output missing or corrupt. Emission mode not active. |

---

## Agent Responsibility

Primary: Tonalist (TF and color pipeline)
Secondary: Sculptor (volume sampling and material quality)
