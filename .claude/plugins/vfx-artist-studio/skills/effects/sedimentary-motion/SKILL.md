---
name: sedimentary-motion
user-invocable: false
type: instruction
primary_owner: effects-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Sedimentary Motion -- Anisotropic Noise and Viscosity for Geological Layering

Reference: Geological strata, coal seam layers. The horizontal banding of sedimentary
rock, where each layer records a different epoch of deposition. In volumetric terms: the
plume develops horizontal shelves and ledges as if the density were settling into layers,
resisting vertical mixing while allowing lateral drift. The motion is glacial, heavy,
stratified -- as if the air itself has become geological.

> "The smoke remembers which way the ground lies."

---

## Principle

Two mechanisms combine to produce the sedimentary look:

**Anisotropic noise** with a heavily compressed Y-axis (0.1x) creates horizontal shelves
in the density field. The noise sees 10x more spatial frequency vertically than
horizontally, producing flat, extended structures that read as strata.

**Viscosity mapping** based on density causes high-density regions to resist motion.
Velocity is damped proportionally to `density^2.0`, so dense strata move sluggishly while
low-density wisps between them flow freely. The quadratic relationship prevents the
viscosity from overwhelming the motion at low densities while creating strong resistance
at high densities.

---

## Procedure

### Step 1 -- Generate Anisotropic Noise Field

Scale the coordinate space before evaluating `fbm_3d` to compress the Y-axis. This
produces noise features that are stretched horizontally and compressed vertically --
the signature of sedimentary layering.

```python
import numpy as np
from oco_viz.plume.noise import fbm_3d

# Generate base noise at full resolution
noise = fbm_3d(
    shape=density.shape,
    octaves=sed_octaves,       # default 5
    lacunarity=2.0,
    gain=0.5,
    seed=42,
)

# Apply anisotropic coordinate scaling to create horizontal shelves.
# The noise field itself is generated isotropically, then resampled
# with compressed Y coordinates to produce horizontal stretching.
nz, ny, nx = density.shape
coords_z = np.linspace(0, nz - 1, nz)
coords_y = np.linspace(0, ny - 1, ny) * y_compression  # 0.1x = heavy horizontal bias
coords_x = np.linspace(0, nx - 1, nx)

# Build anisotropic coordinate grid for resampling
from scipy.ndimage import map_coordinates

zz, yy, xx = np.meshgrid(coords_z, coords_y, coords_x, indexing="ij")
aniso_noise = map_coordinates(
    noise.astype(np.float64),
    [zz.ravel(), yy.ravel(), xx.ravel()],
    order=1,
    mode="wrap",
).reshape(density.shape).astype(np.float32)

# Center around zero and scale
aniso_noise = (aniso_noise - 0.5) * sed_amplitude  # default 0.25
```

### Step 2 -- Apply Sedimentary Displacement to Density

Modulate the density field with the anisotropic noise to carve horizontal shelves
into the plume structure. Regions where `aniso_noise` is negative lose density,
creating gaps between strata. Regions where it is positive gain density,
reinforcing the shelf structure.

```python
density_sed = density * (1.0 + aniso_noise)
np.maximum(density_sed, 0.0, out=density_sed)
```

### Step 3 -- Compute Viscosity and Damp Velocity

Map density to viscosity using a quadratic relationship. High-density strata resist
motion; low-density inter-strata gaps flow freely. Apply viscosity damping to the
velocity field to produce the heavy, geological motion character.

```python
# Quadratic viscosity: dense regions resist motion
viscosity = np.clip(density_sed, 0.0, 1.0) ** 2.0

# Damp velocity proportionally to viscosity and strength
velocity_damped = velocity * (1.0 - viscosity * viscosity_strength)  # default 0.5
```

### Step 4 -- Combine with Plume Turbulence

The sedimentary displacement is applied BEFORE standard plume turbulence from
`apply_turbulence`. The turbulence then acts on the already-stratified field,
introducing wispy detail between the shelves without destroying the layered structure.

```python
from oco_viz.plume.turbulent import apply_turbulence

# Apply turbulence to already-stratified density
density_final = apply_turbulence(density_sed, turb_cfg, grid_cfg, time_index)
```

### Step 5 -- Validate Stratification

Render a scout pass. The plume should exhibit:
- Visible horizontal banding / shelf structures
- Dense strata moving slowly, wisps between them moving faster
- Layered structure that reads as geological, not as turbulent eddies
- The overall plume shape preserved -- stratification adds detail, not new form

---

## Parameters

### Wedge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `y_compression` | float | 0.1 | 0.05 - 0.2 | Y-axis coordinate compression (lower = more horizontal) |
| `viscosity_strength` | float | 0.5 | 0.2 - 0.8 | Viscosity damping strength (higher = more resistance) |
| `sed_octaves` | int | 5 | 3 - 6 | fBm octaves for sedimentary noise |
| `sed_amplitude` | float | 0.25 | 0.1 - 0.4 | Amplitude of sedimentary density modulation |

