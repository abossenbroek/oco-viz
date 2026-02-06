---
name: chromatic-mood
user-invocable: false
---

# Chromatic Mood -- Achromatic Discipline Gate

Achromatic severity enforcement. R = G = B is the concept, not a constraint.
Any channel divergence is contamination. Grey is grey -- not warm, not cool.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Channel divergence | R=G=B +/-2 (exhibition), +/-5 (study) | Pixel measurement at 5 density levels |
| Background purity | #000000 (exhibition), <= #0f0f0f (study) | Corner pixel sampling (all 4 corners) |
| Peak luminance | <= #c8c8c8 (dirty near-white, never clean) | Max pixel value in plume region |
| Color temperature | Neutral (no warm/cool cast) | CIE xy neutral axis check (x=0.3127, y=0.3290) |
| Fog contamination | None (exhibition), <= 5-level drift (study) | Channel divergence measurement in haze regions |
| Greyscale range | Minimum 6 distinguishable luminance zones | Histogram analysis (trace through peak) |
| Post-process chain | ACES ODT does not introduce chromatic shift | Before/after channel comparison |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | All pixels satisfy channel divergence threshold. Background pure black. Peak at dirty near-white. No color temperature shift through compositing chain. |
| CONCERN | Minor divergence (within +/-5 at exhibition, within +/-8 at study). Background near-black but not pure. Peak luminance slightly high but below #d0d0d0. |
| FAIL | Visible color cast in plume or void. Background colored. Peak at clean white (#ffffff). Warm or cool tint from lighting or post-processing. |

---

## Agent Responsibility

Primary: Tonalist
Secondary: Auteur (chromatic discipline sign-off)
