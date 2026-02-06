---
name: asset-integrity
user-invocable: false
---

# Asset Integrity -- Stage 3: Conversion Gate

Conversion fidelity from scientific data to renderable assets. No silent
data loss, no metadata gaps, no axis reorder errors.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Metadata preservation | Voxel size, origin, data range, timestamp all present | Metadata field check at each pipeline stage |
| Value range | min/max within 1% of source | Statistical comparison: source vs converted |
| Grid type correctness | FloatGrid for scalar, Vec3fGrid for vector | VDB grid header inspection |
| Multi-grid completeness | All 5 layers present (co2, wind, temp, pressure, confidence) | Grid listing in output VDB |
| Format validity | `.vdb` readable by Houdini File SOP | Import test in Houdini (or pyopenvdb round-trip) |
| Voxel size consistency | All grids share same voxel size and transform | Transform comparison across grids |
| Axis reorder | VTK x-fastest to numpy z-fastest correct | Asymmetric feature verification (no rotation/mirror) |
| Float precision | float32 maintained through conversion | dtype check at each stage |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | All metadata preserved. Value ranges match source within 1%. Correct grid types. All 5 layers present. VDB imports cleanly. Consistent transforms. Axis reorder verified. |
| CONCERN | Metadata present but incomplete (missing one non-critical field). Value range within 2%. Grid types correct. 4 of 5 layers present (non-critical layer missing). |
| FAIL | Metadata silently dropped. Value range diverges > 2%. Wrong grid type (scalar as Vec3f or vice versa). Axis reorder incorrect (rotated volume). VDB fails to import. |

---

## Agent Responsibility

Primary: Alchemist
