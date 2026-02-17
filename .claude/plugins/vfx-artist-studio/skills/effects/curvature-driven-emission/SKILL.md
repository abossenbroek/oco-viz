---
name: curvature-driven-emission
user-invocable: false
type: instruction
primary_owner: effects-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Curvature-Driven Emission -- Oxygen-at-Surface Combustion Glow

Reference: Industrial combustion -- oxygen reaches the fuel surface, and the reaction
glows. The emission is brightest where the volume boundary is most convoluted: at ridges,
folds, and turbulent edges where surface area exposes fuel to oxidizer. In the interior,
oxygen is consumed and emission dies. At smooth, flat surfaces, exposure is low and glow
is faint. At sharp curves and vortex cores, exposure is maximum and the volume pulses
with achromatic light.

> "Fire breathes at the surface. The interior is already ash."

---

## Principle

Emission intensity is modeled as a combustion proxy: `emission = fuel * oxygen *
emission_intensity`, where fuel is the density field and oxygen is a proxy derived
from the maximum of vorticity magnitude and surface curvature. High vorticity means
turbulent mixing brings fresh oxidizer; high curvature means large surface-area-to-volume
ratio exposes more fuel.

An arrhythmic temporal pulse modulates the emission using two incommensurable frequencies
-- `sin(2*pi*0.2*t) * sin(2*pi*0.05*t)` -- producing flicker that never repeats and never
synchronizes. The pulse creates the organic, breathing quality of real combustion.

MaterialX starting point: `standard_volume` with `emission_color` = (0.68, 0.68, 0.68) --
achromatic. The soot lookdev bible mandates no color in emission. The glow is grey light,
not orange flame.

---

## Procedure

### Step 1 -- Compute Vorticity Magnitude

Vorticity measures local rotation in the velocity field. High vorticity indicates
turbulent mixing zones where fresh oxidizer is being entrained. Use `curl_noise_3d`
as a proxy for vorticity in the pre-viz pipeline.

```python
import numpy as np
from oco_viz.plume.noise import curl_noise_3d

# Generate curl noise as vorticity proxy
curl_dx, curl_dy, curl_dz = curl_noise_3d(
    shape=density.shape,
    octaves=4,
    lacunarity=2.0,
    gain=0.5,
    seed=42,
)

# Vorticity magnitude = |curl|
vorticity_mag = np.sqrt(
    curl_dx.astype(np.float64)**2
    + curl_dy.astype(np.float64)**2
    + curl_dz.astype(np.float64)**2
).astype(np.float32)

# Normalize to [0, 1]
vort_max = vorticity_mag.max()
if vort_max > 0:
    vorticity_mag /= vort_max
```

### Step 2 -- Compute Surface Curvature

Curvature measures how sharply the density iso-surfaces bend. High curvature indicates
folds, ridges, and edges where surface area is large relative to volume -- exposing
more fuel to oxidizer.

```python
# Compute gradient of density
gz, gy, gx = np.gradient(density.astype(np.float64))
grad_mag = np.sqrt(gz**2 + gy**2 + gx**2)

# Compute divergence of normalized gradient = mean curvature proxy
grad_mag_safe = np.maximum(grad_mag, 1e-8)
nx_field = gx / grad_mag_safe
ny_field = gy / grad_mag_safe
nz_field = gz / grad_mag_safe

div_nx = np.gradient(nx_field, axis=2)  # d/dx
div_ny = np.gradient(ny_field, axis=1)  # d/dy
div_nz = np.gradient(nz_field, axis=0)  # d/dz

curvature = np.abs(div_nx + div_ny + div_nz).astype(np.float32)

# Normalize to [0, 1]
curv_max = curvature.max()
if curv_max > 0:
    curvature /= curv_max
```

### Step 3 -- Compute Oxygen Proxy and Emission

Combine vorticity and curvature into the oxygen proxy, then multiply by fuel (density)
and emission intensity to produce the emission field.

```python
# Oxygen = max(vorticity, curvature), weighted by curvature_weight
oxygen = np.maximum(
    vorticity_mag,
    curvature * curvature_weight,  # default 0.5
)

# Emission = fuel * oxygen * intensity
emission = density * oxygen * emission_intensity  # default 1.5
```

### Step 4 -- Apply Arrhythmic Temporal Pulse

Modulate emission with two incommensurable frequencies. The frequencies are chosen so
their ratio is irrational -- they never synchronize, producing organic flicker.

```python
import math

# Two incommensurable frequencies -- never repeat
pulse_a = math.sin(2.0 * math.pi * freq_a * time_index)  # default 0.2
pulse_b = math.sin(2.0 * math.pi * freq_b * time_index)  # default 0.05

# Combined pulse modulates emission amplitude
pulse = 1.0 + pulse_amplitude * pulse_a * pulse_b  # default amplitude 0.2
emission_pulsed = emission * pulse

np.maximum(emission_pulsed, 0.0, out=emission_pulsed)
```

### Step 5 -- Configure MaterialX Emission

The emission color is achromatic grey -- no warmth, no color. The achromatic soot
language uses grey-light combustion, not orange flame.

```xml
<!-- MaterialX standard_volume with achromatic emission -->
<standard_volume name="soot_emission">
  <input name="emission" type="float" value="1.0"/>
  <input name="emission_color" type="color3" value="0.68, 0.68, 0.68"/>
  <input name="density" type="float" value="1.0"/>
  <input name="absorption" type="float" value="0.8"/>
  <input name="scattering" type="float" value="0.2"/>
  <input name="scattering_anisotropy" type="float" value="0.6"/>
</standard_volume>
```

