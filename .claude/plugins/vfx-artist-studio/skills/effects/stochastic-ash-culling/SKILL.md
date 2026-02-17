---
name: stochastic-ash-culling
user-invocable: false
type: instruction
primary_owner: effects-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Stochastic Ash Culling -- Binary Alpha Masking in the Crumble Zone

Reference: Ash falling from industrial stacks. At the plume boundary, density does not
fade smoothly to zero -- it disintegrates into discrete particles. Some voxels are ash;
some are air. The transition is binary, not gradual. The edge crumbles into a stochastic
field of present-or-absent fragments, like the edge of a charcoal drawing where individual
grains of carbon sit alone on the paper surface, separated by pure white ground.

> "Ash does not fade. It breaks."

---

## Principle

In the low-density crumble zone (density 0.0 to 0.2), voxel opacity is determined by a
binary test against a blue noise threshold. Blue noise is spatially uniform -- unlike white
noise, it does not produce visible clusters or voids. The result is a stochastic edge that
reads as particulate disintegration rather than smooth falloff.

The threshold is remapped from density: at density 0.0, the threshold is 1.0 (nothing
survives); at density 0.2 (the crumble ceiling), the threshold is 0.0 (everything
survives). Between these values, the threshold drops linearly, and each voxel lives or
dies based on whether the blue noise sample at its position falls below the threshold.

Above the crumble zone (density > 0.2), voxels have full opacity. The culling operates
ONLY in the crumble transition zone.

---

## Procedure

### Step 1 -- Generate or Load the Blue Noise Field

Blue noise has a power spectrum that suppresses low-frequency content, producing spatially
uniform sampling with no visible clumps or voids. The field is 3D, tiled at 128^3, and
pre-computed for temporal stability.

```python
import numpy as np

def generate_blue_noise_3d(
    resolution: int = 128,
    seed: int = 42,
) -> np.ndarray:
    """Generate a 3D blue noise field via void-and-cluster.

    Returns a volume of shape (resolution, resolution, resolution)
    with values in [0, 1], spatially uniform distribution.
    """
    rng = np.random.default_rng(seed)
    # Initialize with white noise
    field = rng.random((resolution, resolution, resolution)).astype(np.float32)

    # Iterative void-and-cluster refinement
    # (simplified: in production, use a proper void-and-cluster algorithm
    # or load a pre-computed blue noise texture)
    from scipy.ndimage import gaussian_filter
    for _ in range(16):
        blurred = gaussian_filter(field, sigma=1.5, mode="wrap")
        # Find the tightest cluster (max of blurred) and move it to void (min of blurred)
        cluster_idx = np.unravel_index(np.argmax(blurred), field.shape)
        void_idx = np.unravel_index(np.argmin(blurred), field.shape)
        field[cluster_idx], field[void_idx] = field[void_idx], field[cluster_idx]

    # Normalize to [0, 1]
    field = (field - field.min()) / (field.max() - field.min() + 1e-8)
    return field
```

### Step 2 -- Tile Blue Noise to Match Density Volume

If the density volume is larger than the blue noise resolution, tile the noise field to
cover it. Blue noise tiles seamlessly because the void-and-cluster algorithm uses
`mode="wrap"` during generation.

```python
# Tile blue noise to match density volume shape
blue_noise = generate_blue_noise_3d(resolution=blue_noise_resolution)  # default 128

# Tile to cover the full density volume
nz, ny, nx = density.shape
bn = np.tile(
    blue_noise,
    (
        (nz // blue_noise_resolution) + 1,
        (ny // blue_noise_resolution) + 1,
        (nx // blue_noise_resolution) + 1,
    ),
)[:nz, :ny, :nx]
```

### Step 3 -- Compute the Crumble Threshold

Remap density in the crumble zone [0.0, 0.2] to a threshold [1.0, 0.0]. Above the
crumble zone, threshold is 0.0 (all voxels survive).

```python
def remap(value, in_low, in_high, out_low, out_high):
    """Linear remap with clamping."""
    t = np.clip((value - in_low) / (in_high - in_low + 1e-8), 0.0, 1.0)
    return out_low + t * (out_high - out_low)

# Remap density to threshold: low density -> high threshold -> more culling
threshold = remap(density, crumble_low, crumble_high, 1.0, 0.0)
# crumble_low = 0.0 (fixed), crumble_high = 0.2 (default)
```

### Step 4 -- Apply Binary Alpha Culling

Compare blue noise against the threshold. If `blue_noise < threshold`, the voxel is
culled (alpha = 0). Otherwise, it survives (alpha = 1). This is a binary decision --
no intermediate opacity values in the crumble zone.

```python
# Binary culling: voxel either fully present or fully absent
alpha = np.where(bn < threshold, 0.0, 1.0).astype(np.float32)

# Apply alpha to density
density_culled = density * alpha
```

### Step 5 -- Optional Temporal Jitter

For animation, a small temporal jitter can be added to the blue noise per frame to
prevent the culling pattern from being perfectly static. The jitter is tiny (0.0 - 0.02)
-- enough to create subtle shimmering at the edge without visible motion.

