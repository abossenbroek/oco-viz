---
name: data-driven-turbulence
user-invocable: false
---

# Data-Driven Turbulence -- Constrained Generative Dynamics

Turbulence that is motivated by climate data, not decorative. Wind and pressure
fields constrain the procedural noise, giving the substance physically grounded
behavior. Used by both Spectralist (constraint derivation) and Sculptor
(artistic application within constraints).

---

## Constraint Integration

Four physical fields govern the procedural noise:

1. **Direction**: `shear_tensor` determines anisotropy axis -- turbulence stretches along wind shear, not arbitrarily.
2. **Amplitude**: `max_kinetic_energy` caps noise amplitude per voxel -- dense wind regions produce more energetic turbulence, calm regions stay quiescent.
3. **Frequency**: Temperature gradient maps to noise frequency -- warm convective regions produce high-frequency turbulence, stable stratified regions produce low-frequency laminar structure.
4. **Character**: `boundary_layer_height` determines coupling -- below BLH, turbulence is surface-coupled and convective. Above BLH, free-atmospheric and layered.

---

## Noise Stack (Additive Octaves)

| Octave | Frequency | Amplitude | Source |
|--------|-----------|-----------|--------|
| 1 (base) | grid_spacing x 4 | 1.0 | ERA5 wind field direction |
| 2 | base x lacunarity | 0.5 x persistence | Shear tensor anisotropy |
| 3 | base x lacunarity^2 | 0.25 x persistence^2 | Temperature gradient modulation |
| 4 | base x lacunarity^3 | 0.125 x persistence^3 | Procedural (aesthetic) |
| 5+ | higher | diminishing | Grit detail (Sculptor's domain) |

**Key insight**: Octaves 1-3 are data-driven (constrained by ERA5 wind/pressure/temperature).
Octaves 4+ are procedural (aesthetic detail). This creates turbulence that FEELS motivated
by climate data at large scales, with artistic detail at small scales.

The `data_influence` parameter (0.0-1.0, default 0.7) controls the weight of physical
constraints vs procedural freedom. At 1.0, turbulence is fully data-driven. At 0.0,
turbulence is fully procedural (Spectralist would flag this as CONCERN).

---

## Parameters

| Parameter | Range | Default | Maps To |
|-----------|-------|---------|---------|
| lacunarity | 1.5-3.0 | 2.0 | Frequency ratio between octaves |
| persistence | 0.3-0.7 | 0.5 | Amplitude falloff between octaves |
| anisotropy_ratio | 1.0-5.0 | 2.0 | Z-squash for geological folding |
| data_influence | 0.0-1.0 | 0.7 | Weight of physical constraints vs procedural |
| seed | int | -- | Reproducibility |
| num_octaves | 3-8 | 4 | Total octave count |

---

## Grid Resolution Constraints

| Grid Size | Max Octaves | Notes |
|-----------|-------------|-------|
| 64 x 64 x 48 | 3 | Sketch tier, minimal turbulence |
| 96 x 96 x 64 | 4 | Study tier, no "brick wall" at lacunarity=2.0 |
| 128 x 128 x 96 | 6 | Exhibition tier, full geological folding |
| 192 x 192 x 128 | 8 | Ultra exhibition, extreme detail |

Exceeding the octave limit for a given grid size produces aliasing artifacts
("brick wall" texture at Nyquist frequency).

---

## VTK Implementation Notes (Current Pipeline)

- 4 octaves with lacunarity=2.0 at 96x96x64 grid -- no "brick wall" artifacts
- 6 octaves need >= 128x128x96 grid
- Anisotropic Z-squash (dz < dx/dy) creates sedimentary geological folding
- Gaussian smoothing sigma=2.0 eliminates voxelization at octave boundaries (sigma=1.0 insufficient)
- Boundary falloff (raised-cosine, 15% margin) eliminates VTK bounding box artifacts
- Soft thresholding (quadratic below 5% cutoff) produces better edges than hard cutoff

---

## Future Pipeline (Houdini/OpenVDB)

When the pipeline migrates from VTK to Houdini:
- VEX implementation of constrained noise using `shear_tensor` grid as anisotropy input
- Per-voxel amplitude clamping against `max_kinetic_energy` grid
- Native OpenVDB sparse evaluation (only active voxels computed)
- Real-time lookdev via NanoVDB in TouchDesigner/Unreal
- Multi-resolution VDB for LOD-based turbulence detail

The constraint integration workflow remains identical -- only the implementation layer changes.
