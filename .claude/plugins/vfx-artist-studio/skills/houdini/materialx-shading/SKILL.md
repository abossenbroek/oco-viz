---
name: materialx-shading
user-invocable: false
type: instruction
primary_owner: houdini-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# MaterialX Shading -- standard_volume Shader Authoring for the Soot Aesthetic

The Soot visual language demands a dual-state volumetric shader: matte black crust at
high-gradient surfaces, translucent scattering interior at low-gradient regions. This
shader is authored in MaterialX using the `standard_volume` node, the only volume
shading model supported by both Karma XPU and the broader VFX interchange ecosystem.
The shader encodes the Soot Crust behavior from the lookdev bible (Technique 6) into
a production-ready MaterialX graph.

> "The crust is where the plume meets the void. It must be matte black, absolutely."

---

## Principle

MaterialX `standard_volume` provides physically-based volume shading with absorption,
scattering, and emission channels. The Soot Crust shader uses the density gradient
magnitude to drive a smooth blend between two material states: a near-black absorptive
crust (high gradient, at plume boundaries) and a translucent grey scattering interior
(low gradient, deep within the plume). Emission is achromatic -- always `(0.68, 0.68, 0.68)`
matching the exhibition transfer function peak. No color is ever introduced.

---

## Procedure

### Step 1 -- Define the Crust Factor

The crust factor is a per-voxel scalar derived from the density gradient:

```
crust = |grad(density)|
crust_norm = crust / percentile(crust, 95)
crust_factor = smoothstep(threshold - blend_width, threshold + blend_width, crust_norm)
```

| Variable | Description |
|----------|-------------|
| `crust` | Raw gradient magnitude |
| `crust_norm` | Normalized to [0, ~1] using 95th percentile |
| `crust_factor` | 0 = interior, 1 = crust (smoothly interpolated) |

### Step 2 -- Configure Dual-State Parameters

The shader blends between two parameter sets driven by `crust_factor`:

| Parameter | Interior (crust_factor=0) | Crust (crust_factor=1) |
|-----------|--------------------------|----------------------|
| Absorption | 0.1 | 1.0 |
| Scattering | 0.8, 0.8, 0.8 | 0.0, 0.0, 0.0 |
| Scattering anisotropy | 0.8 (forward) | 0.0 (irrelevant, no scattering) |
| Emission color | 0.68, 0.68, 0.68 | 0.0, 0.0, 0.0 |
| Albedo (effective) | 0.85 | 0.02 |

### Step 3 -- Configure Scattering Anisotropy

Scattering anisotropy controls the Henyey-Greenstein phase function:

| Value | Behavior | Visual Effect |
|-------|----------|---------------|
| 0.0 | Isotropic | Flat, no directional depth |
| 0.3-0.5 | Mild forward | Study-tier scattering |
| 0.6-0.7 | Moderate forward | Visible light penetration |
| 0.8-0.9 | Strong forward | Exhibition "ghost light" effect |

The exhibition tier uses 0.8 for strong forward scattering. Light enters the translucent
interior and bleeds through, but is blocked by the opaque crust. This creates visible
depth cues even in achromatic imagery.

### Step 4 -- Configure Emission

Emission is driven by the curvature-driven emission field from Technique 3 of the lookdev
bible. The emission color is always achromatic:

| Property | Value | Rationale |
|----------|-------|-----------|
| Color | (0.68, 0.68, 0.68) | Matches exhibition TF peak color |
| Intensity | Driven by emission field | Varies per-voxel from curvature computation |
| Blackbody | Achromatic only | No Kelvin-to-RGB color mapping for Soot |

### Step 5 -- Validate the Shader

Before rendering:

1. Render a single frame and verify the crust reads as matte black.
2. Verify the interior shows translucent grey with visible depth.
3. Verify emission appears only at surfaces and vortex cores.
4. Verify no color is present (all channels equal, fully achromatic).
5. Compare against lookdev bible Technique 6 lock criteria.

---

## Verified Code Templates

### standard_volume MTLX Definition

