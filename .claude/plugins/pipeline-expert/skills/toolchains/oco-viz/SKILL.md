---
name: toolchain-oco-viz
user-invocable: false
---

# Current Stack -- VTK / xarray / Python

The prototype rendering pipeline. Python-native, fast iteration, limited to
VTK's GPU volume mapper. Sufficient for study tier and exhibition-quality
stills. Not suitable for production deep compositing or multi-pass rendering.

---

## Rendering Engine

**VTK vtkSmartVolumeMapper / vtkGPUVolumeRayCastMapper**

| Setting | Value | Purpose |
|---------|-------|---------|
| `ShadeOff()` | Always on | Pure emission mode -- TF color IS the pixel color |
| `GlobalIlluminationReach(0.8)` | 0.8 | Internal light bleed between voxels |
| `SetMultiSamples(0)` | 0 | Pure #000000 background (fixes #020202 contamination) |
| `GradientBackgroundOff()` | Always on | Clean void even when sky disabled |
| `SetUseJittering(True)` | Always on | Breaks banding into imperceptible noise |
| `sample_distance` | grid_spacing / 10 | Exhibition quality (10m for 100m grid) |

**Post-processing:** ACES tonemap only for exhibition. No fog, no bloom.
Exposure 25.0 with boundary falloff, 4.0 without.

---

## Data Pipeline

**xarray + zarr + Pydantic v2**

- Canonical interchange: `xr.Dataset` with dims `(time, z, y, x)` and
  `"concentration"` data variable
- Config schemas: Pydantic v2 in `src/oco_viz/config/schema.py` (`AppConfig`)
- Pipeline modes: `gaussian`, `turbulent`, `composite`, `wind`, `advected`
- Config layering: `configs/base.yaml` overlaid with platform-specific YAML

---

## Volumetric Generation

| Parameter | Exhibition | Study |
|-----------|-----------|-------|
| Grid resolution | 96x96x64 min (128x128x96 for 6 octaves) | 48x48x32 min |
| fBm octaves | 4 at 96x96x64, 6 at 128x128x96 | 2-3 |
| Lacunarity | 2.0 | 2.0 |
| Gaussian smoothing sigma | 2.0 (eliminates voxelization) | 1.0 |
| Soft threshold | Quadratic below 5% cutoff | Hard cutoff acceptable |
| Boundary falloff | Raised-cosine, 15% margin | Optional |
| Z-squash | Anisotropic (dz < dx/dy) for geological folding | Isotropic |

---

## Transfer Function

| Parameter | Exhibition | Study |
|-----------|-----------|-------|
| Color control points | 14+ (linear grey #000000 to #c8c8c8) | 8+ |
| Opacity control points | 25+ (shaped S-curve) | 12+ |
| Max opacity | 0.85 | 0.90 |
| Peak luminance | #c8c8c8 (dirty near-white) | #d0d0d0 |
| Exposure (with falloff) | 25.0 | 15.0 |

---

## Limitations

- No deep compositing (single-pass only)
- No per-sample AOV output (emission, absorption, position)
- No multi-scatter volume shading (emission mode only)
- No USD scene description
- No NanoVDB GPU path
- Limited to single-machine rendering

These limitations motivate the production toolchain transition.
