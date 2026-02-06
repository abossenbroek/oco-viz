---
name: toolchain-production
user-invocable: false
---

# Target Stack -- Houdini / RenderMan / Nuke

Production VFX pipeline for exhibition-quality animation and deep compositing.
Multi-pass rendering with full AOV separation, USD scene description, and
ACES color management throughout.

---

## Houdini (20+) / Solaris

**SOPs -- Volume Manipulation**

- File SOP: Load `.vdb` from disk (pyopenvdb output)
- VDB Reshape SOP: Resample to target render grid spacing
- VDB Smooth SOP: Gaussian anti-aliasing (sigma >= 2.0 for exhibition)
- Volume VOP: Custom turbulence application via VEX
- SOP Import: Bridge from SOP context to LOPS

**LOPS / Solaris -- USD Scene Assembly**

- `UsdVol.Volume` + `UsdVol.Field` child prims for volumetric assets
- Material assignment via `UsdShade.MaterialBindingAPI`
- Camera via `UsdGeom.Camera` with lens package parameters
- Composition arcs for layered override (base -> artistic -> exhibition)
- Variants for LOD switching (viewport vs render resolution)
- Time-sampled VDB caches: `atmosphere.####.vdb`

**VEX -- Custom Operations**

- Constraint-derived turbulence using `shear_tensor` grid as anisotropy input
- Data-driven noise amplitude modulation from `data_confidence` grid
- Boundary falloff computation (raised-cosine, configurable margin)

---

## RenderMan (26+) -- PxrVolume

| Parameter | Value | Notes |
|-----------|-------|-------|
| `densityFloatPrimVar` | `"density"` | Maps to co2_density grid |
| `diffuseColor` | `[albedo, albedo, albedo]` | Achromatic -- from substance preset |
| `extinctionCoeff` | absorption coefficient | From substance-shading preset |
| `anisotropy` | Henyey-Greenstein phase (g) | Material-dependent (-0.2 to 0.2) |
| `multiScatter` | `True` | Internal light bleed (replaces VTK GIR) |
| `maxDiffuseDepth` | 4 minimum | Multiple scattering depth |

**Deep output:** DeepExr with per-sample position, density, emission.
**Sample distance:** grid_spacing / 10 for exhibition quality.

---

## Arnold (alternative) -- Standard Volume

| Parameter | Value | Notes |
|-----------|-------|-------|
| `density` | density attribute | From VDB co2_density grid |
| `scatter_color` | `[albedo, albedo, albedo]` | Achromatic |
| `scatter_anisotropy` | phase parameter (g) | Material-dependent |
| `absorption` | absorption coefficient | From substance preset |
| `volume_ray_depth` | 8+ | Multiple scattering |

---

## Nuke (15+) -- Deep Compositing

- DeepRead -> DeepMerge (front-to-back) -> DeepToImage
- Log-space grading for Contamination and Clarity controls
- ACES ODT applied at final output stage only
- Output: DPX for projection, ProRes4444 for distribution

**AOV Set (complete):** beauty, emission, absorption, residual, position, depth.

---

## OCIO / ACES

| Stage | Color Space |
|-------|------------|
| Working | ACEScg (AP1, linear) |
| Rendering | ACEScg throughout |
| Compositing | ACEScg -- no mid-chain conversions |
| Display | ACES Output Transform (Rec.709 / P3-D65) |
| Config | ACES 1.0.3+ (`aces_1.0.3` OCIO config) |
