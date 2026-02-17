---
name: final-tier
user-invocable: false
type: standard
primary_owner: shared
---

# Final Tier Standard

Defines the parameters for final-tier (exhibition) production. Final tier
is the delivery format for gallery exhibition, publication, and archival.
Every technical and artistic decision has been validated at preview tier;
final tier maximizes fidelity with no creative surprises.

---

## Principle

Final tier answers the question: "Is this exhibition-ready?" There should
be zero creative unknowns at this stage. The preview-tier creative direction,
lighting, materials, and grading are locked. Final tier adds resolution,
sample depth, deep compositing readiness, and the full AOV complement.
If final tier reveals a creative problem, it means preview tier failed.

---

## Technical Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| VDB resolution | 1024^3 | Maximum detail for exhibition output |
| Render resolution | 4K DCI (4096 x 2160) | Exhibition projection standard |
| Samples per pixel | 1024+ spp | Noise-free at 100% zoom on 4K display |
| Frame rate | 24 fps | Match delivery frame rate |
| Color space | ACEScg (working), ACES output | Full ACES 1.3+ pipeline |
| Output format | EXR (full-float, multi-layer, deep) | Maximum precision and compositing readiness |
| Bit depth | 32-bit float | Full dynamic range, no quantization |
| Dynamic range | >= 14 stops | Exhibition-grade latitude |

---

## Required Capabilities

Everything required at preview tier, PLUS:

| Area | Requirement | Validation |
|------|------------|------------|
| Deep compositing | Per-sample position + density | Deep EXR file inspection |
| Full AOV set | All AOVs rendered (see table below) | Layer count verification |
| 32-bit precision | Full float, not half-float | EXR bit depth inspection |
| >= 14 stops DR | Measured dynamic range | EXR value range analysis |
| Grain/texture | Subtle film grain or procedural texture applied | Visual inspection |
| Sparse VDB | Exact 0.0 in empty regions | Non-zero voxel ratio check |
| Grid naming | "density", "vel", "temperature" | OpenVDB grid name inspection |

---

## Quality Thresholds

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Noise | Zero visible noise at 100% zoom on 4K display | Pixel-level inspection of smooth gradients |
| Banding | Zero banding in any region | 32-bit precision + jittering eliminates quantization |
| Background purity | #000000 exactly | Corner pixel measurement (all four corners) |
| Volume edges | Wispy halo visible, no hard clip | Plume boundary inspection |
| Lighting depth | Full volumetric scattering, directional shadows | Light direction + shadow verification |
| Color accuracy | Achromatic compliance verified | CDL neutral gray test |
| TF quality | Smooth curves, no contouring, >= 14 color + >= 25 opacity points | TF curve analysis |
| Max opacity | <= 0.85 | TF opacity maximum (stricter than preview) |
| Dynamic range | >= 14 stops | EXR histogram analysis |
| Deep validity | Per-sample position + density correct | Deep file sample inspection |
| Physical accuracy | Units in meters, Kelvin, m/s | Grid metadata and value range checks |
| Sparse efficiency | Empty regions are exact 0.0 | Voxel occupancy ratio |
| Frame projection test | Would hold up projected on gallery wall at 4K | Simulated 4K display inspection |

---

## Full AOV Set

Final tier must render ALL of these AOVs:

| AOV | Purpose | Format | Required |
|-----|---------|--------|----------|
| beauty | Final composited image | RGB float | Yes |
| emission | Self-illumination contribution | RGB float | Yes |
| absorption | Volume absorption contribution | RGB float | Yes |
| residual | Unaccounted light contribution | RGB float | Yes |
| density | Volume density per pixel | single-channel float | Yes |
| depth | Camera-space Z depth | single-channel float | Yes |
| position | World-space position | RGB float | Yes |
| normal | Surface/volume normal | RGB float | Yes (if applicable) |
| velocity | Motion vectors | RGB float | Yes (animated sequences) |

---

## Approval Gate

Final tier requires the full dual-agent critical-eye review:

