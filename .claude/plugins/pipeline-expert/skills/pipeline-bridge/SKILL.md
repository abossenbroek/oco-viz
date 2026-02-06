---
name: pipeline-bridge
user-invocable: false
---

# Pipeline Bridge -- VTK to VDB to Houdini to RenderMan

The complete conversion pipeline from prototype (VTK/Python) to production
(Houdini/RenderMan/Nuke). The Alchemist uses this skill to validate
conversion fidelity, metadata preservation, and dependency correctness
at every stage.

---

## Pipeline Stages

```
vtkImageData (Python)
    -> numpy.ndarray (float32/float64)
        -> pyopenvdb.FloatGrid / Vec3fGrid
            -> .vdb file on disk
                -> Houdini SOP (File SOP -> VDB Reshape -> VDB Smooth)
                    -> Solaris/LOPS (UsdVol)
                        -> RenderMan PxrVolume / Arnold Standard Volume
                            -> Deep EXR -> Nuke deep compositing
```

---

## Stage 1: VTK to numpy

```python
from vtk.util.numpy_support import vtk_to_numpy

image_data = vtk.vtkImageData()
scalars = vtk_to_numpy(image_data.GetPointData().GetScalars())
dims = image_data.GetDimensions()
# CRITICAL: VTK is x-fastest, numpy is z-fastest (C-order)
array_3d = scalars.reshape(dims[2], dims[1], dims[0])
```

**Validation**: Axis reorder must be `(z, y, x)` -- incorrect reorder produces
rotated or mirrored volumes. Verify by checking known asymmetric features.

---

## Stage 2: numpy to OpenVDB

```python
import pyopenvdb as vdb

grid = vdb.FloatGrid()
grid.copyFromArray(array_3d.astype(np.float32))
grid.transform = vdb.createLinearTransform(voxelSize=voxel_size)
grid.name = "co2_density"
grid.metadata = {
    "source": "oco-viz",
    "voxel_size": str(voxel_size),
    "world_origin": str(origin),
    "data_range": f"{array_3d.min():.6f},{array_3d.max():.6f}",
    "timestamp": iso_timestamp,
}
vdb.write("output.vdb", grids=[density_grid, wind_grid, confidence_grid])
```

**Grid types**: `FloatGrid` for scalar fields (density, temperature, pressure, confidence).
`Vec3fGrid` for vector fields (wind velocity). Grid names must follow the convention
defined in `atmospheric-state` skill.

**Sparsity**: The `tolerance` argument in `copyFromArray` controls which voxels are
stored vs pruned. For atmospheric data with smooth gradients, use tight tolerance
to preserve detail.

---

## Stage 3: VDB to Houdini

- **File SOP**: Load `.vdb` from disk. Reference by path for cache invalidation.
- **VDB Reshape SOP**: Resample to target resolution if grid spacing differs from render grid.
- **VDB Smooth SOP**: Anti-aliasing pass. Gaussian sigma >= 2.0 for exhibition quality.
- **Custom VEX**: Apply constraint-derived turbulence using `shear_tensor` grid as anisotropy input.
- **SOP Import**: Bridge from SOP context to LOPS for USD scene assembly.

---

## Stage 4: Houdini to USD

- **UsdVolVolume** prim: Top-level volume container
- **UsdVolField** child prims: One per VDB grid channel (density, velocity, confidence)
- Field asset path: `@output.vdb@` via `SdfAssetPath`
- Volume purpose: `render`
- Material binding: `PxrVolume` or `ArnoldStandardVolume`
- Variants for LOD switching (viewport vs render resolution)
- Time-sampled caches: `atmosphere.####.vdb` for animated sequences

---

## Stage 5: RenderMan Render

- **PxrVolume shader**: Extinction and albedo from substance-shading presets
- Deep output: DeepExr with per-sample position, density, emission
- **AOV set**: beauty, emission, absorption, residual, position, depth
- Sample distance: grid_spacing / 10 for exhibition quality
- Volume step multiplier tuned per shot for noise/speed tradeoff

---

## Stage 6: Nuke Deep Compositing

- DeepRead -> DeepMerge (front-to-back) -> DeepToImage
- Log-space grading for "Contamination" and "Clarity" looks
- ACES ODT applied at final stage only (not in intermediate grades)
- Output: DPX for projection, ProRes4444 for distribution

---

## Metadata Preservation Checklist

At EVERY stage, verify:

- [ ] Voxel size preserved or correctly resampled (document resampling ratio)
- [ ] World-space origin maintained (coordinate system consistent)
- [ ] Data range documented (min/max values at each stage)
- [ ] Source attribution present (original satellite product, processing date)
- [ ] Timestamp carried through (ISO 8601 format)
- [ ] Grid names follow convention (co2_density, wind_velocity, etc.)
- [ ] CRS information preserved or correctly transformed

A missing metadata field at any stage is a CONCERN. Silently dropped metadata
is a FAIL.

---

## NanoVDB (GPU Path for Real-Time Lookdev)

- Convert OpenVDB -> NanoVDB for GPU acceleration
- Use in Unreal Engine / TouchDesigner for real-time pre-visualization
- Grid class: `nanovdb::GridClass::FogVolume` for density fields
- NOT for final render -- quality insufficient for exhibition tier
- Useful for Installer's gallery pre-visualization and interactive demos
- Preserves grid topology but may quantize values (verify range preservation)

---

## Dependency Graph

```
Spectralist re-assimilates
  -> VDB caches INVALIDATE
    -> Houdini SOP chain re-executes
      -> USD references update (asset path unchanged, content changed)
        -> Render re-executes

Sculptor changes noise
  -> Only turbulence VDB re-generated
    -> Downstream from VDB stage re-executes

Tonalist adjusts TF
  -> Only PxrVolume shader parameters change
    -> Only render stage re-executes (VDB caches valid)

Choreographer moves camera
  -> Only render stage re-executes (all caches valid)
```

Minimal re-execution is the goal. The Alchemist verifies that dependency
tracking correctly identifies what invalidates and what survives.
