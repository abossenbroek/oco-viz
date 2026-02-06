---
name: density-to-dread
user-invocable: false
---

# Density-to-Dread -- Transfer Function as Emotional Instrument

The non-linear remapping of physical density values to visual and emotional
weight. This is NOT a color ramp. It drives density, absorption, AND emission
simultaneously. The transfer function is the single most consequential artistic
decision in volumetric rendering.

In VTK emission mode (`ShadeOff()`), the TF color IS the pixel color. There is
no lighting, no shading, no second chance. The TF must carry the entire
emotional architecture alone.

---

## Three Control Axes

### 1. Oppression

How much the volume presses down on the viewer.

| Parameter | Effect |
|-----------|--------|
| Opacity curve steepness | Steeper = substance appears sooner, more confrontational |
| Absorption coefficient | Higher = light dies faster inside the substance |
| Low-density threshold | Lower = oppressive (substance starts at lower density values) |
| Ramp onset | Earlier onset = the void is invaded sooner |

**Mapping:** Oppression 0.0 = substance barely visible. Oppression 1.0 = the
void itself feels contaminated.

### 2. Grit

Textural roughness of the substance at the perceptual level.

| Parameter | Effect |
|-----------|--------|
| Noise octave count | More octaves = finer granularity |
| High-frequency amplitude | Higher = sharper textural detail |
| Sample distance | Closer (grid_spacing/10) = grittier, resolves fine structure |
| Gaussian smoothing sigma | Lower = grittier (2.0 eliminates voxelization, 1.0 preserves grain) |

**Mapping:** Grit 0.0 = smooth, digital, unconvincing. Grit 1.0 = coal dust
under a microscope, every particle resolved.

### 3. Contamination

How much the "dirty near-white" pollutes the achromatic range.

| Parameter | Effect |
|-----------|--------|
| Peak luminance | Higher toward #c8c8c8 = more contaminated near-white |
| Emission intensity | Higher in dense regions = the substance glows with absorbed energy |
| Void-substance boundary | Sharper = contamination is sudden. Gradual = it creeps. |
| Exposure | 25.0 with falloff pushes contamination into visible range |

**Mapping:** Contamination 0.0 = clean separation between void and substance.
Contamination 1.0 = even the void feels polluted, the near-white is filthy.

---

## Transfer Function Architecture

### Color Control Points (minimum 14)

Linear grey ramp from #000000 to #c8c8c8. Fewer than 14 points creates visible
contour banding in the density-to-luminance mapping.

| Index | Density | Hex | Character |
|-------|---------|-----|-----------|
| 0 | 0.00 | #000000 | Pure void |
| 1 | 0.05 | #0d0d0d | First trace -- barely perceptible |
| 2 | 0.10 | #1a1a1a | Ghost wisps at periphery |
| 3 | 0.15 | #262626 | Threshold of visibility |
| 4 | 0.20 | #333333 | Diffuse haze begins |
| 5 | 0.30 | #4d4d4d | Structure emerges |
| 6 | 0.40 | #5c5c5c | Substance has form |
| 7 | 0.50 | #6b6b6b | Medium density -- weight visible |
| 8 | 0.60 | #7a7a7a | Dense particulate |
| 9 | 0.70 | #898989 | Heavy -- light suffocating |
| 10 | 0.75 | #939393 | Near-peak density |
| 11 | 0.80 | #9e9e9e | Peak structure |
| 12 | 0.90 | #b3b3b3 | Approaching contamination peak |
| 13 | 1.00 | #c8c8c8 | Dirty near-white -- never clean |

### Opacity Control Points (minimum 25)

Shaped S-curve with specific zone behavior:

| Zone | Density Range | Opacity Range | Behavior |
|------|--------------|---------------|----------|
| Void | 0.00 - 0.05 | 0.00 - 0.00 | Absolute zero -- void breathes |
| Trace | 0.05 - 0.15 | 0.00 - 0.02 | Near-zero -- peripheral ghosts |
| Ramp onset | 0.15 - 0.25 | 0.02 - 0.10 | The confrontation begins |
| Steep ramp | 0.25 - 0.40 | 0.10 - 0.35 | Rapid opacity increase |
| Dense | 0.40 - 0.60 | 0.35 - 0.55 | Building weight |
| Heavy | 0.60 - 0.80 | 0.55 - 0.75 | Light suffocating, never opaque |
| Peak | 0.80 - 1.00 | 0.75 - 0.85 | Plateau at max (0.85 exhibition) |

---

## Presets

| Preset | Oppression | Grit | Contamination | Character |
|--------|-----------|------|---------------|-----------|
| **Industrial Pall** | High | Medium | High | Choking smog over a city. Relentless, dirty, inescapable. Low-density threshold at 0.08 -- the void itself is contaminated. |
| **Volcanic Plinian** | Medium | High | Medium | Explosive pyroclastic particulate. Sharp-edged, aggressive, clumped. Steep ramp with high-frequency noise. |
| **Geological Seep** | Low | Low | Low | Ancient carbon emerging from earth. Slow, heavy, compressed by geological time. Gradual ramp, smooth transitions. |
| **Anthropocene Peak** | Maximum | Maximum | Maximum | All controls at maximum. Data confrontation. The viewer cannot escape the substance. Every pixel contaminated. |

---

## Anti-Patterns

- **The Ramp Wall** -- opacity jumps from 0 to 0.5 in a narrow density band. Creates a visible shell instead of depth.
- **The Ghost** -- max opacity below 0.3. Substance has no weight, no conviction.
- **The Blob** -- uniform opacity across all densities. No internal structure, no depth reading.
- **Clean White** -- peak luminance at #ffffff. Destroys the contamination concept.
- **Banding** -- fewer than 14 color points or 25 opacity points. Visible contouring in the density field.
