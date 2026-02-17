---
name: paper-grain-manifold
user-invocable: false
type: instruction
primary_owner: effects-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Paper Grain Manifold -- Static Noise Subtraction for Tooth and Texture

Reference: William Kentridge -- charcoal on black paper. The tooth of the paper shows
through the drawing in the interior zones where the charcoal dust sits loosely, but the
hard-pressed edges remain dense and clean. The grain is a property of the rendering
surface, not the subject. It does not move with the plume. It is always there, waiting
under the density like the weave of canvas under paint.

> "The paper has its own opinion."

---

## Principle

A static 3D noise field is subtracted from the density volume before opacity evaluation.
The noise field is generated once per shot from a fixed seed, using `fbm_3d` from
`src/oco_viz/plume/noise.py` at 8 octaves -- two more than the standard 6 used for plume
turbulence. The extra octaves introduce finer structure that reads as paper tooth rather
than atmospheric turbulence.

The grain is suppressed at density edges (high gradient magnitude) and visible in density
interiors (low gradient magnitude). This mirrors charcoal technique: the paper tooth is
visible where the hand is light, invisible where the mark is pressed hard.

---

## Procedure

### Step 1 -- Generate the Static Grain Field

Generate a single `fbm_3d` noise field matching the density volume shape. This field is
computed once and reused for every frame in the shot. The grain field does NOT advect,
does NOT change per frame, and does NOT respond to velocity. It is a fixed manifold in
rendering space -- the tooth of the virtual paper.

```python
from oco_viz.plume.noise import fbm_3d

grain_field = fbm_3d(
    shape=density.shape,      # match density volume dimensions
    octaves=grain_octaves,    # default 8 (vs 6 for plume turbulence)
    lacunarity=grain_lacunarity,  # default 2.2
    gain=0.5,
    seed=grain_seed,          # default 7777, fixed per shot
)
# Center around zero: [-0.5, 0.5]
grain_field = grain_field - 0.5
```

### Step 2 -- Compute the Edge-Suppression Weight

Compute the gradient magnitude of the density field. Where gradient is high (edges, wispy
boundaries), grain is suppressed. Where gradient is low (dense interiors, flat plateaus),
grain is fully visible.

```python
import numpy as np

# Gradient magnitude across all three spatial axes
gz, gy, gx = np.gradient(density.astype(np.float64))
grad_mag = np.sqrt(gz**2 + gy**2 + gx**2).astype(np.float32)

# Normalize gradient magnitude to [0, 1]
grad_max = grad_mag.max()
if grad_max > 0:
    grad_norm = np.clip(grad_mag / grad_max, 0.0, 1.0)
else:
    grad_norm = np.zeros_like(grad_mag)

# grain_weight: 1.0 in interiors (low gradient), 0.0 at edges (high gradient)
grain_weight = 1.0 - grad_norm
```

### Step 3 -- Apply Grain Subtraction

Subtract the weighted grain from the density field. The subtraction erodes density in
interior zones, creating the tooth-of-paper texture. Clamp to zero -- grain can remove
density but never add it.

```python
# Apply grain: subtract weighted noise from density
density_grained = density - grain_amplitude * grain_weight * grain_field
np.maximum(density_grained, 0.0, out=density_grained)
```

### Step 4 -- Validate Grain Visibility

Render a scout pass. The grain should be:
- Invisible at density edges and in the wispy halo
- Visible as subtle texture in the dense core and plateaus
- Static across frames -- if the grain appears to swim or advect, the implementation
  is using a per-frame seed instead of a fixed seed

---

## Parameters

### Wedge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_amplitude` | float | 0.05 | 0.02 - 0.12 | Strength of grain subtraction from density |
| `grain_octaves` | int | 8 | 6 - 10 | fBm octaves for grain field (higher = finer tooth) |
| `grain_lacunarity` | float | 2.2 | 2.0 - 2.5 | Frequency multiplier per grain octave |
| `grain_seed` | int | 7777 | any | Fixed seed per shot (must not change between frames) |

### Derived Parameters

| Parameter | Derivation | Description |
|-----------|-----------|-------------|
| `grain_weight` | `1.0 - clamp(\|grad(density)\| / grad_max, 0, 1)` | Edge suppression mask |
| `grad_max` | `max(gradient_magnitude(density))` | Per-frame normalization factor |

