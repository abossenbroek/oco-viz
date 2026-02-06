---
name: toolchain-bridge
user-invocable: false
---

# Handoff -- VTK to Production via VDB + USD

The bridge between prototype (VTK/Python) and production (Houdini/RenderMan).
OpenVDB as the interchange format, USD as the unifying scene description.

---

## VTK to Houdini Handoff

```
vtkImageData -> numpy (axis reorder z,y,x) -> pyopenvdb FloatGrid -> .vdb
```

**Axis reorder is critical:** VTK is x-fastest, numpy/OpenVDB is z-fastest.
Incorrect reorder produces rotated or mirrored volumes.

**Metadata preservation at handoff:**

| Field | Source | Required |
|-------|--------|----------|
| `voxel_size` | `vtkImageData.GetSpacing()` | Yes |
| `world_origin` | `vtkImageData.GetOrigin()` | Yes |
| `data_range` | `min/max` of array | Yes |
| `timestamp` | Pipeline config (ISO 8601) | Yes |
| `source` | `"oco-viz"` attribution | Yes |

**Multi-grid VDB output:**

| Grid | Type | Content |
|------|------|---------|
| `co2_density` | FloatGrid | Normalized XCO2 field (0-1) |
| `wind_velocity` | Vec3fGrid | u, v, w components (m/s) |
| `temperature` | FloatGrid | Air temperature (K) |
| `pressure` | FloatGrid | Atmospheric pressure (Pa) |
| `data_confidence` | FloatGrid | Assimilation confidence (0-1) |

All grids share the same `voxelSize` and `worldOrigin` via
`pyopenvdb.createLinearTransform`.

---

## USD as Unifying Scene Description

**Volume prims:**
- `UsdVol.Volume` top-level container
- `UsdVol.Field` child prims (one per VDB grid channel)
- Field asset path via `SdfAssetPath` referencing `.vdb` files

**Material binding:**
- `UsdShade.Material` with renderer-specific shader (PxrVolume / Arnold)
- Bound via `UsdShade.MaterialBindingAPI`

**Camera:**
- `UsdGeom.Camera` with focal length, aperture, clipping planes
- Animated via time-sampled transforms

**Composition arcs for layered override:**

| Layer | Purpose |
|-------|---------|
| Base | Data-driven volume + default material |
| Artistic | Sculptor/Tonalist overrides (TF, noise, exposure) |
| Exhibition | Installer overrides (resolution, frame-edge, projection) |

Layers compose non-destructively. Artistic intent preserved while allowing
per-exhibition customization.

---

## Real-Time Lookdev

**NanoVDB for GPU-accelerated preview:**
- Convert OpenVDB -> NanoVDB for GPU traversal
- Grid class: `nanovdb::GridClass::FogVolume` for density fields
- Supports CUDA, OptiX, Vulkan, GLSL

**Target platforms:**
- Unreal Engine for interactive walkthrough
- TouchDesigner for real-time installation preview

**Constraints:**
- NOT for final render -- lookdev quality only
- May quantize values (verify range preservation)
- Useful for Installer's gallery pre-visualization
- Interactive frame rates enable spatial composition testing from
  multiple viewer positions within the viewing cone
