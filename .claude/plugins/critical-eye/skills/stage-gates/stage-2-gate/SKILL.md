---
name: stage-2-gate
user-invocable: false
---

# Stage 2 Gate -- Reconstruction Visual QA

Visual quality assessment for Stage 2 (3D Reconstruction) outputs. Reviews
visualizations of the assimilated atmospheric field to verify spatial coherence,
confidence calibration, and physically plausible plume structure.

---

## What to Check

- **Volume slice**: Cross-section shows plume structure with spatial coherence
- **Confidence overlay**: High confidence near observations, gradient to low in gaps
- **Wind field**: Vector arrows align with expected atmospheric flow
- **Vertical profile**: Plume extent reasonable for boundary layer height

---

## Visual Criteria

| Check | What to Look For | PASS If | CONCERN If | FAIL If |
|-------|-----------------|---------|------------|---------|
| Spatial coherence | Smooth gradients, no salt-and-pepper | Continuous, smooth field | Minor noise in low-confidence regions | Noisy or discontinuous field |
| Plume structure | Recognizable plume morphology | Clear plume shape with gradient edges | Plume visible but diffuse | Uniform or random field (no structure) |
| Confidence calibration | Spatial structure matching data density | High near soundings, low in gaps | Visible structure but noisy | Uniform confidence (assimilation failure) |
| Vertical extent | Within 2x boundary layer height (BLH) | Plume contained within BLH | Extends to 1.5-2x BLH | Extends to stratosphere |
| Wind consistency | Flow direction matches ERA5 input | Vectors align with plume elongation | Minor misalignment | Flow contradicts plume shape |

---

## Procedure

1. Read the stage output visualization image (typically a Z-slice or cross-section)
2. Run `pixi run image-stats` for quantitative pixel measurements
3. Check each criterion in the table above
4. Verify that field gradients are smooth (no checkerboard or ringing artifacts)
5. Produce verdict: PASS / CONCERN / FAIL with specific observations

---

## Common Failure Modes

- Checkerboard pattern (assimilation numerical instability)
- Uniform field with no spatial structure (failed data insertion)
- Plume extending to domain top (missing boundary layer constraint)
- Confidence grid is spatially uniform (background covariance too isotropic)
- Salt-and-pepper noise (insufficient smoothing or too few iterations)
