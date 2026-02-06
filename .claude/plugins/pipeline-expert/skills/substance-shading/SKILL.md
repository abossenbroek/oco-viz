---
name: substance-shading
user-invocable: false
---

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
