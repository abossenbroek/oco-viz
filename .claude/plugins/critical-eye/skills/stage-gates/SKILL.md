---
name: stage-gates
user-invocable: false
---

# Stage Gates -- Visual QA Framework

Visual quality assessment at pipeline stage boundaries. Each stage gate defines
what visual evidence is expected before proceeding to the next pipeline stage.

Stage gates use the critical-eye's image analysis capabilities (pixel stats,
visual inspection) but apply stage-specific criteria rather than the full
artistic evaluation used for final renders.

---

## Gate Sequence

```
Stage 1 (Ingestion)       -> Stage 1 Gate (data visualization QA)
Stage 2 (Reconstruction)  -> Stage 2 Gate (field visualization QA)
Stage 3 (Conversion)      -> Stage 3 Gate (VDB render QA)
Stage 4 (Rendering)       -> [Use /critical-eye:review -- full dual-agent review]
```

Stage 4 (rendering) uses the full `/critical-eye:review` command with its
dual-agent VFX TD + Art Director architecture. Stage gates are for the
earlier pipeline stages where quick visual sanity checks are needed, not
full artistic evaluation.

---

## Gate Principle

Stage gates answer one question: **does the visual output of this pipeline
stage show what we expect to see?** They check for obvious failures (missing
data, corrupted fields, spatial misalignment) rather than artistic quality.

Each gate produces a verdict: `PASS`, `CONCERN`, or `FAIL`.

---

## Separation of Concerns

| Domain | Tool | What It Reviews |
|--------|------|----------------|
| Visual QA at stage boundaries | `/critical-eye:review-gate` | Stage output visualizations |
| Full artistic + technical review | `/critical-eye:review` | Final rendered images |
| Technical pipeline review | `/pipeline-expert:review-stage` | Configs, data files, parameters |

---

## Gate Skills

- `stage-1-gate`: Ingestion visual QA (data coverage, quality flags, ERA5 alignment)
- `stage-2-gate`: Reconstruction visual QA (spatial coherence, confidence, vertical extent)
- `stage-3-gate`: Conversion visual QA (morphology match, grid completeness, value range)
