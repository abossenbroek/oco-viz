---
name: stage-3-gate
user-invocable: false
---

# Stage 3 Gate -- Conversion Visual QA

Visual quality assessment for Stage 3 (VDB Conversion) outputs. Reviews
basic volume renders of converted VDB assets to verify that format conversion
preserved the source data morphology, grid structure, and value ranges.

---

## What to Check

- **VDB render**: Basic volume render matches source reconstruction morphology
- **Multi-grid**: All 5 grids present and independently renderable
- **Metadata**: Voxel size, origin, and data range preserved through conversion
- **Value range**: Histogram of converted values matches source distribution

---

## Visual Criteria

| Check | What to Look For | PASS If | CONCERN If | FAIL If |
|-------|-----------------|---------|------------|---------|
| Morphology match | VDB render resembles reconstruction output | Recognizable same shape and structure | Shape matches but minor artifacts | Unrecognizable shape or rotated volume |
| Grid completeness | All 5 layers render independently | All 5 grids visible (co2, wind, temp, pressure, confidence) | 4 of 5 grids render (non-critical missing) | Missing critical grids (co2 or wind) |
| Value range | Histogram similar to source distribution | Distribution shape matches, range within 1% | Range within 2%, minor histogram shift | Values clipped, inverted, or > 2% range error |
| Resolution | Sufficient detail at target grid size | Detail consistent with source resolution | Minor smoothing beyond source | Blocky voxelization or over-smoothed |
| Axis orientation | Volume oriented correctly in world space | Correct up/north/east orientation | Minor rotation (< 5 deg) | 90-degree rotation or mirror (axis reorder error) |

---

## Procedure

1. Read the stage output visualization image (typically a basic volume render preview)
2. Run `pixi run image-stats` for quantitative pixel measurements
3. Compare visually against Stage 2 reconstruction output if available
4. Check each criterion in the table above
5. Produce verdict: PASS / CONCERN / FAIL with specific observations

---

## Common Failure Modes

- Rotated or mirrored volume (VTK x-fastest to numpy z-fastest axis reorder error)
- Missing grids (incomplete conversion loop or wrong grid names)
- Value clamping (float32 overflow or incorrect normalization)
- Blocky appearance (voxel size mismatch between source and VDB transform)
- Empty volume (zero-fill from wrong array shape or dtype mismatch)

---

## Conservation Readiness Check

After all visual QA checks above, verify conservation package status. This is a
WARNING-level check --- it does not block the stage gate but surfaces visibility
for the line-producer to track.

| Check | PASS If | WARNING If |
|-------|---------|------------|
| Conservation flag | `conservation_complete: true` is set | Flag is missing or false |
| Checksum manifests | All category manifests exist under `checksums/` | Any manifest missing |
| Source archive | Git bundle exists at expected path | Bundle missing or not yet created |

**Note:** Conservation is REQUIRED for exhibition delivery (Gate 7) but is not a
blocking requirement at Stage 3. A WARNING here signals that conservation
deliverables should be prepared before exhibition promotion. See
`vfx-artist-studio/skills/finaling/conservation-package` for the full procedure.