### Derived Parameters

| Parameter | Derivation | Description |
|-----------|-----------|-------------|
| `viscosity` | `clip(density, 0, 1) ^ 2.0` | Per-voxel motion resistance |
| `velocity_damped` | `velocity * (1 - viscosity * strength)` | Viscosity-damped velocity field |

### Tier Behavior

| Tier | Behavior |
|------|----------|
| **Exhibition** | Full: y_compression=0.1, 5 octaves, viscosity_strength=0.5 |
| **Study** | Reduced: y_compression=0.2, 3 octaves, viscosity_strength=0.3 |
| **Sketch** | Disabled -- no sedimentary effects |

---

## API Dependencies

| Dependency | Module | Function | Usage |
|------------|--------|----------|-------|
| fBm noise | `src/oco_viz/plume/noise.py` | `fbm_3d` | Generate base noise for anisotropic resampling |
| Turbulence | `src/oco_viz/plume/turbulent.py` | `apply_turbulence` | Post-stratification turbulence detail |
| Resampling | `scipy.ndimage` | `map_coordinates` | Anisotropic coordinate resampling |

---

## Anti-Patterns

### 1. The Isotropic Noise

**Symptom:** The density modulation reads as turbulent eddies rather than horizontal
shelves. No visible stratification. The plume looks churned, not layered.

**Cause:** Using isotropic noise (equal frequency in all axes) instead of anisotropic
noise with compressed Y-axis. Without the 10:1 horizontal-to-vertical frequency ratio,
the noise cannot produce shelf structures.

**Fix:** Apply `y_compression` = 0.1 (default) to the Y coordinate before resampling.
The heavy compression produces features that extend horizontally and repeat vertically
at high frequency -- the signature of sedimentary banding.

### 2. The Linear Viscosity

**Symptom:** Even low-density wisps move sluggishly. The inter-strata gaps do not flow
freely, so the layered structure lacks the density-dependent motion contrast that makes
it read as geological.

**Cause:** Using `viscosity = density * strength` (linear) instead of
`viscosity = density^2.0 * strength` (quadratic). Linear viscosity damps low-density
regions too aggressively, killing the motion contrast.

**Fix:** Use quadratic viscosity: `viscosity = clip(density, 0, 1)^2.0`. The quadratic
curve provides near-zero damping at low densities and strong damping at high densities,
creating the fast-wisp / slow-stratum contrast.

### 3. The Overwhelming Shelves

**Symptom:** The sedimentary banding dominates the plume shape entirely. The original
plume form is unrecognizable, replaced by a stack of horizontal slabs with no connection
to the underlying Gaussian base or HYSPLIT transport.

**Cause:** `sed_amplitude` set too high (> 0.4), causing the anisotropic noise to
overpower the base density field. The sedimentary modulation should add texture, not
replace form.

**Fix:** Keep `sed_amplitude` within 0.1 - 0.4 (default 0.25). The modulation is
`density * (1 + aniso_noise)`, so amplitude 0.25 creates a +/-25% density variation --
enough to carve visible shelves without destroying the plume silhouette.

### 4. The Post-Turbulence Stratification

**Symptom:** Sedimentary shelves appear sharp and geometric, unaffected by the plume's
turbulent character. The stratification looks stamped on top rather than integrated into
the volume.

**Cause:** Applying sedimentary displacement AFTER turbulence instead of BEFORE. The
turbulence needs to act on the already-stratified field to soften the shelf edges and
introduce wispy detail between strata.

**Fix:** Apply sedimentary displacement first, then pass the stratified density to
`apply_turbulence`. The turbulence breaks up the shelf edges naturally.

---

## Validation Checklist

- [ ] Horizontal banding visible in rendered output (shelf structures)
- [ ] Y-axis coordinate compressed by `y_compression` factor (default 0.1)
- [ ] Viscosity uses quadratic relationship: `density^2.0`
- [ ] Dense strata move slower than inter-strata wisps
- [ ] Sedimentary displacement applied BEFORE plume turbulence
- [ ] Original plume silhouette preserved (stratification adds, does not replace)
- [ ] `sed_amplitude` within 0.1 - 0.4 range (no overwhelming shelves)
- [ ] Scout render shows layered-not-turbulent character
- [ ] Velocity damping proportional to viscosity and `viscosity_strength`
- [ ] Density clamped to >= 0.0 after sedimentary modulation
- [ ] Study tier uses reduced parameters (y_compression=0.2, 3 octaves)
- [ ] Sketch tier has sedimentary effects fully disabled
