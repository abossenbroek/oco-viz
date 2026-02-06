---
name: materiality
user-invocable: false
---

# Materiality -- Physical Conviction Gate

Does the substance feel physical? The viewer must believe the volume has mass,
texture, and would leave residue on contact. Digital smoothness is failure.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Absorption dominance | Albedo < 0.15 | Shader parameter check |
| Multi-scale granularity | >= 3 visible noise octaves | Visual inspection at macro/meso/micro |
| Weight in motion | Heavy ease-in, settling behavior | Temporal analysis of animation curves |
| Texture variation | No uniform density regions > 10% of volume | Histogram analysis of density field |
| Edge dissolution | Continuous -> clumped -> particle (exhibition) | Visual inspection of boundary zones |
| Residue quality | "Would leave residue on your hand" | Subjective material assessment |
| Depth reading | Interior structure visible through layers | Semi-transparency depth test |
| Smoothing quality | No voxelization artifacts visible | Gaussian sigma >= 2.0 verified |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | Substance reads as physical matter at all scales. Material reference (coal dust, volcanic ash, charcoal) identifiable. Edge dissolution and weight present. |
| CONCERN | Material direction correct but conviction incomplete. Missing one scale of granularity, or edges slightly too smooth. Weight present but not overwhelming. |
| FAIL | Substance reads as digital effect. Smooth blob, uniform density, no physical reference. No edge dissolution. Floats rather than presses. |

---

## Agent Responsibility

Primary: Sculptor
Secondary: Auteur (artistic conviction sign-off)
