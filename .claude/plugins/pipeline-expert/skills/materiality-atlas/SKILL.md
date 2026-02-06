---
name: materiality-atlas
user-invocable: false
---

# Materiality Atlas -- Physical Reference Library

Physical reference mapping for material conviction assessment. Each entry maps
real-world visual and tactile qualities to procedural parameters. The Sculptor
uses this atlas to evaluate whether digital substance achieves physical truth.

---

## Reference Materials

### 1. Coal Seam Face

Exposed bituminous coal in a working mine. Conchoidal fracture surfaces with
vitreous luster on fresh breaks, matte-dull on weathered surfaces. Layered
sedimentary banding from millions of years of compression. The material
carries geological time in its structure.

**Maps to:**
- Anisotropic Z-squash (dz < dx/dy) for sedimentary banding
- Banding frequency from noise field layering
- Low albedo (0.05) with micro-facet variation at fracture surfaces
- Gaussian smoothing sigma 2.0 to eliminate voxelization while preserving layered structure

### 2. Volcanic Tephra (Fine Ash)

Airborne pyroclastic particles <2mm diameter. Suspended, clumped, with a
settling hierarchy -- larger fragments fall first, fine ash lingers. Particles
are individually visible at boundaries where concentration thins. Clumps
form and break apart in shear layers.

**Maps to:**
- Particle dissolution system at volume edges
- Size distribution 0.5-2mm equivalent in procedural noise
- Gravity settling implied through vertical density gradient
- Clumping factor in noise field (Worley-type cellular structure)
- Forward scattering (g = 0.2) at boundary where particles thin

### 3. Kentridge Charcoal on Paper

Hand-pressed charcoal. Smudge zones with soft, directional boundaries.
Granular texture with visible stroke marks -- the material process is part
of the subject. The charcoal IS the medium AND the message. Weight comes
from the hand that pressed it.

**Maps to:**
- High Grit (density-to-dread axis)
- Gaussian smoothing sigma 1.0-1.5 (not fully smooth -- preserves grain)
- Directionality in noise field (anisotropic noise stretching)
- Isotropic scatter (g = 0.0) for matte, non-directional surface quality
- Smudge zones: gradual density transitions with micro-variation

### 4. Electron Microscope: PM2.5 Particulate Matter

Spherical and agglomerated chain-aggregate structures at the microscopic
scale. Fractal geometry with self-similarity across magnification levels.
Individual particles are spheroids; aggregates form branching chains and
clusters.

**Maps to:**
- High-frequency noise octaves (5-6) for fractal detail
- Lacunarity 2.0+ for self-similar scaling
- Micro-clumping through secondary noise modulation
- 4 octaves with lacunarity 2.0 adequate at 96x96x64 grid; 6 octaves need larger grid

### 5. Industrial Smokestack Plume

Source-proximal: dense, laminar core with sharp density boundary.
Downwind: turbulent breakup through Kelvin-Helmholtz instability, atmospheric
entrainment, visible shear layers at wind boundaries. The transition from
laminar to turbulent is the signature of real plume dynamics.

**Maps to:**
- Data-driven turbulence constrained by wind field
- Core-to-edge density gradient (dense interior, filamentary edges)
- Boundary falloff (raised-cosine, 15% margin) to eliminate VTK bounding box
- Shear layer noise aligned with wind direction vectors
- Entrainment: background air mixing into plume at boundaries

---

## Assessment Criteria

When evaluating material conviction, apply these physical truth tests:

| Test | Question | Failure Mode |
|------|----------|-------------|
| **Residue** | Does it look like it would leave residue on your hand? | Reads as clean, digital, untouchable |
| **Weight** | Is there visible weight in its form and motion? | Floats, drifts, has no mass |
| **Texture** | Can you imagine the texture on your fingertips? | Smooth, glassy, featureless |
| **Scale** | Is there granularity at multiple scales? | Single-scale reads as procedural |
| **Absorption** | Does light die in it? | Light illuminates it (scattering-dominant = cloud, not soot) |
| **Settling** | Does it look like it would settle, not disperse? | Dissolves upward like smoke |
| **History** | Does it feel like it accumulated over time? | Looks instantaneous, generated |

---

## Anti-References

Materials that Soot must NEVER resemble:

- **Cumulus clouds** -- bright, white, light-scattering. The opposite of absorption-dominant.
- **Fog / mist** -- uniform, structureless, atmospheric. Too gentle, too natural.
- **CG smoke** -- wispy, transient, ethereal. No weight, no permanence.
- **Nebulae** -- colorful, cosmic, beautiful. Decorative spectacle.
- **Ink in water** -- fluid, graceful, diffusing. Too elegant, too clean.