### Step 6 -- Validate Emission Distribution

Render a scout pass. Emission should:
- Concentrate at density edges and turbulent folds (high curvature/vorticity)
- Vanish in the dense interior (oxygen consumed)
- Vanish in empty space (no fuel)
- Pulse irregularly -- never a steady glow, never a rhythmic strobe
- Read as achromatic grey light, not colored flame

---

## Parameters

### Wedge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `emission_intensity` | float | 1.5 | 0.5 - 3.0 | Overall emission strength multiplier |
| `pulse_amplitude` | float | 0.2 | 0.05 - 0.6 | Strength of temporal pulse modulation |
| `freq_a` | float | 0.2 | 0.1 - 0.3 | First pulse frequency (cycles per frame) |
| `freq_b` | float | 0.05 | 0.03 - 0.08 | Second pulse frequency (incommensurable with freq_a) |
| `curvature_weight` | float | 0.5 | 0.0 - 1.0 | Curvature contribution to oxygen proxy (0 = vorticity only) |

### Derived Parameters

| Parameter | Derivation | Description |
|-----------|-----------|-------------|
| `oxygen` | `max(vorticity_mag, curvature * curvature_weight)` | Oxidizer availability proxy |
| `emission` | `density * oxygen * emission_intensity` | Raw emission field |
| `pulse` | `1 + pulse_amplitude * sin(2*pi*freq_a*t) * sin(2*pi*freq_b*t)` | Temporal modulation |

### Tier Behavior

| Tier | Behavior |
|------|----------|
| **Exhibition** | Full: curvature + vorticity + arrhythmic pulse |
| **Study** | Simplified: `emission = density * noise * emission_intensity` (no curvature, no pulse) |
| **Sketch** | Disabled -- no emission computed |

---

## API Dependencies

| Dependency | Module | Function | Usage |
|------------|--------|----------|-------|
| Curl noise | `src/oco_viz/plume/noise.py` | `curl_noise_3d` | Vorticity proxy via curl of potential fields |
| Gradient | `numpy` | `np.gradient` | Density gradient for curvature computation |
| Divergence | `numpy` | `np.gradient` | Divergence of normalized gradient for mean curvature |

---

## Anti-Patterns

### 1. The Colored Emission

**Symptom:** The emission glows orange, yellow, or any hue. The achromatic soot language
is violated. The plume reads as "fire" rather than "industrial combustion residue."

**Cause:** Setting `emission_color` to a warm or colored value. The lookdev bible
specifies achromatic emission: grey light from grey fuel combustion.

**Fix:** Set `emission_color` = (0.68, 0.68, 0.68) in MaterialX. All three channels
identical. No warmth, no coolness. The color of the emission is the color of the soot.

### 2. The Uniform Emission

**Symptom:** The entire plume glows uniformly. There is no spatial variation -- the
interior and the edges emit equally. The volume looks like a lightbulb, not a combustion
event.

**Cause:** Setting emission proportional to density alone without the oxygen proxy.
`emission = density * intensity` produces uniform glow. The oxygen proxy concentrates
emission at surfaces and turbulent zones.

**Fix:** Use `emission = density * oxygen * intensity` where `oxygen = max(vorticity,
curvature)`. This concentrates emission at the boundary where oxidizer is available.

### 3. The Linear Pulse

**Symptom:** The emission flickers rhythmically like a strobe or a candle. The flicker
has a visible period -- it repeats predictably. Real combustion flicker is aperiodic.

**Cause:** Using a single frequency for the pulse (`sin(2*pi*f*t)`). A single frequency
produces periodic flicker that the eye detects as mechanical.

**Fix:** Use two incommensurable frequencies multiplied together:
`sin(2*pi*0.2*t) * sin(2*pi*0.05*t)`. The product of two irrational-ratio frequencies
never repeats, producing organic flicker. Verify that `freq_a / freq_b` is not a simple
rational number.

### 4. The Overwhelming Emission

**Symptom:** Emission dominates the rendered volume. The density, scattering, and
absorption characteristics of the soot material are washed out by bright emission.
The plume looks like a neon sign.

**Cause:** `emission_intensity` set too high (> 3.0), or `pulse_amplitude` set too high
(> 0.6). Emission should be a subtle luminance detail, not the primary visual feature.

**Fix:** Start with `emission_intensity` = 1.5 and `pulse_amplitude` = 0.2. The emission
should be visible only upon careful inspection -- a faint internal glow at the edges, not
a beacon.

---

## Validation Checklist

- [ ] Emission concentrated at high-curvature and high-vorticity zones
- [ ] Emission vanishes in dense interior (oxygen consumed)
- [ ] Emission vanishes in empty space (no fuel)
- [ ] Temporal pulse uses two incommensurable frequencies
- [ ] Pulse never produces rhythmic or periodic flicker
- [ ] `emission_color` is achromatic: (0.68, 0.68, 0.68) -- no color
- [ ] `emission_intensity` within 0.5 - 3.0 range (default 1.5)
- [ ] `curvature_weight` balances curvature vs vorticity contribution
- [ ] Emission does not overpower density/scattering visual read
- [ ] Study tier uses simplified density*noise emission (no curvature)
- [ ] Sketch tier has emission fully disabled
- [ ] Vorticity computed via `curl_noise_3d` from `plume/noise.py`
- [ ] Curvature computed as divergence of normalized density gradient
