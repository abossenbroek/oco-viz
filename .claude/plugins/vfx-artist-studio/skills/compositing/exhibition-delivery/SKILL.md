---
name: exhibition-delivery
user-invocable: false
type: instruction
primary_owner: compositor
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Exhibition Delivery -- Format Fidelity for Gallery and Projection

Delivery Format Fidelity -- output matches exhibition delivery spec exactly. No
approximations, no "close enough." The exhibition delivery specification defines
five distinct output formats, each serving a specific viewing context. A format
mismatch -- wrong color space, wrong bit depth, wrong paper, wrong metadata -- is
a delivery failure that invalidates the exhibition.

> "The last pixel matters as much as the first."

---

## Principle

The gap between a correct render and a correct delivery is where exhibitions fail.
A perfectly rendered frame delivered in the wrong color space, at the wrong bit depth,
on the wrong paper, or without required metadata is as useless as a corrupt file. The
delivery specification is not a guideline -- it is a contract with the exhibition venue,
the printer, the projectionist, and the archive.

Every delivery format in `exhibition-delivery-spec.yaml` exists for a specific reason:
the projection format serves calibrated gallery displays, the print format serves
archival paper under controlled lighting, the review format serves editorial workflows,
and the archive format preserves full-fidelity source for future use. Each format has
non-negotiable requirements that must be met exactly.

---

## Procedure

### Step 1 -- Verify Source Quality

Before generating any delivery format, verify that the source composited frames meet
all quality thresholds from `exhibition-delivery-spec.yaml`:

| Check | Requirement | Measurement |
|-------|-------------|-------------|
| Black level | Background pixels exactly (0,0,0) | Sample void regions |
| Dynamic range | Minimum 14 stops | Log-space analysis |
| Temporal stability | Flicker variance < 0.005 | Frame-to-frame comparison |
| Grain visibility | Visible at density 0.1, invisible at density 0.8 | Sample density regions |
| Crust read | Surface matte black, interior translucent grey | Visual inspection |

If any quality threshold fails, the source is defective and must be fixed before delivery
generation proceeds.

### Step 2 -- Generate Digital Projection Deliverable

The primary exhibition deliverable for gallery projection on calibrated displays:

```yaml
format: "16-bit Deep EXR"
resolution: [4096, 2160]    # 4K DCI
color_space: "ACEScg"
compression: "ZIP (lossless)"
framerate: 24
channels: "RGB + deep"
```

**Metadata requirements** (embedded in EXR header):

| Field | Value | Purpose |
|-------|-------|---------|
| `shot_id` | e.g. "sc010" | Shot identification |
| `frame_number` | e.g. 0001 | Frame within shot |
| `tier` | "final" | Must be final tier |
| `lookdev_locked` | true | Confirms all parameters locked by human |
| `approved_by` | "vfx-supe" | Approval authority |

### Step 3 -- Generate Review Proxy

For dailies, editorial review, and client screening:

```yaml
format: "ProRes 4444 XQ"
resolution: [2048, 1080]    # 2K
color_space: "Rec.709"
bit_depth: "12-bit"
framerate: 24
```

The review proxy is the only format where a display transform is baked in. The
Rec.709 color space includes the ACES Output Transform, converting from the ACEScg
working space to display-referred values suitable for standard monitors.

### Step 4 -- Generate Film-Out Deliverable (Contingency)

If film-out is required by the exhibition:

```yaml
format: "DPX"
resolution: [4096, 2160]    # 4K DCI
color_space: "Cineon/ADX"
bit_depth: "10-bit log"
framerate: 24
```

### Step 5 -- Generate Print Deliverable

For gallery prints under controlled viewing conditions:

```yaml
format: "TIFF"
bit_depth: "16-bit"
resolution: "300 DPI native at print size"
color_space: "sRGB"
icc_profile: "Matched to printer/paper combination"
```

**Print specifications:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Paper | Hahnemuhle Photo Rag Baryta 315 gsm | Archival, glossy fiber finish |
| DPI | 300 | Native resolution, no resampling |
| Black point | Absolute (no compensation) | The void must be true black on paper |
| ICC profile | Matched to printer/paper | Ensures screen-to-print fidelity |
| Sizes | A3+ (13x19"), A1 (24x36") | Contact sheet and exhibition print |

**Critical:** The black point must be absolute, not relative. Relative black point
compensation lifts the darkest values to match the paper's minimum density, which
means the void is no longer true black. For the achromatic soot visual language, the
void must be as black as the paper can produce -- absolute black point preserves this.

### Step 6 -- Generate Archive Master

Full-fidelity archive with every rendered pass:

```yaml
format: "EXR"
bit_depth: "32-bit float"
resolution: [4096, 2160]
color_space: "ACEScg"
compression: "ZIP"
channels: "multi-layer (all AOVs)"
retention: "permanent"
```

The archive master preserves the full AOV slate in 32-bit float. This is the only
format from which all other formats can be regenerated without quality loss.

### Step 7 -- Embed Metadata and Generate Manifest

Every delivery file must carry metadata in its header or sidecar:

```yaml
metadata:
  shot_id: "sc010"
  frame_number: 42
  tier: "final"
  lookdev_locked: true
  approved_by: "vfx-supe"
  delivery_format: "digital_projection"
  color_space: "ACEScg"
  timestamp: "2026-02-15T20:00:00Z"
```

Generate a delivery manifest with checksums for the complete delivery package.

---

## Parameters

