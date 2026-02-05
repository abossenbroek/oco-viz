---
name: sketch-standard
user-invocable: false
---

# Sketch Tier — VFX Technical Standard

Fast iteration, form exploration. Minimal rendering. The only question: does the plume exist and is the camera pointed at it?

Source of truth: `configs/tiers/sketch.yaml`

---

## Evaluation Scope

Sketch tier evaluates **only 3 things**:

### 1. Existence

Is there geometry in the frame? A non-degenerate volume or point cloud must be visible. Any visual representation of the plume data counts.

### 2. Non-Degeneracy

The visible geometry is not degenerate:
- Not a single pixel
- Not a flat plane viewed edge-on
- Not entirely uniform (at least some density variation visible)
- Not corrupted (no NaN artifacts, no garbage pixels)

### 3. Orientation

The camera is pointed at the plume:
- Plume is within the frame
- Plume occupies at least some visible area (> 5% of frame)
- Plume is not entirely occluded or behind the camera

---

## Not Evaluated

The following are explicitly **not assessed** at sketch tier:

- Transfer function quality
- Lighting
- Turbulence / volume structure
- Edge treatment
- Composition aesthetics
- Color accuracy
- Post-processing quality

---

## Verdicts

- **pass**: Plume exists, is non-degenerate, and camera sees it
- **fail**: Black frame, missing geometry, camera pointing at nothing, degenerate output

There is no `conditional_pass` at sketch tier. It either works or it doesn't.
