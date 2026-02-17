---
name: boundary-dissolution
user-invocable: false
type: instruction
primary_owner: matte-artist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Boundary Dissolution -- Where the Image Lives

The boundary dissolves rather than terminates. The plume-void boundary is where the
image's character lives -- it can be crisp (industrial, mechanical), wispy (atmospheric,
organic), or crumbling (ashen, decaying). The boundary quality defines the emotional
read of the entire frame. A hard-clipped boundary reads as synthetic; a dissolving
boundary reads as physical; a crumbling boundary reads as entropic.

> "The edge is the most expressive part of the form." -- Henry Moore

---

## Principle

The plume-void boundary is not a technical artifact -- it is the primary expressive
surface of the image. When a viewer looks at a CO2 plume floating in the void, they
are looking at the boundary. The dense core is opaque and reveals little; the void is
black and reveals nothing. The boundary is where density transitions from visible to
invisible, where the plume's material quality is most apparent, where lighting reveals
form, and where the emotional character of the shot is communicated.

Four boundary types define the vocabulary:

**Crisp** -- High-density cutoff with a sharp transition. The plume ends abruptly, as
if cut by a blade. This reads as industrial, mechanical, artificial. Appropriate for
shots that emphasize the manufactured nature of CO2 emissions.

**Wispy** -- Exponential falloff over multiple voxels. The plume thins gradually into
transparent wisps that dissolve into the void. This reads as atmospheric, organic,
natural. The default boundary type for most exhibition work.

**Crumbling** -- Stochastic ash culling removes density at the boundary in a pattern
that reads as particulate shedding. Small clumps of density detach from the main mass
and dissolve independently. This reads as ashen, decaying, entropic.

**Dissolving** -- The paper grain manifold erodes the boundary with a static noise
pattern that reads as material texture. The plume dissolves into the tooth of the
virtual paper. This reads as crafted, printerly, handmade.

---

## Procedure

### Step 1 -- Select Boundary Type from Shot Design

The boundary type is specified by the matte-artist as part of the void design. Each
shot should have one dominant boundary type, though the boundary quality may vary
around the perimeter of the plume:

| Boundary Type | Emotional Read | Falloff Curve | Width (voxels) |
|-------------- |---------------|---------------|----------------|
| Crisp | Industrial, mechanical | Step function | 1-3 |
| Wispy | Atmospheric, organic | Exponential | 8-20 |
| Crumbling | Ashen, entropic | Stochastic | 5-15 |
| Dissolving | Printerly, crafted | Noise-driven | 10-30 |

### Step 2 -- Specify Falloff Curve

The falloff curve defines how density transitions from full value to zero at the
boundary:

**Step function** (for crisp): Density drops from its interior value to zero within
1-3 voxels. The transition is nearly binary -- the plume either exists or it does not.

```
falloff(d) = 1.0 if d >= threshold else 0.0
```

**Exponential** (for wispy): Density decreases exponentially from the interior value,
producing the characteristic atmospheric haze at the plume edge:

```
falloff(d) = exp(-falloff_rate * distance_from_core)
```

**Stochastic** (for crumbling): Density is probabilistically culled at the boundary.
Each voxel in the boundary zone has a chance of being zeroed proportional to its
distance from the core:

```
falloff(d) = d * (noise(position) > cull_threshold(distance))
```

**Noise-driven** (for dissolving): The paper grain manifold subtracts a static noise
field from the density, producing a boundary that follows the grain pattern:

```
falloff(d) = max(0, d - grain_amplitude * grain_field)
```

### Step 3 -- Define Boundary Width

The boundary width controls how many voxels participate in the transition. Wider
boundaries produce softer, more atmospheric edges; narrower boundaries produce harder,
more mechanical edges:

| Boundary Type | Min Width (voxels) | Max Width (voxels) | Default |
|---------------|-------------------|-------------------|---------|
| Crisp | 1 | 3 | 2 |
| Wispy | 8 | 20 | 12 |
| Crumbling | 5 | 15 | 8 |
| Dissolving | 10 | 30 | 20 |

### Step 4 -- Specify Spatial Variation

The boundary quality need not be uniform around the plume perimeter. The matte-artist
may specify zones where different boundary types apply:

| Zone | Typical Boundary | Rationale |
|------|-----------------|-----------|
| Emission point (base) | Crisp | Dense, high-velocity flow at source |
| Leeward edge | Wispy | Wind shear stretches density into wisps |
| Upper extent | Crumbling | Buoyancy-driven ash shedding |
| Downwind tail | Dissolving | Diffusion-dominated density decay |

### Step 5 -- Coordinate with Effects-TD

The boundary-dissolution skill specifies the DESIGN -- what the boundary should look
and feel like. The implementation is the responsibility of the effects-td, who translates
the design specification into VEX/VOP code, transfer function modifications, or
post-processing operations.

The handoff from matte-artist to effects-td uses the `void_design_delivery` schema
and must include: boundary type per zone, falloff curve parameters, boundary width,
and reference images showing the intended look.

---

## Parameters

### Boundary Type Parameters