```xml
<?xml version="1.0" encoding="UTF-8"?>
<materialx version="1.38">

  <!-- Soot Crust: dual-state volume shader -->
  <nodegraph name="soot_crust_graph">

    <!-- Crust factor input (computed upstream in VEX/VOPs) -->
    <input name="crust_factor" type="float" value="0.0"
           doc="0=interior, 1=crust. Driven by smoothstep of gradient magnitude." />

    <!-- Emission field input (from Technique 3) -->
    <input name="emission_field" type="float" value="0.0"
           doc="Curvature-driven emission intensity." />

    <!-- Parameters -->
    <input name="crust_threshold" type="float" value="0.4" uimin="0.2" uimax="0.6" />
    <input name="blend_width" type="float" value="0.05" uimin="0.02" uimax="0.15" />
    <input name="scattering_anisotropy" type="float" value="0.8" uimin="0.6" uimax="0.9" />

    <!-- Interpolated absorption: lerp(0.1, 1.0, crust_factor) -->
    <mix name="absorption_blend" type="float">
      <input name="fg" type="float" value="1.0" />
      <input name="bg" type="float" value="0.1" />
      <input name="mix" type="float" interfacename="crust_factor" />
    </mix>

    <!-- Interpolated scattering: lerp(0.8, 0.0, crust_factor) -->
    <mix name="scattering_blend" type="color3">
      <input name="fg" type="color3" value="0.0, 0.0, 0.0" />
      <input name="bg" type="color3" value="0.8, 0.8, 0.8" />
      <input name="mix" type="float" interfacename="crust_factor" />
    </mix>

    <!-- Emission: achromatic, only in interior -->
    <multiply name="emission_masked" type="color3">
      <input name="in1" type="color3" value="0.68, 0.68, 0.68" />
      <input name="in2" type="float" interfacename="emission_field" />
    </multiply>
    <mix name="emission_blend" type="color3">
      <input name="fg" type="color3" value="0.0, 0.0, 0.0" />
      <input name="bg" type="color3" nodename="emission_masked" />
      <input name="mix" type="float" interfacename="crust_factor" />
    </mix>

  </nodegraph>

  <!-- Final standard_volume shader -->
  <standard_volume name="soot_crust" type="volumeshader">
    <input name="absorption" type="float" nodename="soot_crust_graph/absorption_blend" />
    <input name="scattering" type="color3" nodename="soot_crust_graph/scattering_blend" />
    <input name="scattering_anisotropy" type="float" value="0.8" />
    <input name="emission" type="float" value="1.0" />
    <input name="emission_color" type="color3" nodename="soot_crust_graph/emission_blend" />
  </standard_volume>

</materialx>
```

### Crust Factor Computation in VEX

```c
// VEX wrangle: compute crust_factor from density gradient
// Run on VDB points or in a Volume VOP.

vector grad_d = volumegradient(0, "density", @P);
float grad_mag = length(grad_d);

// Normalize against 95th percentile (pre-computed, passed as channel)
float grad_max = ch("grad_max");
float crust_norm = clamp(grad_mag / grad_max, 0, 1);

// Smoothstep blend
float threshold = ch("crust_threshold");  // default 0.4
float blend = ch("blend_width");          // default 0.05
float crust_factor = smooth(threshold - blend, threshold + blend, crust_norm);

f@crust_factor = crust_factor;
```

### Hython MaterialX Assignment

```python
"""Assign MaterialX soot_crust shader to a volume prim via Hython."""
from __future__ import annotations

from pxr import Usd, UsdShade  # type: ignore[import-untyped]


def assign_soot_crust_material(
    stage: Usd.Stage,
    volume_prim_path: str,
    mtlx_file: str,
) -> None:
    """Bind the Soot Crust MaterialX shader to a volume prim.

    Parameters
    ----------
    stage : Usd.Stage
        Target USD stage.
    volume_prim_path : str
        Path to the volume prim (e.g. "/World/Volumes/co2_plume").
    mtlx_file : str
        Path to the MaterialX .mtlx file.
    """
    # Define material prim
    mat_path = "/World/Materials/soot_crust"
    material = UsdShade.Material.Define(stage, mat_path)

    # Reference the MaterialX file
    material_prim = stage.GetPrimAtPath(mat_path)
    material_prim.GetReferences().AddReference(mtlx_file)
    material_prim.SetCustomDataByKey("purpose", "Soot Crust dual-state volume shader")
    material_prim.SetCustomDataByKey("created_by", "oco-viz/houdini-td")

    # Bind material to volume
    volume_prim = stage.GetPrimAtPath(volume_prim_path)
    binding = UsdShade.MaterialBindingAPI.Apply(volume_prim)
    binding.Bind(material)
```

---

## Parameters