| Agent | Role | What They Evaluate |
|-------|------|--------------------|
| critical-eye (dual review) | Primary | Full visual quality per CLAUDE.md 5.3 — both agents must pass |
| dp | Secondary | Technical render quality, lighting fidelity |
| colorist | Secondary | Final grade, achromatic compliance, show LUT |
| groundtruth | Validation | Physical accuracy, unit verification, constraint check |
| production-designer | Verification | Material preset fidelity against visual bible |

Final tier governance requires:
- Auteur approval of rendered frames (creative direction)
- Alchemist approval of technical render quality
- Tonalist approval of final color pipeline
- Sculptor approval of material fidelity
- Spectralist approval of physical validation

A single FAIL from any reviewer blocks exhibition delivery.

---

## Deliverables

A complete final-tier delivery includes:

1. **Rendered frames**: Deep multi-layer EXR at 4K DCI, 32-bit float
2. **collaboration YAML**: `shot_execution_delivery` with complete render stats
3. **Lighting rig**: Final `lighting_rig_delivery`
4. **Grading config**: Final `grading_delivery` with locked show LUT
5. **Validation report**: Comprehensive `validation_report` from groundtruth
6. **Visual bible**: Final `visual_bible_delivery` with >= 12 keyframes
7. **Critical-eye dual review**: Both agents pass
8. **All governance approvals**: Cross-plugin requests with PASS verdicts

---

## Exhibition Readiness Criteria

The ultimate test for final tier is the gallery wall test:

> Would this frame, projected at native 4K resolution on a gallery wall,
> hold up under sustained scrutiny from a knowledgeable audience?

Specific sub-criteria:
- Does the plume have visible edges and a wispy halo, not a hard blob?
- Is there directional depth from lighting, not a flat lifeless volume?
- Is cross-tier coherence maintained (same structure, different mood)?
- Do bloom, fog, exposure, and tonemapping contribute to the intended look?
- Do camera paths and easing produce smooth, intentional motion?
- Is the dynamic range sufficient for the projected environment?
- Would a Pixar/Disney lighting TD approve this as a final shot?

---

## Anti-Patterns

- **Creative changes at final**: Discovering a creative problem that should have been caught at preview. Final tier renders locked creative direction only.
- **Half-float at final**: Using 16-bit half-float instead of 32-bit float. Exhibition demands maximum precision.
- **Missing deep data**: Rendering without deep compositing. Final tier requires per-sample data for downstream Nuke compositing.
- **Incomplete AOVs**: Rendering beauty-only at final tier. All AOVs in the table above are mandatory.
- **Opacity too high**: Max opacity exceeding 0.85 at final tier (limit is stricter than preview's 0.90). High opacity produces hard-edged, unnatural volumes.
- **Single reviewer**: Relying on one critical-eye pass instead of the required dual review. Exhibition quality demands independent confirmation.
- **Skipped governance**: Proceeding to exhibition without all pipeline-expert approvals. Every approval in the gate list is mandatory.

---

## Validation Checklist

- [ ] VDB resolution is 1024^3
- [ ] Render resolution is 4096 x 2160 (4K DCI)
- [ ] Samples per pixel is 1024+
- [ ] Output format is EXR 32-bit float with deep data
- [ ] Dynamic range >= 14 stops measured
- [ ] ACES 1.3+ pipeline fully active
- [ ] All required AOVs present (beauty, emission, absorption, residual, density, depth, position, normal, velocity)
- [ ] Deep compositing data valid (per-sample position + density)
- [ ] Zero noise at 100% zoom on 4K
- [ ] Zero banding anywhere
- [ ] Background exactly #000000 (all four corners)
- [ ] Volume edges wispy, not hard-clipped
- [ ] Max opacity <= 0.85
- [ ] TF >= 14 color + >= 25 opacity control points
- [ ] Achromatic compliance verified
- [ ] Physical units correct (meters, Kelvin, m/s)
- [ ] Sparse VDB (exact 0.0 in empty regions)
- [ ] Grid names correct ("density", "vel", "temperature")
- [ ] Film grain or procedural texture applied
- [ ] Visual bible keyframe count >= 12
- [ ] Dual critical-eye review passed
- [ ] All governance approvals obtained
- [ ] Gallery wall test: frame holds up at native 4K projection
