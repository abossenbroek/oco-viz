---
name: soot-crust-shader
user-invocable: false
type: instruction
primary_owner: effects-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Soot Crust Shader -- Dual-State Volume Material via Gradient Magnitude

Reference: Industrial slag, cooling lava. The surface crusts over -- matte black,
absorptive, dead to light. But beneath the crust, the interior remains translucent,
scattering photons forward through the grey particulate like light passing through
smoke from behind. The crust is opacity. The interior is transmission. Two states,
one material, separated by the sharpness of the density gradient.

> "The surface is where light goes to die. The interior is where it goes to haunt."

---

## Principle

The soot crust shader creates a dual-state volumetric material based on the gradient
magnitude of the density field. Where the gradient is high (density changes rapidly --
the surface), the material is absorptive: matte black, no scattering, albedo 0.02. Where
the gradient is low (density is flat -- the interior), the material is translucent:
high scattering, albedo 0.85, with strong forward scattering anisotropy (0.8) that
creates the "ghost light" effect of backlit smoke.

The transition between crust and interior is a smooth interpolation via `smoothstep`,
not a hard binary switch. The `blend_width` parameter controls the sharpness of this
transition.

MaterialX `standard_volume` with `scattering_anisotropy` = 0.8 for the interior state
produces strong forward scattering: photons preferentially continue in their original
direction through the volume, creating the translucent grey glow visible when the plume
is backlit or side-lit. This is the "ghost light" -- light that passes through the volume
and reaches the camera, dim and diffused.

---

## Procedure

### Step 1 -- Compute Gradient Magnitude

The density gradient magnitude determines the crust-interior boundary. High gradient =
surface = crust. Low gradient = interior = translucent.

```python
import numpy as np

# Compute gradient magnitude of density field
gz, gy, gx = np.gradient(density.astype(np.float64))
grad_mag = np.sqrt(gz**2 + gy**2 + gx**2).astype(np.float32)
```

### Step 2 -- Normalize and Compute Crust Factor

Normalize the gradient magnitude to [0, 1], then apply `smoothstep` to create the
crust factor. The crust factor is 1.0 at the surface (high gradient) and 0.0 in the
interior (low gradient).

```python
# Normalize gradient magnitude
grad_max = grad_mag.max()
if grad_max > 0:
    crust_norm = grad_mag / grad_max
else:
    crust_norm = np.zeros_like(grad_mag)

# Smoothstep for gradual transition
def smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
    """Hermite interpolation between edge0 and edge1."""
    t = np.clip((x - edge0) / (edge1 - edge0 + 1e-8), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

# crust_factor: 1.0 at surface (high gradient), 0.0 in interior (low gradient)
crust_factor = smoothstep(
    crust_threshold - blend_width,   # default 0.4 - 0.05 = 0.35
    crust_threshold + blend_width,   # default 0.4 + 0.05 = 0.45
    crust_norm,
)
```

### Step 3 -- Interpolate Material Parameters

Blend between crust (surface) and interior parameters using the crust factor. Every
material parameter is interpolated, not switched.

```python
# CRUST state (high gradient / surface):
#   absorption = 1.0, scattering = 0.0, albedo = 0.02 (matte black)
# INTERIOR state (low gradient / interior):
#   absorption = 0.1, scattering = 0.8, albedo = 0.85 (translucent grey)

absorption = crust_factor * crust_absorption + (1.0 - crust_factor) * 0.1
# crust_absorption default = 1.0

scattering = crust_factor * 0.0 + (1.0 - crust_factor) * interior_scattering
# interior_scattering default = 0.8

albedo = crust_factor * 0.02 + (1.0 - crust_factor) * 0.85

# Scattering anisotropy (Henyey-Greenstein g parameter)
# Crust: isotropic (irrelevant since scattering=0)
# Interior: strong forward scatter = "ghost light"
anisotropy = (1.0 - crust_factor) * scattering_anisotropy
# scattering_anisotropy default = 0.8
```

### Step 4 -- Generate MaterialX Shader

The dual-state material is expressed as a MaterialX `standard_volume` with
spatially-varying parameters driven by the crust factor field.

```xml
<!-- MaterialX standard_volume with dual-state soot crust -->
<standard_volume name="soot_crust">
  <!-- Parameters interpolated per-voxel by crust_factor -->
  <input name="density" type="float" value="1.0"/>
  <input name="absorption" type="float" nodename="crust_absorption_interp"/>
  <input name="scattering" type="float" nodename="crust_scattering_interp"/>
  <input name="scattering_color" type="color3" nodename="crust_albedo_interp"/>
  <input name="scattering_anisotropy" type="float" value="0.8"/>
  <input name="emission" type="float" value="0.0"/>
  <input name="emission_color" type="color3" value="0.0, 0.0, 0.0"/>
</standard_volume>

<!--
  In the Houdini/Karma pipeline, the crust_factor is baked into
  the VDB as a float grid named "crust_factor", and the MaterialX
  shader reads it via a Volume primvar to drive interpolation.
-->
```

### Step 5 -- Validate Dual-State Read

Render a scout pass with side or back lighting (not front lighting). The dual-state
read should be:

- **Surface:** Matte black, absorbs light, no visible scattering. The plume edge reads
  as a dark silhouette.
- **Interior (backlit):** Translucent grey, light passes through the body and reaches
  the camera. The ghost light effect is visible as a dim inner glow.
- **Transition:** Smooth, not abrupt. The crust blends into the interior over the
  `blend_width` range.

