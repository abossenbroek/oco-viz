---
name: substance-shading
user-invocable: false
---

> **Phase status:** VTK emission mode parameters are **active** and tested. MaterialX `standard_volume` and PxrVolume mappings are **aspirational** -- they document target shader configurations for the Karma XPU pipeline (Wave 13).

# Substance Shading -- Material Conviction Presets

Material presets that map artistic intent to shader configuration. The bridge
between what the Sculptor demands and what the renderer delivers.

---

## Core Principle

**Low scattering albedo.** Soot is light-swallowing, not light-scattering. The
substance absorbs. When light enters the volume, it dies. Any visible
luminance comes from emission (TF color in VTK's `ShadeOff()` mode), not from
scattered illumination.

This is the fundamental departure from smoke, cloud, and atmospheric haze
rendering. Those materials scatter light. Soot devours it.

---

## Material Presets

### Coal Dust

Dry, matte, granular. The dominant Soot material. Near-zero scatter -- light
enters and does not return. Fresh surfaces have faint vitreous luster;
weathered surfaces are matte-dull. Conchoidal fracture patterns at macro scale.

| Property | Value | Notes |
|----------|-------|-------|
| Albedo | 0.05 | Near-black body |
| Scatter | 0.02 | Negligible forward scatter |
| Absorption | 0.95 | Light dies in the substance |
| Phase (g) | -0.1 | Slight back-scatter for micro-facet glint |

### Volcanic Ash

Heavy, clumped, aggressive. Pyroclastic particles suspended and settling.
Clump density varies -- dense cores with filamentary edges. Slightly
forward-scattering at boundaries where particles thin.

| Property | Value | Notes |
|----------|-------|-------|
| Albedo | 0.12 | Mineral reflectance |
| Scatter | 0.08 | Forward scatter at edges |
| Absorption | 0.88 | Absorption-dominant |
| Phase (g) | 0.2 | Mild forward scattering |

### Charcoal

Granular, smudgy, friable. The Kentridge material -- hand-pressed charcoal on
paper. Smudge zones with soft boundaries, granular texture with visible stroke
directionality. The material IS the subject.

| Property | Value | Notes |
|----------|-------|-------|
| Albedo | 0.08 | Dark matte |
| Scatter | 0.04 | Isotropic, diffuse |
| Absorption | 0.92 | Strong absorption |
| Phase (g) | 0.0 | Isotropic -- no directional preference |

### Industrial Soot

Oily, sticky, iridescent-black. The residue that coats every surface near a
refinery. Back-scatter shimmer at oblique viewing angles produces a faint
oil-slick quality. The most absorption-dominant preset.

| Property | Value | Notes |
|----------|-------|-------|
| Albedo | 0.03 | Nearly complete absorption |
| Scatter | 0.01 | Minimal |
| Absorption | 0.97 | Maximum absorption |
| Phase (g) | -0.2 | Back-scatter shimmer |

### Geological Carbon

Dense, compressed, mineral. Carbon compressed by geological time -- coal seam
weight, sedimentary banding, mineral quality. Forward scatter from crystalline
micro-structure.

| Property | Value | Notes |
|----------|-------|-------|
| Albedo | 0.10 | Mineral reflectance |
| Scatter | 0.06 | Mild forward |
| Absorption | 0.90 | Absorption-dominant |
| Phase (g) | 0.1 | Slight forward scatter |

---

## Production Renderer Mapping

### VTK (current pipeline)

VTK operates in emission mode. Scattering parameters do not apply directly --
the transfer function color IS the rendered color.

| VTK Setting | Purpose | Value |
|-------------|---------|-------|
| `ShadeOff()` | Pure emission mode -- TF color = pixel color | Always on |
| `GlobalIlluminationReach(0.8)` | Internal light bleed between voxels | 0.8 |
| `SetUseJittering(True)` | Noise dither to break banding | Always on |
| `SetMultiSamples(0)` | Pure #000000 background (fixes #020202) | 0 |
| `GradientBackgroundOff()` | Clean void even with sky disabled | Always on |
| `sample_distance` | grid_spacing / 10 for exhibition quality | e.g. 10m for 100m grid |

Material conviction in VTK is achieved through the transfer function opacity
curve (see density-to-dread) and volume structure (noise, smoothing,
boundary falloff), not through shader scattering parameters.

### PxrVolume (RenderMan target)

| PxrVolume Parameter | Mapping |
|---------------------|---------|
| `densityFloatPrimVar` | "density" |
| `diffuseColor` | [albedo, albedo, albedo] |
| `extinctionCoeff` | absorption coefficient |
| `anisotropy` | Henyey-Greenstein phase (g) |
| `multiScatter` | True for internal bleed |
| `maxDiffuseDepth` | 4 minimum |

### MaterialX `standard_volume` (Karma XPU — primary production renderer)

The production renderer per RFC Decision 10. MaterialX provides renderer-agnostic
material definitions consumed by Karma XPU.

| MaterialX Parameter | Mapping | Notes |
|---------------------|---------|-------|
| `absorption_color` | [1-albedo, 1-albedo, 1-albedo] | Achromatic; high absorption for soot |
| `scattering_color` | [albedo, albedo, albedo] | Low scatter albedo (0.03-0.12) |
| `scattering_anisotropy` | phase parameter (g) | Exhibition: 0.8 forward scatter for ghost light |
| `emission_color` | TF-mapped density→grey | Self-illumination from transfer function |
| `emission_weight` | density-dependent | Dense core emits more; sparse periphery dim |

**Karma XPU settings:**
- Volume step size: `grid_spacing / 10` for exhibition quality
- SPP tiers: Scout 64, Preview 256, Final 1024+
- OIDN denoiser enabled; NoisyBeauty AOV preserved for grain restoration

#### Soot Crust — Dual-State Shader Concept

Exhibition tier uses a gradient-driven split between absorption and scattering
behavior. The density gradient magnitude (`|∇density|`) determines material state:

| Gradient | Region | Material State | Visual Effect |
|----------|--------|----------------|---------------|
| Steep (`|∇density|` high) | Edges, boundary | **Crust**: matte black, high absorption | Hard silhouette, charcoal-like edge |
| Shallow (`|∇density|` low) | Interior, core | **Smoke**: translucent grey, mild scatter | Depth-readable interior, internal glow |

Implementation in MaterialX:
- `crust_weight = clamp(|∇density| / grad_max, 0, 1)`
- `absorption_color = lerp(interior_absorption, crust_absorption, crust_weight)`
- `scattering_color = lerp(interior_scatter, near_zero, crust_weight)`

This creates volumes that have a matte, charcoal-like crust with translucent,
glowing interiors — solving the "Floating Cotton Ball" problem where volumes
read as featureless blobs.

### Arnold Standard Volume (alternative target)

| Arnold Parameter | Mapping |
|------------------|---------|
| `density` | density attribute |
| `scatter_color` | [albedo, albedo, albedo] |
| `scatter_anisotropy` | phase parameter (g) |
| `absorption` | absorption coefficient |
| `volume_ray_depth` | 8+ for multiple scattering |

---

## Validation Checklist

When evaluating material conviction:

- [ ] Albedo + absorption roughly sum to 1.0
- [ ] Scattering albedo below 0.15 (Soot absorbs, not scatters)
- [ ] Phase function appropriate for material (back-scatter for metallic sheen, isotropic for matte)
- [ ] VTK emission mode parameters correct (`ShadeOff()`, jittering, multi-samples)
- [ ] Material reads as physical substance, not digital effect
