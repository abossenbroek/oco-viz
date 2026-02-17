---
name: scout-tier
user-invocable: false
type: standard
primary_owner: shared
---

# Scout Tier Standard

Defines the minimum acceptable parameters for scout-tier production.
Scout tier is the fastest iteration cycle, used for creative direction
approval, timing validation, and composition exploration before
committing to higher-fidelity renders.

---

## Principle

Scout tier answers the question: "Is this the right idea?" It validates
creative direction, camera choreography, and narrative structure at the
lowest cost. Technical quality is intentionally relaxed to maximize
iteration speed. A scout render that nails the creative direction is
more valuable than a preview render that misses it.

---

## Technical Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| VDB resolution | 128^3 | Sufficient for volume shape and motion |
| Render resolution | HD (1920 x 1080) | Standard 16:9 |
| Samples per pixel | 64 spp | Acceptable noise floor for direction approval |
| Frame rate | 24 fps | Match delivery frame rate |
| Color space | ACEScg (working) | Pipeline consistency even at scout |
| Output format | EXR (half-float) | Linear data preserved |

---

## Acceptable Shortcuts

The following quality relaxations are permitted at scout tier:

| Area | Relaxation | Rationale |
|------|-----------|-----------|
| Sample count | 64 spp (vs 256+ preview) | Noise acceptable for direction calls |
| Lighting | Single key + ambient | Motivated lighting not yet required |
| Materials | Flat density-only shading | Material presets not yet applied |
| Post-processing | None or minimal | Bloom, fog, grain deferred to preview |
| OCIO/LUT | Working-space only, no show LUT | Grading deferred to preview |
| Deep compositing | Disabled | Not needed for direction approval |
| AOVs | Beauty pass only | Auxiliary passes deferred |

---

## Quality Floor

Even at scout tier, these minimums must be met:

| Criterion | Minimum | Rationale |
|-----------|---------|-----------|
| Volume visible | Plume structure identifiable | Cannot judge direction without seeing the subject |
| Camera path smooth | No discontinuities or jumps | Timing validation requires smooth motion |
| Frame count correct | Matches storyboard timing_map | Shot duration must be evaluable |
| Background clean | No render artifacts | Artifacts distract from direction evaluation |
| Units correct | Meters, Kelvin, m/s | Physical accuracy from origin (CLAUDE.md golden rule) |

---

## Approval Gate

Scout tier requires sign-off from:

| Agent | Role | What They Evaluate |
|-------|------|--------------------|
| storyboarder | Primary | Shot sequence, timing, emotional arc alignment |
| dp | Secondary | Camera choreography, basic composition |

Scout tier does NOT require:
- Pipeline-expert governance approval
- Critical-eye visual review
- Groundtruth physical validation (beyond basic unit checks)
- Colorist grading review

---

## Deliverables

A complete scout-tier delivery includes:

1. **Rendered frames**: EXR sequence at HD resolution
2. **collaboration YAML**: `shot_execution_delivery` with render stats
3. **Storyboard alignment**: Verification that shots match `timing_map`

---

## Progression to Preview

Scout tier is approved when the storyboarder confirms:
- Shot sequence tells the intended story
- Emotional arc reads correctly in playback
- Camera choreography supports the narrative
- No structural changes needed before investing in higher fidelity

Once approved, the dp may proceed to preview-tier rendering with
the locked creative direction.

---

## Anti-Patterns

- **Over-polishing scout**: Spending time on materials, grading, or post-processing at scout tier. The point is speed, not beauty.
- **Skipping scout**: Jumping directly to preview tier without direction approval. Scout exists to prevent expensive wrong-direction renders.
- **Wrong resolution**: Rendering at 4K "just in case" at scout tier. This wastes compute and defeats the iteration speed advantage.
- **Missing timing verification**: Rendering all frames but not verifying against the storyboard timing_map. Scout validates timing above all else.
- **Direction drift**: Making creative changes during scout render without updating the storyboard. The storyboard is the source of truth.

---

## Validation Checklist

- [ ] VDB resolution is 128^3
- [ ] Render resolution is 1920 x 1080 (HD)
- [ ] Samples per pixel is 64
- [ ] Frame count matches storyboard timing_map
- [ ] Camera path is smooth (no discontinuities)
- [ ] Volume structure is identifiable
- [ ] Background is clean (no artifacts)
- [ ] Units are correct (meters, Kelvin, m/s)
- [ ] ACEScg working color space
- [ ] EXR half-float output format
- [ ] Storyboarder sign-off obtained