### Tier Behavior

| Tier | Behavior |
|------|----------|
| **Exhibition** | Full grain: 8 octaves, amplitude 0.05, fixed seed per shot |
| **Study** | Disabled -- no grain subtraction applied |
| **Sketch** | Disabled -- no grain subtraction applied |

---

## API Dependencies

| Dependency | Module | Function | Usage |
|------------|--------|----------|-------|
| fBm noise | `src/oco_viz/plume/noise.py` | `fbm_3d` | Generate static grain field |
| Gradient | `numpy` | `np.gradient` | Compute density gradient for edge suppression |

---

## Anti-Patterns

### 1. The Advecting Grain

**Symptom:** The grain texture appears to drift, swim, or flow with the plume motion
across frames. The tooth of the paper moves with the charcoal instead of staying fixed
underneath it.

**Cause:** Using a per-frame seed or regenerating the grain field each timestep. The
grain field must be computed once with a fixed seed and reused for every frame.

**Fix:** Generate `grain_field` once before the frame loop. Use `grain_seed` = 7777
(or any fixed value). Never pass `time_index` or frame number to the grain seed.

### 2. The Shared Octaves

**Symptom:** The grain reads as turbulence rather than paper texture. The visual
frequency of the grain matches the plume's own turbulent displacement, making them
indistinguishable.

**Cause:** Using the same octave count (6) for grain as for plume turbulence. The grain
must operate at a higher frequency (more octaves) to read as a distinct textural layer.

**Fix:** Use `grain_octaves` = 8 (default) or higher. The two extra octaves above the
plume's 6 introduce sub-turbulence-scale detail that reads as material texture.

### 3. The Colored Grain

**Symptom:** The grain introduces chromatic variation -- some voxels appear warmer or
cooler than their neighbors due to the grain. The achromatic soot language is compromised.

**Cause:** Applying grain to individual color channels or to emission rather than to the
scalar density field. Grain is a density-space operation. It subtracts mass, not color.

**Fix:** Apply grain subtraction only to the density scalar. Never apply grain to RGB
channels, emission color, or albedo independently.

### 4. The Everywhere Grain

**Symptom:** Grain is equally visible at density edges and in the wispy halo. The plume
boundary looks noisy and jagged instead of smooth and atmospheric.

**Cause:** Omitting the gradient-based edge suppression (`grain_weight`). Without edge
suppression, grain erodes the wispy halo that gives the plume its atmospheric character.

**Fix:** Compute `grain_weight = 1.0 - grad_norm` and multiply it into the grain
subtraction. High-gradient regions (edges) get zero grain; low-gradient regions
(interiors) get full grain.

---

## Validation Checklist

- [ ] Grain field generated with `fbm_3d` at 8 octaves (not 6)
- [ ] Fixed seed per shot -- grain field identical across all frames
- [ ] `grain_weight` computed from density gradient magnitude
- [ ] Grain invisible at density edges (high gradient regions)
- [ ] Grain visible as subtle texture in dense interior zones
- [ ] Grain subtracted from density only (not from color or emission)
- [ ] `density_grained` clamped to >= 0.0 after subtraction
- [ ] Scout render inspected for static grain (no swimming or advection)
- [ ] Grain amplitude within 0.02 - 0.12 range (default 0.05)
- [ ] Disabled for Study and Sketch tiers
- [ ] No chromatic artifacts from grain application
- [ ] Grain lacunarity set to 2.2 (not plume default 2.0)

---

## Art-Historical Parameter Mapping

| Artistic Reference | Physical Sensation | Pipeline Parameter | Calibration |
|--------------------|--------------------|--------------------|-------------|
| Kentridge charcoal tooth at light hand pressure | Paper texture visible through sparse marks | Grain visible at density < 0.2, invisible at density > 0.8 | Edge-suppression weight threshold |
| Kentridge charcoal on black paper (albedo ~0.04) | Near-black surface with subtle luminance variation | `grain_amplitude` producing 4% luminance variation | Calibrate so max grain effect = 0.04 relative luminance delta |

The grain should behave like charcoal tooth: visible where the artist's hand is light
(low density), suppressed where the mark is pressed hard (high density). The 4% luminance
target matches the measured albedo of charcoal on black stock paper.
