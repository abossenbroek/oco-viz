---
name: aces-ocio
user-invocable: false
type: instruction
primary_owner: colorist
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# ACES / OCIO — Color Management for Exhibition-Grade Delivery

ACES is the law. ACEScg is the working space. No exceptions. Every pixel in the oco-viz
pipeline lives in a defined color space from the moment it is generated to the moment it
reaches the display. Undocumented color transforms are pipeline-breaking defects. If you
cannot name the input space, the working space, and the output transform for every image,
the color pipeline is broken.

> "If you don't know what color space you're in, you're in the wrong one."

---

## Principle

The Academy Color Encoding System (ACES) provides a scene-referred, wide-gamut color
framework that preserves the full dynamic range of rendered imagery from VTK generation
through final exhibition output. ACEScg (AP1 primaries, linear encoding) is the working
space for all compositing, grading, and rendering operations. OpenColorIO (OCIO) is the
configuration layer that manages all color space conversions.

Every color transform in the pipeline must be annotated with `from_space` and `to_space`.
Color space provenance is not optional metadata — it is the mechanism by which the
pipeline guarantees that a rendered pixel on the artist's monitor matches the pixel on
the exhibition display.

---

## Procedure

### Step 1 — Configure OCIO Environment

The oco-viz pipeline uses a project OCIO config that defines all required color spaces,
input transforms, and view transforms:

```yaml
ocio_profile_version: 2.1

environment:
  OCIO: /path/to/oco_viz_config.ocio

search_path:
  - luts

roles:
  scene_linear: ACEScg
  compositing_log: ACEScct
  color_timing: ACEScct
  data: Raw
  default: ACEScg
```

### Step 2 — Define Color Spaces

The pipeline requires these color spaces:

| Color Space | Primaries | Transfer | Use |
|-------------|-----------|----------|-----|
| ACEScg | AP1 | Linear | Working space — all rendering and compositing |
| ACEScct | AP1 | Log (ACEScct curve) | Color timing / CDL adjustments |
| ACES2065-1 | AP0 | Linear | Archival interchange format |
| sRGB | Rec.709 | sRGB EOTF | Input from web assets, display output |
| Rec.709 | Rec.709 | BT.1886 | Broadcast display output |
| Raw | -- | None | Data passes (depth, motion vectors, masks) |

### Step 3 — Define Input Transforms

Every source of color data entering the pipeline must be tagged with an input transform:

| Source | Input Space | Transform | Notes |
|--------|-------------|-----------|-------|
| VTK render output | Linear (scene-referred) | ACEScg (identity) | VTK renders in linear |
| Reference photographs | sRGB | sRGB to ACEScg | Web images are sRGB |
| HDRI environments | ACEScg or ACES2065-1 | Varies | Check HDRI metadata |
| Film scans | LogC / Print Density | Per-stock transform | Requires film emulation LUT |

### Step 4 — Define View Transforms

View transforms convert from the working space to the display space:

| View Transform | Target Display | Use |
|----------------|----------------|-----|
| ACES Output Transform (sRGB) | sRGB monitor | Artist workstation review |
| ACES Output Transform (P3-D65) | DCI-P3 / HDR display | Exhibition projection |
| Raw | None | Technical inspection (linear values) |
| SHIFT Process (film emulation) | sRGB with film character | Creative review with emulation |

### Step 5 — Annotate Color Space Provenance

Every image file, every render pass, every compositing node must carry color space
provenance metadata:

```yaml
color_provenance:
  from_space: ACEScg
  to_space: sRGB
  transform: "ACES Output Transform (sRGB)"
  ocio_config: "oco_viz_config.ocio"
  timestamp: "2026-02-15T14:30:00Z"
```

If an image lacks provenance, it must be treated as unknown color space and flagged for
investigation before it enters any compositing operation.

---

## OCIO Config Structure

### Working Space Definition

```yaml
colorspaces:
  - !<ColorSpace>
    name: ACEScg
    family: ACES
    description: "ACEScg (AP1 primaries, linear). Working space."
    isdata: false
    encoding: scene-linear
    allocation: lg2
    allocationvars: [-12, 6]
```

### Input Transform Example

```yaml
  - !<ColorSpace>
    name: sRGB - Texture
    family: Input
    description: "sRGB input for texture and reference images."
    isdata: false
    encoding: sdr-video
    from_scene_reference: !<GroupTransform>
      children:
        - !<ColorSpaceTransform> {src: ACES2065-1, dst: ACEScg}
    to_scene_reference: !<BuiltinTransform> {style: sRGB_to_ACES2065-1}
```

### View Transform Example

```yaml
displays:
  sRGB:
    - !<View>
      name: ACES 1.0 - SDR Video
      view_transform: ACES-OUTPUT - SDR-VIDEO - ACES 1.0
      display_colorspace: sRGB - Display

  P3-D65:
    - !<View>
      name: ACES 1.0 - SDR Cinema
      view_transform: ACES-OUTPUT - SDR-CINEMA - ACES 1.0
      display_colorspace: P3-D65 - Display
```