Front lighting alone cannot validate the dual-state shader because front lighting does
not reveal the interior scattering. Side or back lighting is required to see the ghost
light.

---

## Parameters

### Wedge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `crust_threshold` | float | 0.4 | 0.2 - 0.6 | Normalized gradient magnitude threshold for crust/interior boundary |
| `blend_width` | float | 0.05 | 0.02 - 0.15 | Half-width of smoothstep transition zone |
| `crust_absorption` | float | 1.0 | 0.8 - 1.0 | Absorption coefficient at surface (crust state) |
| `interior_scattering` | float | 0.8 | 0.5 - 0.95 | Scattering coefficient in interior |
| `scattering_anisotropy` | float | 0.8 | 0.6 - 0.9 | Henyey-Greenstein g parameter for forward scatter |

### Fixed Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Crust albedo | 0.02 | Matte black surface (near-zero reflectance) |
| Interior albedo | 0.85 | Translucent grey (high single-scatter albedo) |
| Crust scattering | 0.0 | No scattering at surface |
| Interior absorption | 0.1 | Low absorption in interior (light passes through) |

### Derived Parameters

| Parameter | Derivation | Description |
|-----------|-----------|-------------|
| `crust_norm` | `grad_mag / grad_max` | Normalized gradient magnitude [0, 1] |
| `crust_factor` | `smoothstep(threshold-blend, threshold+blend, crust_norm)` | Per-voxel crust/interior blend |

### Tier Behavior

| Tier | Behavior |
|------|----------|
| **Exhibition** | Full dual-state with anisotropy 0.8 (strong forward scatter) |
| **Study** | Single-state volume with anisotropy 0.35 (weak forward scatter) |
| **Sketch** | No volumetric shading -- density-only rendering |

---

## API Dependencies

| Dependency | Module | Function | Usage |
|------------|--------|----------|-------|
| Gradient | `numpy` | `np.gradient` | Density gradient for crust/interior classification |
| Smoothstep | (inline) | `smoothstep` | Hermite interpolation for crust factor |

---

## Anti-Patterns

### 1. The Hard Binary Transition

**Symptom:** The material snaps abruptly from matte black to translucent grey at a
visible isosurface. The transition is a hard edge, not a smooth blend. The plume has a
visible "shell" around a glowing interior.

**Cause:** Using a binary threshold (`if gradient > threshold: crust else: interior`)
instead of `smoothstep`. Binary transitions produce visible discontinuities that break
the volume illusion.

**Fix:** Use `smoothstep(threshold - blend_width, threshold + blend_width, crust_norm)`
to create a gradual transition. The `blend_width` = 0.05 (default) provides a 10% band
where crust and interior parameters are smoothly interpolated.

### 2. The Symmetric Scattering

**Symptom:** The interior scatters light equally in all directions. Backlit views show
no more interior glow than front-lit views. The ghost light effect is absent.

**Cause:** `scattering_anisotropy` set to 0.0 (isotropic). Isotropic scattering
distributes light equally in all directions, so the camera sees the same scattered
intensity regardless of lighting direction.

**Fix:** Set `scattering_anisotropy` = 0.8 (strong forward scatter). The Henyey-Greenstein
phase function at g=0.8 concentrates scattered light within ~30 degrees of the forward
direction. This means light entering the back of the plume preferentially exits toward
the camera -- the ghost light.

### 3. The Colored Interior

**Symptom:** The interior scattering introduces a color cast -- warm, cool, or any hue.
The achromatic soot language is violated. The interior glows with color instead of
neutral grey.

**Cause:** Setting `scattering_color` to a non-neutral RGB value. The interior albedo
of 0.85 must be achromatic: all three channels identical.

**Fix:** Set `scattering_color` = (0.85, 0.85, 0.85) in MaterialX. All channels equal.
The soot material is achromatic by definition -- it scatters all visible wavelengths
equally because carbonaceous particles have flat spectral response across the visible.

### 4. The Inverted Crust

**Symptom:** The plume interior is matte black and the surface is translucent. The volume
reads as a dark core surrounded by a glowing shell. The physical logic is reversed.

**Cause:** Swapping the crust and interior parameter assignments, or inverting the
`crust_factor` direction so that high gradient maps to interior instead of crust.

**Fix:** Verify: `crust_factor` = 1.0 at HIGH gradient (surface), 0.0 at LOW gradient
(interior). HIGH gradient = rapid density change = surface boundary = CRUST (absorptive).
LOW gradient = flat density = interior body = TRANSLUCENT (scattering).

---

## Validation Checklist

- [ ] Gradient magnitude computed from density field via `np.gradient`
- [ ] Crust factor uses `smoothstep` (not binary threshold)
- [ ] `blend_width` within 0.02 - 0.15 range (default 0.05)
- [ ] Surface (high gradient): absorption dominant, albedo 0.02, no scattering
- [ ] Interior (low gradient): scattering dominant, albedo 0.85, low absorption
- [ ] `scattering_anisotropy` = 0.8 for exhibition (strong forward scatter)
- [ ] Ghost light visible in backlit or side-lit scout render
- [ ] Transition smooth, not a hard shell or visible isosurface
- [ ] All albedo values achromatic (equal RGB channels)
- [ ] No color in interior scattering (neutral grey only)
- [ ] MaterialX `standard_volume` used for shader specification
- [ ] VDB exports `crust_factor` as named float grid for Houdini pipeline
- [ ] Study tier uses single-state volume with reduced anisotropy (0.35)
- [ ] Sketch tier uses no volumetric shading