```python
if temporal_jitter > 0.0:
    rng_frame = np.random.default_rng(seed + time_index)
    jitter = rng_frame.uniform(-temporal_jitter, temporal_jitter, size=bn.shape)
    bn_jittered = np.clip(bn + jitter, 0.0, 1.0)
    alpha = np.where(bn_jittered < threshold, 0.0, 1.0).astype(np.float32)
    density_culled = density * alpha
```

### Step 6 -- Validate Culling Edge

Render a scout pass. The crumble zone should:
- Show discrete voxel fragments at the plume boundary
- No visible clumping or void patterns (blue noise is spatially uniform)
- No tiling artifacts (check at volume boundaries)
- Sharp binary transition: voxels are fully present or fully absent, no partial opacity

---

## Parameters

### Wedge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `crumble_low` | float | 0.0 | 0.0 (fixed) | Lower bound of crumble zone |
| `crumble_high` | float | 0.2 | 0.1 - 0.3 | Upper bound of crumble zone (density above this is fully opaque) |
| `blue_noise_resolution` | int | 128 | 64 - 256 | Resolution of 3D blue noise tile |
| `temporal_jitter` | float | 0.0 | 0.0 - 0.02 | Per-frame jitter added to blue noise for animation |

### Derived Parameters

| Parameter | Derivation | Description |
|-----------|-----------|-------------|
| `threshold` | `remap(density, 0.0, 0.2, 1.0, 0.0)` | Per-voxel culling threshold |
| `alpha` | `1.0 if blue_noise >= threshold else 0.0` | Binary opacity mask |

### Tier Behavior

| Tier | Behavior |
|------|----------|
| **Exhibition** | Full: blue noise culling in [0.0, 0.2] crumble zone |
| **Study** | Smooth opacity ramp (no binary culling -- standard density falloff) |
| **Sketch** | Simple binary threshold at density 0.05 (no blue noise) |

---

## API Dependencies

| Dependency | Module | Function | Usage |
|------------|--------|----------|-------|
| Gaussian filter | `scipy.ndimage` | `gaussian_filter` | Blue noise void-and-cluster generation |
| Noise field | `numpy` | `np.random.default_rng` | White noise initialization for blue noise |

---

## Anti-Patterns

### 1. The White Noise Culling

**Symptom:** The crumble zone shows visible clusters and voids -- some areas have dense
clumps of surviving voxels while adjacent areas are empty. The edge looks patchy rather
than uniformly stochastic.

**Cause:** Using white noise instead of blue noise for the threshold comparison. White
noise has unconstrained low-frequency content, producing visible spatial patterns in the
culling mask.

**Fix:** Use blue noise generated via void-and-cluster or loaded from a pre-computed
blue noise texture. Blue noise suppresses low frequencies, ensuring that surviving voxels
are spatially uniform with no visible clustering.

### 2. The Smooth Culling

**Symptom:** The crumble zone fades smoothly to zero opacity. No individual voxels are
visible at the boundary. The edge reads as a soft gradient, not as particulate
disintegration.

**Cause:** Using the blue noise value as an opacity multiplier instead of as a binary
threshold test. The culling must be binary: 0 or 1, nothing in between.

**Fix:** Use strict binary comparison: `alpha = 1.0 if blue_noise >= threshold else 0.0`.
No intermediate values. The ash either exists or it does not. Partial opacity defeats
the purpose of stochastic culling.

### 3. The Visible Tiling

**Symptom:** A periodic grid pattern is visible in the culling mask, repeating every N
voxels. The tiling of the blue noise field produces visible seams or repetition.

**Cause:** Blue noise resolution too low relative to the density volume, or the tiling
boundary produces discontinuities because the noise was not generated with wrapping.

**Fix:** Generate blue noise with `mode="wrap"` in the Gaussian filter to ensure
seamless tiling. Use `blue_noise_resolution` = 128 (default) or higher. If tiling
artifacts persist, increase resolution to 256.

### 4. The Over-Extended Crumble Zone

**Symptom:** The binary culling extends deep into the plume interior, creating holes
in medium-density regions. The plume looks Swiss-cheesed rather than crumble-edged.

**Cause:** `crumble_high` set too high (> 0.3), extending the culling zone beyond the
true plume boundary into the body of the volume.

**Fix:** Keep `crumble_high` within 0.1 - 0.3 (default 0.2). The crumble zone should
cover only the lowest-density transition at the plume edge. Above density 0.2, all
voxels should survive unconditionally.

---

## Validation Checklist

- [ ] Blue noise field generated (not white noise) -- spatially uniform
- [ ] Binary alpha: only 0.0 or 1.0 in the crumble zone (no intermediate values)
- [ ] Crumble zone limited to density [0.0, 0.2] (default)
- [ ] Above crumble_high, all voxels fully opaque
- [ ] No visible tiling artifacts at noise field boundaries
- [ ] No visible clustering or void patterns in culled edge
- [ ] Blue noise resolution at least 128^3
- [ ] Temporal jitter within 0.0 - 0.02 range (if used)
- [ ] Scout render shows discrete voxel fragments at plume boundary
- [ ] Study tier uses smooth opacity ramp (no binary culling)
- [ ] Sketch tier uses simple binary threshold (no blue noise)
- [ ] Blue noise wraps seamlessly for tiling
