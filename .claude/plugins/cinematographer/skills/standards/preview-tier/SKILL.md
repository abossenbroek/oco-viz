---
name: preview-tier
user-invocable: false
type: standard
primary_owner: shared
---

# Preview Tier Standard

Defines the parameters for preview-tier production. Preview tier validates
lighting, materials, transfer functions, and the ACES color pipeline at
near-production fidelity. This is where creative decisions are locked
before committing to final-tier render costs.

---

## Principle

Preview tier answers the question: "Is this the right execution?" Creative
direction was approved at scout tier; now the execution quality must be
validated. Lighting must be motivated. Materials must be physically plausible.
The ACES pipeline must be active. A preview render should look like a
slightly noisier, slightly lower-resolution version of the final.

---

## Technical Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| VDB resolution | 512^3 | Detail sufficient for material and lighting evaluation |
| Render resolution | 2K DCI (2048 x 1080) | Industry standard intermediate format |
| Samples per pixel | 256 spp | Low noise, suitable for lighting judgment |
| Frame rate | 24 fps | Match delivery frame rate |
| Color space | ACEScg (working), ACES output | Full ACES pipeline active |
| Output format | EXR (half-float, multi-layer) | Beauty + key AOVs |
| Bit depth | 16-bit half-float minimum | Full dynamic range preserved |

---

## Required Capabilities

The following MUST be active at preview tier (not acceptable shortcuts):

| Area | Requirement | Validation |
|------|------------|------------|
| Motivated lighting | Every light has a narrative/physical justification | Lighting rig `motivation` field non-empty |
| Material presets | Visual bible material_presets applied | VDB shader params match bible |
| ACES pipeline | Full OCIO config loaded and active | `Config.CreateFromFile()` succeeds |
| Transfer functions | Production TF curves active | >= 14 color + >= 25 opacity control points |
| Show LUT | Applied but with bypass available | LUT path in grading_delivery |
| Post-processing | Bloom, fog, exposure active | Post-process config non-empty |
| Camera easing | Production easing curves | Matches storyboard easing field |

---

## Quality Thresholds

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Noise floor | No visible noise at 100% zoom in smooth regions | Visual inspection of gradient areas |
| Banding | None visible in smooth gradients | Jittering enabled, 256+ spp |
| Background | Pure black (#000000) or intended environment | Corner pixel measurement |
| Volume detail | Wispy edges and density gradients visible | No hard clipping on plume boundary |
| Lighting depth | Directional shadows and volume shading | Light direction readable from volume |
| Color accuracy | Neutral gray maps to neutral gray through pipeline | CDL achromatic compliance test |
| TF quality | Smooth opacity ramp, no contouring | TF curve inspection |
| Max opacity | <= 0.90 | TF opacity maximum check |
| Dynamic range | >= 10 stops measured | EXR value range inspection |

---

## Approval Gate

Preview tier requires:

| Agent | Role | What They Evaluate |
|-------|------|--------------------|
| critical-eye (VFX review) | Primary | Visual quality per CLAUDE.md section 5.3 criteria |
| dp | Secondary | Lighting execution, camera execution |
| colorist | Secondary | Color pipeline, grading, achromatic compliance |
| groundtruth | Validation | Physical accuracy of density, temperature, units |

Preview tier also requires governance approval:
- dp lighting rig approved by Auteur (via governance-bridge)
- Colorist grading approved by Tonalist (via governance-bridge)

---

## Deliverables

A complete preview-tier delivery includes:

1. **Rendered frames**: Multi-layer EXR sequence at 2K DCI
2. **collaboration YAML**: `shot_execution_delivery` with full render stats
3. **Lighting rig**: `lighting_rig_delivery` with all light motivations
4. **Grading config**: `grading_delivery` with show LUT and CDL
5. **Validation report**: `validation_report` from groundtruth
6. **Critical-eye review**: Visual quality verdict

---

## AOV Requirements

Preview tier must render these AOVs:

| AOV | Purpose | Format |
|-----|---------|--------|
| beauty | Final composited image | RGB half-float |
| emission | Self-illumination contribution | RGB half-float |
| density | Volume density at each pixel | single-channel half-float |
| depth | Camera-space Z depth | single-channel float |

Additional AOVs (absorption, residual) are optional at preview but
recommended if the render cost is marginal.

---

## Progression to Final

Preview tier is approved when:
- Critical-eye VFX review passes (no visual quality failures)
- Groundtruth physical validation passes
- Governance approvals obtained (Auteur for lighting, Tonalist for grading)
- No creative direction changes pending

Once approved, the dp may proceed to final-tier rendering. Creative
direction and technical approach are locked at this point.

---

## Anti-Patterns

- **Scout-quality lighting at preview**: Using single key + ambient when motivated lighting is required. Preview demands narrative justification for every light.
- **Missing ACES pipeline**: Rendering in sRGB or unmanaged color at preview tier. The full OCIO pipeline must be active.
- **Skipping critical-eye review**: Self-approving visual quality without dedicated visual inspection. The bias-free review is mandatory.
- **Resolution inflation**: Rendering at 4K to "get ahead". Preview is 2K DCI; final-tier resolution is a separate decision point.
- **Grading without show LUT**: Evaluating color without the show LUT applied. The LUT is part of the creative intent.

---

## Validation Checklist

- [ ] VDB resolution is 512^3
- [ ] Render resolution is 2048 x 1080 (2K DCI)
- [ ] Samples per pixel is 256
- [ ] ACES pipeline active (ACEScg working space confirmed)
- [ ] All lights have motivation field populated
- [ ] Material presets match visual bible
- [ ] Transfer function has >= 14 color + >= 25 opacity control points
- [ ] Show LUT applied via OCIO config
- [ ] Post-processing active (bloom, fog, exposure)
- [ ] No visible noise at 100% zoom
- [ ] No banding in smooth gradients
- [ ] Background is pure black or intended environment
- [ ] Achromatic compliance verified (CDL neutral test)
- [ ] Dynamic range >= 10 stops
- [ ] Max opacity <= 0.90
- [ ] Required AOVs present (beauty, emission, density, depth)
- [ ] Critical-eye review obtained
- [ ] Groundtruth validation passed
- [ ] Governance approvals obtained
