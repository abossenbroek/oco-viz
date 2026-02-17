---
name: pipeline-migration
user-invocable: false
type: instruction
---

# Pipeline Migration Checklist -- VTK to Houdini Transition

Future-facing checklist for validating VTK-to-Houdini pipeline migration.
Each item must pass before a shot is promoted from VTK pre-viz to Karma XPU
production rendering.

---

## Migration Checklist

### 1. OpenVDB Grid Naming

- [ ] Density grid named `"density"` (not `"Density"`, `"cd"`, or `"Cd"`)
- [ ] Velocity grid named `"vel"` (not `"velocity"`, `"v"`, or `"wind"`)
- [ ] Temperature grid named `"temperature"` (not `"temp"`, `"T"`, or `"heat"`)
- [ ] Grid names verified against Houdini native volume SOP expectations

### 2. Voxel Spacing

- [ ] Voxel size = world_size / resolution (meters, not arbitrary units)
- [ ] `vdb.createLinearTransform(voxelSize=...)` matches intended Houdini scale
- [ ] 1 voxel unit = 1 meter in Houdini scene scale
- [ ] Volume bounding box verified in Houdini viewport after import

### 3. Sparse Design

- [ ] Empty regions contain exact 0.0 (not 1e-8 or epsilon residuals)
- [ ] Sparsity > 80% for atmospheric volumes (prune verification)
- [ ] `vdb_print` reports expected active voxel count
- [ ] File size proportional to active region, not full grid extent

### 4. Constraint Grid Transfer

- [ ] `transport_vectors` (Vec3fGrid) survives VDB round-trip without axis swap
- [ ] `max_kinetic_energy` values preserved within float32 precision
- [ ] `shear_tensor` eigenvalue ordering unchanged after format conversion
- [ ] All constraint grids share voxel size and world origin with density grid

### 5. Transfer Function Translation

- [ ] VTK TF color stops mapped to MaterialX `standard_volume` emission ramp
- [ ] VTK TF opacity stops mapped to MaterialX absorption/scattering density
- [ ] Non-linear VTK opacity curves approximated with sufficient ramp points
- [ ] Achromatic constraint preserved in MaterialX shader (soot palette)

### 6. Temporal Layering

- [ ] DRONE temporal offset works in Solaris timeline (frame range correct)
- [ ] CHURN noise seeds produce consistent results across VTK and Houdini
- [ ] ASH/SPARK emission flicker phase aligns between pre-viz and production
- [ ] Frame-to-frame continuity verified (no pops at shot boundaries)

### 7. Visual Regression

- [ ] Same frame rendered in both VTK and Karma XPU
- [ ] Plume structure (silhouette, wispy edges) matches between renderers
- [ ] Density distribution histogram comparison within 5% tolerance
- [ ] Mood and lighting intent preserved (not identical pixels, same feeling)
- [ ] No grid artifacts, axis flips, or missing channels in Karma output