### Soot Crust Shader Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `crust_threshold` | float | 0.4 | 0.2 - 0.6 | Gradient magnitude cutoff for crust state |
| `blend_width` | float | 0.05 | 0.02 - 0.15 | Smoothstep transition width |
| `scattering_anisotropy` | float | 0.8 | 0.6 - 0.9 | Henyey-Greenstein forward scattering |
| `crust_absorption` | float | 1.0 | 0.8 - 1.0 | Absorption coefficient for crust state |
| `interior_absorption` | float | 0.1 | 0.05 - 0.2 | Absorption coefficient for interior state |
| `interior_scattering` | float | 0.8 | 0.5 - 0.95 | Scattering coefficient for interior state |
| `emission_color` | color3 | 0.68, 0.68, 0.68 | achromatic only | Emission color (must be achromatic) |

### Wedge Parameters (from Lookdev Bible Technique 6)

| Parameter | Wedge Range | Steps | Lock Criterion |
|-----------|-------------|-------|----------------|
| `crust_threshold` | 0.2 - 0.6 | 5 | Visible crust at boundaries, not interior |
| `blend_width` | 0.02 - 0.15 | 4 | Smooth transition, no hard edge |
| `scattering_anisotropy` | 0.6 - 0.9 | 5 | Forward scattering creates ghost light |
| `crust_absorption` | 0.8 - 1.0 | 3 | Surfaces read as matte black |
| `interior_scattering` | 0.5 - 0.95 | 4 | Visible depth, translucent grey |

---

## Anti-Patterns

### 1. The Colored Emission

**Symptom:** The plume glows orange, blue, or any color other than achromatic grey.
The Soot aesthetic is broken. The plume looks like a video game fire effect.

**Cause:** Setting `emission_color` to a non-achromatic value, or using Kelvin-to-RGB
blackbody mapping. The Soot visual language explicitly forbids color.

**Fix:** Emission color is always `(0.68, 0.68, 0.68)` or darker. All three channels
must be equal. The emission field modulates intensity, not hue. If a render shows any
color in the emission pass, the shader is wrong.

### 2. The Linear Scattering

**Symptom:** The volume looks flat and lifeless. There is no sense of depth or internal
structure. Light passes through uniformly without creating directional cues.

**Cause:** Scattering anisotropy set to 0.0 (isotropic) or too low. Without forward
scattering, there is no directional light transport and no "ghost light" effect.

**Fix:** Set `scattering_anisotropy` to 0.6-0.9 for exhibition tier (default 0.8).
This creates strong forward scattering where light bleeds through the translucent
interior but is blocked by the opaque crust. The resulting depth cues are critical
for the achromatic aesthetic where color cannot provide depth information.

### 3. The Missing Crust State

**Symptom:** The entire volume is uniformly translucent. There is no matte black
surface, no visible boundary between plume and void. The plume looks like fog, not
soot.

**Cause:** The crust factor is not computed or not connected to the shader. The shader
operates in interior state everywhere.

**Fix:** Compute `crust_factor` from the density gradient. Verify it ranges from 0
(interior) to 1 (crust). Connect it to drive the absorption/scattering blend.
Visually verify: plume boundaries should be opaque matte black, interior should be
translucent grey with visible depth.

### 4. The Constant Absorption

**Symptom:** The volume is uniformly dark or uniformly bright. There is no variation
in opacity across the plume. Dense and sparse regions look the same.

**Cause:** Using a constant absorption coefficient instead of density-driven absorption.
The shader ignores the density field.

**Fix:** Absorption must vary with the crust factor: high (1.0) at surfaces where the
crust is opaque, low (0.1) in the interior where light should penetrate. The density
field itself modulates the effective opacity through the volume rendering integral.

---

## Validation Checklist

- [ ] Emission color is achromatic: all three channels equal (0.68, 0.68, 0.68)
- [ ] No color present in any render pass (emission, scatter, beauty)
- [ ] Crust factor computed from density gradient magnitude
- [ ] Crust factor normalized against 95th percentile gradient
- [ ] Smoothstep transition between crust and interior states
- [ ] Crust state: absorption near 1.0, scattering near 0.0, matte black appearance
- [ ] Interior state: absorption near 0.1, scattering near 0.8, translucent grey
- [ ] Scattering anisotropy set to 0.8 for exhibition (forward scattering)
- [ ] Ghost light effect visible: light bleeds through interior, blocked by crust
- [ ] Emission appears only at surfaces and vortex cores (Technique 3)
- [ ] All shader parameters within lookdev bible wedge ranges
- [ ] MaterialX file validates against MaterialX 1.38 schema
- [ ] Shader renders correctly in Karma XPU without fallback