| Parameter | Type | Default | Allowed Values | Description |
|-----------|------|---------|----------------|-------------|
| `boundary_type` | string | wispy | crisp / wispy / crumbling / dissolving | Primary boundary dissolution type |
| `falloff_curve` | string | exponential | linear / exponential / step / stochastic / noise | Mathematical falloff function |
| `boundary_width_voxels` | int | 12 | 1 - 30 | Number of voxels in boundary transition |

### Crisp Boundary Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `crisp_threshold` | float | 0.1 | 0.01 - 0.5 | Density value below which the plume is cut to zero |
| `crisp_transition_voxels` | int | 2 | 1 - 3 | Width of the step transition |

### Wispy Boundary Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `wispy_falloff_rate` | float | 0.3 | 0.1 - 1.0 | Exponential decay rate per voxel |
| `wispy_min_density` | float | 0.001 | 0.0001 - 0.01 | Density below which wisps are clamped to zero |

### Crumbling Boundary Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `ash_density` | float | 0.15 | 0.05 - 0.3 | Density of detached ash particles |
| `cull_probability` | float | 0.6 | 0.3 - 0.9 | Probability of culling at boundary midpoint |
| `ash_size_voxels` | int | 3 | 1 - 8 | Typical size of detached ash clumps |

### Dissolving Boundary Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_amplitude` | float | 0.05 | 0.02 - 0.12 | From paper-grain-manifold skill |
| `grain_octaves` | int | 8 | 6 - 10 | From paper-grain-manifold skill |
| `grain_seed` | int | 7777 | any | Fixed per shot, from paper-grain-manifold |

---

## Anti-Patterns

### 1. The Hard Clip Boundary

**Symptom:** The plume edge is a crisp, uniform contour around the entire perimeter.
The plume looks like a solid object silhouetted against the void rather than a
volumetric atmospheric phenomenon.

**Cause:** Using a binary threshold for the entire plume boundary without spatial
variation or without intentionally choosing the crisp boundary type. Often caused by
a transfer function opacity curve that goes from zero to full opacity too quickly.

**Fix:** If the crisp boundary was intentional, verify it is restricted to zones where
it is motivated (emission point, high-velocity flow). If it was not intentional, switch
to a wispy boundary type with exponential falloff. The default boundary for most
exhibition work should be wispy with 8-20 voxel transition width.

### 2. Uniform Boundary Around Entire Plume

**Symptom:** The boundary quality is identical in all directions -- the same falloff
rate, the same width, the same character at the base, the sides, and the top. The
plume looks like a symmetric blob rather than a wind-shaped atmospheric mass.

**Cause:** Applying a single boundary type globally without considering the physical
forces acting on different parts of the plume (emission velocity at base, wind shear
on leeward side, buoyancy at top, diffusion in the tail).

**Fix:** Vary boundary quality around the perimeter. Use the spatial variation
guidelines in Step 4 as a starting point. The emission point should be crisper (high
velocity), the leeward edge should be wispier (wind stretching), and the upper extent
may crumble (ash shedding).

### 3. Boundary Disconnected from Effects Implementation

**Symptom:** The matte-artist specifies a crumbling boundary, but the rendered result
shows a wispy boundary because the effects-td implemented exponential falloff instead
of stochastic culling. Or, the boundary design exists only as a verbal description
with no parameters that the effects-td can implement.

**Cause:** The design-implementation handoff lacks specificity. The matte-artist
described the feeling but did not provide the boundary_type, falloff_curve,
boundary_width, and per-zone variation that the effects-td needs to implement.

**Fix:** Use the `void_design_delivery` schema for the handoff. Include: boundary
type, falloff curve, all relevant parameters, and reference images showing the
intended look. The matte-artist specifies WHAT; the effects-td implements HOW.

### 4. Boundary Width Mismatch with Resolution

**Symptom:** Boundary dissolution looks correct at scout resolution (128 cubed) but
collapses to a hard edge at final resolution (1024 cubed), or vice versa. The boundary
width in voxels does not scale with resolution.

**Cause:** Specifying boundary width in absolute voxels without considering that voxel
count changes with resolution. A 12-voxel boundary at 128 cubed occupies 9.4% of the
volume; at 1024 cubed it occupies 1.2%.

**Fix:** Specify boundary width in world-space units (meters) and derive the voxel count
from the resolution. A 1-meter boundary width is 12.8 voxels at 128 cubed and 102.4
voxels at 1024 cubed, maintaining the same physical boundary character across tiers.

---

## Validation Checklist

- [ ] Boundary type explicitly specified per shot (crisp / wispy / crumbling / dissolving)
- [ ] Falloff curve matches boundary type specification
- [ ] Boundary width appropriate for the chosen type (1-3 for crisp, 8-20 for wispy, etc.)
- [ ] Spatial variation specified -- boundary is not uniform around entire perimeter
- [ ] Boundary width specified in world-space units, not only voxels
- [ ] Boundary character consistent across resolution tiers (scout, preview, final)
- [ ] Handoff to effects-td uses void_design_delivery schema with all parameters
- [ ] Reference images provided for the intended boundary look
- [ ] Boundary quality serves the shot's emotional intent (documented in shot brief)
- [ ] No hard clip where wispy was specified (check transfer function opacity curve)
- [ ] Ash density, cull probability, and grain parameters within specified ranges
- [ ] Boundary dissolution coordinated with void quality (from void-design skill)