### Film Emulation View Transform (SHIFT Process)

```yaml
  - !<View>
    name: SHIFT Process
    view_transform: !<GroupTransform>
      children:
        - !<FileTransform> {src: shift_base.spi3d}
        - !<ColorSpaceTransform> {src: ACEScg, dst: sRGB - Display}
    display_colorspace: sRGB - Display
```

---

## Parameters

### Working Space Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `working_space` | string | ACEScg | Working color space (always ACEScg) |
| `primaries` | string | AP1 | Color space primaries |
| `encoding` | string | linear | Transfer function (always linear for working) |
| `white_point` | string | D65 | Illuminant white point |

### Dynamic Range Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `dynamic_range_stops` | int | 16 | 14 - 20 | Minimum scene-referred dynamic range |
| `exposure_range_min` | float | -6.0 | -12.0 - 0.0 | Minimum log2 exposure in scene |
| `exposure_range_max` | float | 6.0 | 0.0 - 10.0 | Maximum log2 exposure in scene |
| `highlight_headroom` | float | 2.0 | 1.0 - 4.0 | Stops above mid-gray before clipping |

### Gamut Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `gamut_boundary_check` | bool | true | -- | Warn on values outside ACEScg gamut |
| `negative_value_policy` | string | clamp | clamp / preserve | How to handle negative values |
| `max_scene_value` | float | 16.0 | 1.0 - 65504.0 | Maximum scene-referred value |

### Display Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `primary_display` | string | sRGB | Primary artist review display |
| `exhibition_display` | string | P3-D65 | Exhibition target display |
| `hdr_display` | string | Rec.2020-ST2084 | Optional HDR display |
| `film_emulation_lut` | string | shift_base.spi3d | Film emulation LUT path |

---

## Anti-Patterns

### 1. The sRGB Pipeline

**Symptom:** All rendering, compositing, and grading is performed in sRGB. Colors clip
at 1.0, highlights lose detail, dark tones quantize visibly. The pipeline has 8 stops of
dynamic range instead of 16+.

**Cause:** Using sRGB as the working space because it "looks correct on the monitor."
sRGB is a display-referred format with gamma encoding — it is designed for output, not
for computation.

**Fix:** Switch working space to ACEScg. All rendering and compositing in linear, all
grading in ACEScct. Apply the sRGB view transform only at display time. This preserves
14+ stops of dynamic range through the entire pipeline.

### 2. The Undocumented Transform

**Symptom:** An image looks "wrong" — too dark, too saturated, or color-shifted — but
nobody can identify where the error occurred. The image passed through multiple tools
and nodes without color space annotations.

**Cause:** Color transforms applied without `from_space` / `to_space` annotation. The
pipeline becomes a guessing game about what space each image is in.

**Fix:** Every transform must be annotated. Every image file must carry color provenance
metadata. If an image has no provenance, it is treated as unknown and flagged. This is
not bureaucracy — it is the mechanism by which color accuracy is maintained across tools,
machines, and time.

### 3. The Clipped Gamut

**Symptom:** Highlights snap to white or saturated colors lose their hue when viewed on
a wide-gamut display. Values that looked fine on an sRGB monitor are out-of-gamut for
P3-D65 or Rec.2020.

**Cause:** Working with values that exceed the ACEScg gamut boundary without checking or
preserving them. Or, applying a view transform that clips values above 1.0 instead of
compressing them gracefully.

**Fix:** Enable gamut boundary checking. Use the ACES Output Transform which includes
gamut mapping and highlight roll-off. Never hard-clip values — the ACES RRT/ODT system
handles the mapping from scene-referred to display-referred with perceptual preservation.

### 4. The Double Transform

**Symptom:** Images appear over-corrected — too contrasty, color-shifted, or with
crushed blacks. The "look" is applied twice because two tools in the pipeline both apply
the same view transform.

**Cause:** One tool converts from ACEScg to sRGB for display, then the output is fed
into another tool that assumes sRGB input and converts to ACEScg, then displays through
another sRGB transform — effectively applying the transform twice.

**Fix:** Establish clear handoff points. Compositing output is always ACEScg EXR. The
view transform is applied once, at display time, by the viewing application. No
intermediate file should contain display-referred data unless explicitly labeled.

---

## Validation Checklist

- [ ] OCIO config file exists and is valid
- [ ] Working space is ACEScg (AP1, linear)
- [ ] White point is D65
- [ ] Dynamic range is 14+ stops
- [ ] All required color spaces defined: ACEScg, ACEScct, ACES2065-1, sRGB, Raw
- [ ] All input transforms documented with from_space / to_space
- [ ] All view transforms documented with target display
- [ ] Film emulation LUT (SHIFT Process) configured and tested
- [ ] Every image in the pipeline carries color provenance metadata
- [ ] No sRGB or gamma-encoded data used as working space
- [ ] Gamut boundary checking enabled
- [ ] No double transforms in the pipeline
- [ ] Exhibition display target (P3-D65) configured and tested
- [ ] Grading delivery conforms to `grading_delivery` schema from output-schemas