### Delivery Format Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `projection_resolution` | [int, int] | [4096, 2160] -- 4K DCI |
| `projection_format` | string | 16-bit Deep EXR |
| `projection_color_space` | string | ACEScg |
| `review_resolution` | [int, int] | [2048, 1080] -- 2K |
| `review_format` | string | ProRes 4444 XQ |
| `review_color_space` | string | Rec.709 |
| `filmout_format` | string | DPX 10-bit log |
| `filmout_color_space` | string | Cineon/ADX |
| `print_format` | string | TIFF 16-bit |
| `print_dpi` | int | 300 |
| `archive_format` | string | EXR 32-bit float |

### Print Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `paper` | string | Hahnemuhle Photo Rag Baryta 315 gsm | Exhibition paper stock |
| `black_point` | string | absolute | Must be absolute, never relative |
| `icc_profile` | string | matched to printer/paper | ICC color management profile |
| `print_sizes` | list | [A3+ 13x19", A1 24x36"] | Exhibition print dimensions |

### Metadata Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `shot_id` | string | yes | Shot identifier |
| `frame_number` | int | yes | Frame within shot |
| `tier` | string | yes | Must be "final" for delivery |
| `lookdev_locked` | bool | yes | Must be true for delivery |
| `approved_by` | string | yes | Approval authority (vfx-supe) |

---

## Color Management at Delivery

| Delivery Format | Working Space | Output Space | Transform |
|----------------|---------------|--------------|-----------|
| Digital Projection (EXR) | ACEScg | ACEScg | None (scene-referred) |
| Review Proxy (ProRes) | ACEScg | Rec.709 | ACES Output Transform (SDR Video) |
| Film-Out (DPX) | ACEScg | Cineon/ADX | ACES to ADX conversion |
| Print (TIFF) | ACEScg | sRGB | ACES Output Transform (sRGB) + ICC |
| Archive (EXR) | ACEScg | ACEScg | None (scene-referred, full fidelity) |

**Critical:** Display transforms are applied only at the output stage. The working space
is always ACEScg throughout the compositing pipeline. Never apply a display transform
to an intermediate file.

---

## Anti-Patterns

### 1. Wrong Color Space

**Symptom:** Gallery projection appears washed out, oversaturated, or with incorrect
contrast. Print colors do not match the calibrated monitor. Review proxy is too dark
or too bright.

**Cause:** Delivery generated in the wrong color space -- sRGB data labeled as ACEScg,
or ACEScg data with the display transform applied twice, or missing ICC profile for
print delivery.

**Fix:** Follow the color management table exactly. Projection and archive are ACEScg
(no display transform). Review is Rec.709 (one display transform). Print is sRGB with
ICC profile. Every format has exactly one correct color pipeline.

### 2. Missing Metadata

**Symptom:** Exhibition venue cannot verify frame provenance. Archive master cannot be
traced to its source shot and approval chain. Delivery package fails venue QC.

**Cause:** Metadata fields omitted from EXR headers or sidecar files. The delivery was
generated without embedding shot_id, frame_number, tier, lookdev_locked, and approved_by.

**Fix:** Embed all required metadata in every delivery file. Generate a delivery manifest
with checksums. Metadata is not optional decoration -- it is the mechanism by which the
exhibition venue verifies provenance and the archive ensures long-term traceability.

### 3. Relative Black Point for Print

**Symptom:** Gallery prints show the void as dark grey instead of true black. The plume
appears to float on a murky background. The achromatic soot language is compromised.

**Cause:** Print driver or ICC workflow using relative black point compensation, which
lifts the darkest values to match the paper's minimum density (Dmax). This is standard
practice for photographic prints but wrong for this project.

**Fix:** Set black point to absolute. This instructs the print driver to map (0,0,0) to
the paper's absolute black (maximum ink density) without compensation. The void will be
as black as the Hahnemuhle Photo Rag Baryta can produce. Accept that "absolute black"
on paper is not as black as a display -- what matters is that it is the blackest value
the medium can achieve.

### 4. Wrong Paper

**Symptom:** Print texture, surface finish, or archival quality does not match exhibition
specification. Colors shift due to different paper white point. Black density (Dmax) is
insufficient.

**Cause:** Using a different paper stock than the specified Hahnemuhle Photo Rag Baryta
315 gsm. Different papers have different Dmax, different surface textures, different
white points, and different archival properties.

**Fix:** Use only the specified paper stock. If the specified stock is unavailable,
escalate to the exhibition director -- paper substitution is a creative decision, not
a technical one.

---

## Validation Checklist

- [ ] Source frames pass all quality thresholds (black level, dynamic range, temporal stability)
- [ ] Digital projection: 16-bit EXR, 4K DCI, ACEScg, ZIP compression
- [ ] Review proxy: ProRes 4444 XQ, 2K, Rec.709, 12-bit
- [ ] Film-out: DPX, 4K DCI, Cineon/ADX, 10-bit log (if required)
- [ ] Print: TIFF 16-bit, 300 DPI, sRGB with ICC profile, absolute black point
- [ ] Archive: EXR 32-bit float, 4K DCI, ACEScg, all AOVs, ZIP compression
- [ ] All metadata fields embedded: shot_id, frame_number, tier, lookdev_locked, approved_by
- [ ] Tier is "final" for all delivery formats
- [ ] lookdev_locked is true for all delivery formats
- [ ] Paper is Hahnemuhle Photo Rag Baryta 315 gsm for print
- [ ] Black point is absolute (not relative) for print
- [ ] Display transform applied exactly once for display-referred formats (Rec.709, sRGB)
- [ ] No display transform applied to scene-referred formats (ACEScg EXR, archive)
- [ ] Delivery manifest generated with checksums for complete package
- [ ] Delivery conforms to exhibition-delivery-spec.yaml in full
