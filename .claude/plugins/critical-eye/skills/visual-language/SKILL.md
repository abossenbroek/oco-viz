---
name: visual-language
user-invocable: false
---

# Soot — Canonical Visual Language Reference

Shared by both agents (VFX TD and Art Director). This is the definitive aesthetic reference for oco-viz rendering.

Full specification: `plan/visual_language.yaml`

---

## What Soot Is

**Anthropocene industrial dread.** CO2 rendered as heavy, choking industrial particulate — the suffocating residue of fossil combustion. Sasol Secunda's 57 Mt/year CO2 made visible as oppressive soot against black void.

### Material References

- **Coal dust** settling on surfaces — fine, black, pervasive
- **Volcanic ash** — heavy, suffocating, geological
- **Charcoal powder** — matte, granular, smudges everything
- **Industrial fallout** — the residue that coats everything near a refinery

### Mood

Industrial. Choking. Oppressive. Smoldering. Heavy. Suffocating. Granular. Creeping. Inexorable. Dread. Ashen. Geological. Sediment. Residue.

The mood test: viewing a Soot image should feel industrial, oppressive, heavy, choking — never decorative, never comfortable, never pretty.

---

## What Soot Is NOT

- **Not a smoke simulation** — smoke is transient, wispy, ethereal. Soot is heavy, permanent, geological.
- **Not a particle system** — particles exist only at exhibition-tier edges for dissolution. The core is continuous volume.
- **Not scientific rendering** — this is not a visualization with axes, labels, or colorbars. It is a confrontation.
- **Not comfortable** — if the image feels pleasant, decorative, or beautiful for its own sake, it has failed.
- **Not colorful** — any hue is contamination. Soot is achromatic.
- **Not transparent** — opacity below 0.85, but the volume feels dense and heavy, not ghostly.

---

## Palette Rules

Strictly achromatic on black. R = G = B at every pixel (tolerance: +/- 2 levels for exhibition, +/- 5 for study).

| Name | Hex | Density Range | Character |
|------|-----|--------------|-----------|
| Background | `#000000` | — | Pure black void — the room itself |
| Trace | `#1a1a1a` | 0.0–0.1 | Barely visible wisps at periphery |
| Low | `#3d3d3d` | 0.1–0.3 | Diffuse soot haze |
| Medium | `#6b6b6b` | 0.3–0.5 | Dense particulate, structure visible |
| High | `#9e9e9e` | 0.5–0.8 | Heavy concentration, light suffocating |
| Peak | `#c8c8c8` | 0.8–1.0 | Dirty near-white — never clean, always contaminated |

**Peak is dirty near-white (`#c8c8c8`), never clean white (`#ffffff`).** The contamination is the point — even at maximum density, purity is impossible. This is combustion residue.

---

## Opacity Constraint

Opacity never reaches 1.0. Maximum 0.85 for exhibition, 0.90 for study. This guarantees:
- Volume depth is always visible — you can see into the core
- No solid walls of grey — the volume breathes
- Multiple density layers compose into rich depth

---

## Tier Hierarchy

```
sketch < study < exhibition
```

| Aspect | Sketch | Study | Exhibition |
|--------|--------|-------|-----------|
| Transfer function | Single grey | Full Soot palette | Full Soot + opacity curves |
| Lighting | None | Basic 3-point | Internal smoldering only |
| Turbulence | None | 2-3 octaves | 6-octave geological folding |
| Edge treatment | N/A | Smooth falloff | Granular particle dissolution |
| Composition | Default camera | Adjustable | Deliberate asymmetric framing |
| Post-processing | None | Fog + bloom + ACES | ACES tonemap only |
| Color | Single grey | Achromatic + slight fog tint | Strictly achromatic |

---

## The Confrontation

Soot makes the invisible visible. CO2 is normally invisible — rendering it as physical substance is an act of revelation. The viewer must feel the weight of what is normally hidden. This is not data visualization; it is data confrontation.
