# Finishing Specification

## Nuke Compositing, Sound Design, and Master Deliverables

**Version:** 1.0
**Compositing:** Nuke (Foundry) with MCP automation
**Color Pipeline:** ACES 1.3 (ACEScg working space)
**Visual Language:** Soot (see `plan/visual_language.yaml`)

---

## Nuke Node Graph

### Primary Comp Template

Each shot follows this node graph structure. The graph branches at the output stage to produce multiple delivery formats simultaneously.

```
Read (multi-layer EXR)
  |
  v
Shuffle (isolate AOVs: Beauty, NoisyBeauty, emission, scatter, density)
  |
  v
Grade (per-AOV exposure/gamma adjustment)
  |
  +-- Beauty branch --------+
  |                          |
  +-- NoisyBeauty branch --+ |
  |                        | |
  v                        v v
Merge (Beauty + 10-15% NoisyBeauty, "plus" or "over" blend)
  |
  v
ZDefocus / DeepDefocus (volumetric DOF, exhibition tier only)
  |
  v
Grain2 (Kodak Vision3 500T, monochrome, see Grain Strategy below)
  |
  v
OCIOColorSpace (ACEScg -> delivery color space)
  |
  +-- Write: sRGB PNG/TIFF (gallery stills, print)
  +-- Write: Rec.709 ProRes 4444 XQ (mezzanine)
  +-- Write: DCI-P3 DPX (cinema screening)
  +-- Write: Rec.2020 ST2084 EXR (HDR exhibition)
```

### AOV Shuffle Configuration

| Shuffle Node | Source Layer | Output | Purpose |
|-------------|-------------|--------|---------|
| shuffle_beauty | Beauty.RGB | rgba | Primary compositing layer |
| shuffle_noisy | NoisyBeauty.RGB | rgba | Grain restoration source |
| shuffle_emission | emission.RGB | rgba | Emission isolation for creative re-grade |
| shuffle_scatter | scatter.RGB | rgba | Scattering isolation |
| shuffle_density | density.Y | alpha (mono) | Density matte for comp adjustments |
| shuffle_velocity | velocity.XYZ | motion (3-chan) | Motion vectors for MotionBlur3D |
| shuffle_temperature | temperature.Y | alpha (mono) | Diagnostic overlay |

### Grade Nodes

Grade nodes provide per-shot creative adjustment without re-rendering.

| Grade Target | Typical Adjustment | Rationale |
|-------------|-------------------|-----------|
| Beauty | exposure -0.1 to -0.3 | Push overall image darker for industrial dread |
| emission | gain 0.8 - 1.5 | Control curvature-driven glow intensity in comp |
| scatter | gain 0.5 - 1.2 | Modulate interior translucency brightness |

**Critical:** All Grade operations happen in ACEScg linear space, before any color space conversion.

### NoisyBeauty Grain Restoration

The denoised Beauty pass is clean but sterile. Blending 10-15% of the NoisyBeauty (pre-OIDN) pass restores organic render noise character.

```
Merge node:
  operation: plus
  mix: 0.10 - 0.15
  A input: Beauty (graded)
  B input: NoisyBeauty (graded, motion-tracked if camera moves)
```

The NoisyBeauty blend amount varies by tier:
- **Study:** 15% (more noise acceptable, adds life).
- **Exhibition:** 10% (subtle, beneath Grain2 film grain layer).

### Volumetric Depth of Field

**Exhibition tier only.** Uses deep EXR data for physically accurate volumetric DOF.

| Node | Configuration | Notes |
|------|--------------|-------|
| DeepRead | Load `{shot}.{frame}.deep.exr` | Deep sample data |
| DeepDefocus | focal_distance: per-shot, fstop: 2.8-5.6 | Volumetric DOF, not post blur |
| DeepToImage | Output to rgba | Flatten for downstream |

If deep data is unavailable, fall back to ZDefocus using the density AOV as depth proxy:

```
ZDefocus:
  z_channel: density.Y (inverted: high density = near)
  focal_point: 0.5 (mid-density)
  blur_size: 3-8 pixels (subtle, not aggressive)
  filter: disk
```

---

## Nuke MCP Automation

### Framework

[dughogan/nuke_mcp](https://github.com/dughogan/nuke_mcp) -- Model Context Protocol server for Nuke, enabling programmatic node graph creation and batch operations.

### Automated Operations

**1. Comp Template Auto-Generation**

On render job completion (triggered by farm webhook), auto-create the comp .nk file from the AOV manifest:

```python
# Pseudo-code for MCP template generation
def create_comp_template(shot_name, aov_manifest, tier):
    read_node = create_read(path=f"{shot_name}/render/{shot_name}.####.exr")
    shuffles = [create_shuffle(aov) for aov in aov_manifest]
    grades = [create_grade(aov, defaults=TIER_DEFAULTS[tier]) for aov in aov_manifest]
    merge = create_merge(beauty=grades["Beauty"], noisy=grades["NoisyBeauty"],
                         mix=0.10 if tier == "exhibition" else 0.15)
    grain = create_grain2(preset="kodak_5219_500t", intensity=GRAIN_INTENSITY[tier])
    outputs = [create_write(colorspace, format) for colorspace, format in DELIVERABLES]
    connect_graph(read_node, shuffles, grades, merge, grain, outputs)
```

**2. Batch Grain/Grade/Output Transforms**

Apply consistent grain and grade settings across all shots in a sequence:

```python
# Batch update all shots with locked lookdev grade
for shot in shots:
    nuke_mcp.set_knob(f"{shot}/grade_beauty", "multiply", [0.92, 0.92, 0.92, 1.0])
    nuke_mcp.set_knob(f"{shot}/grain2", "intensity", grain_intensity)
```

**3. Per-Shot LUT Comparisons**

Generate before/after comparison screenshots for QA:

```python
# Auto-capture comp output vs. raw render
for shot in shots:
    raw = render_frame(shot, bypass_comp=True)
    comped = render_frame(shot, bypass_comp=False)
    side_by_side = concat_horizontal(raw, comped)
    save(side_by_side, f"qa/{shot}_compare.png")
```

**4. Auto-Slate (Study Tier Only)**

Study tier renders receive automated slate overlays with:
- Shot name, frame number, date
- Tier, sample count, render time
- Lookdev parameter hash (links back to Contact Sheet Bible selection)

Exhibition tier: no slate, no text, no annotations per visual language spec.

**5. Multi-Format Parallel Writes**

All output formats render simultaneously via Nuke's multi-write capability:

```python
# Parallel write nodes, all sourcing from the same comp output
writes = {
    "srgb_png": {"colorspace": "Output - sRGB", "format": "png", "path": "..."},
    "rec709_prores": {"colorspace": "Output - Rec.709", "format": "mov", "codec": "prores4444xq"},
    "dcip3_dpx": {"colorspace": "Output - P3-D65", "format": "dpx", "path": "..."},
    "rec2020_exr": {"colorspace": "ACES - ACEScg", "format": "exr", "path": "..."},
}
```

---

## Deep Compositing

### Purpose

Volumetric content (soot plume) occupies depth continuously, not at a single Z value. Deep compositing preserves per-sample depth information, enabling:

1. Accurate volumetric DOF (DeepDefocus instead of post blur).
2. Correct compositing order with any future foreground/background elements.
3. Re-lighting or re-grading by depth slice.

### Deep EXR Pipeline

```
Karma XPU render (deep camera enabled)
  |
  v
Deep EXR per frame ({shot}.{frame}.deep.exr)
  |
  v
DeepRead (Nuke)
  |
  v
DeepExpression (optional: depth-based grade, e.g., darken far slices)
  |
  v
DeepDefocus (focal_distance, fstop per shot)
  |
  v
DeepToImage (flatten to 2D for downstream grain/color/write)
```

### Deep Settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| Deep output | Enabled in Karma ROP | Adds ~80 MB/frame overhead |
| Samples per deep pixel | 8-16 | Sufficient for single-volume scenes |
| Deep tolerance | 0.01 | Merge close samples to reduce file size |
| Deep channels | rgba, depth, density | Minimum set for volumetric DOF |

---

## Grain Strategy

### Philosophy

Film grain adds organic texture that breaks the clinical precision of digital rendering. For the Soot visual language, grain must be monochrome (matching achromatic palette), consistent with industrial film stocks, and calibrated per tier.

### Grain2 Node Configuration

| Parameter | Study Tier | Exhibition Tier |
|-----------|-----------|-----------------|
| Preset reference | Kodak Vision3 5219 500T | Kodak Vision3 5219 500T |
| Grain mode | Monochrome (R=G=B linked) | Monochrome (R=G=B linked) |
| Intensity (shadows) | 0.5% | 0.8% |
| Intensity (midtones) | 0.5% | 1.0% |
| Intensity (highlights) | 0.3% | 0.6% |
| Size | 1.0 | 1.2 |
| Irregularity | 0.6 | 0.7 |
| Seed | per-frame (animated) | per-frame (animated) |

**Kodak Vision3 5219 500T** is chosen for its:
- Medium-large grain structure (ISO 500 equivalent).
- Warm neutral character (irrelevant for achromatic, but the grain shape is distinctive).
- Film noir lineage (appropriate for "industrial dread" mood).

### Monochrome Enforcement

**Critical:** Grain channels must be linked (R=G=B identical). Any per-channel grain variation introduces subtle color, violating the achromatic palette. In Nuke's Grain2:

```
red_intensity = green_intensity = blue_intensity
```

Verify by sampling grain-only (difference between grained and un-grained frames) and confirming R==G==B at every pixel.

### Grain Interaction with NoisyBeauty

The grain pipeline has two layers:

1. **NoisyBeauty blend (10-15%):** Render noise from Karma, motion-correlated, adds "render texture."
2. **Grain2 (0.5-1.0%):** Film grain emulation, frame-independent, adds "capture texture."

These stack. Total perceived grain = NoisyBeauty contribution + Grain2 contribution. The NoisyBeauty blend goes first (it is render-specific), then Grain2 (it is format-specific, simulating the exhibition medium).

---

## Sound Design Brief

### Concept

The Soot visual language extends to sound. Audio accompaniment is sub-bass drone, no melody, no rhythm, no weather ambience. The sound is the audible equivalent of the visual: heavy, oppressive, geological, inexorable.

### Specifications

| Parameter | Value |
|-----------|-------|
| Frequency range | 20-40 Hz fundamental, harmonics to 120 Hz |
| Character | Sub-bass drone, continuous, no attack/release |
| Dynamics | Amplitude follows density: denser frames = louder |
| Spatial | Mono or stereo (no surround spatial effects) |
| Duration | Continuous loop, seamless join for exhibition playback |
| Playback | Requires subwoofer (below 40 Hz inaudible on standard speakers) |

### Amplitude Envelope

```
amplitude(t) = base_level + density_integral(t) * density_coupling
```

Where `density_integral(t)` is the sum of all voxel densities in the frame (total mass proxy). As the plume grows denser, the drone grows louder. As the plume dissipates, the drone retreats to `base_level`.

| Parameter | Value |
|-----------|-------|
| base_level | -24 dBFS |
| density_coupling | 0.3 (maps full density to -12 dBFS) |
| attack | 2.0 sec (slow swell, matches visual reveal) |
| release | 4.0 sec (lingers after visual dissipation) |

### Reference Artists

| Artist | Quality to Reference |
|--------|---------------------|
| Ben Frost | Industrial sub-bass, physical pressure, material weight |
| Tim Hecker | Textured drone, granular detail in sustained tones |
| Sunn O))) | Geological timescale, overtone saturation, physical vibration |

### Technical Requirements

| Requirement | Specification |
|-------------|--------------|
| Format | 48 kHz / 24-bit WAV (master), AAC 256 kbps (web) |
| Subwoofer | Mandatory for exhibition (18" driver minimum) |
| SPL | 75-85 dB C-weighted at listening position |
| Isolation | Exhibition space requires acoustic isolation from adjacent galleries |

### Non-Requirements

- No weather sounds (wind, rain, thunder).
- No music (melody, harmony, rhythm).
- No narration or voice.
- No spatial audio effects (binaural, Atmos).
- No silence -- the drone is continuous throughout the loop.

---

## Master Deliverables

### Delivery Matrix

| Deliverable | Format | Resolution | Color Space | Bit Depth | Codec | Use Case |
|-------------|--------|-----------|-------------|-----------|-------|----------|
| Gold Master | EXR | 4096x2160 | ACEScg | 16-bit float | ZIP | Archive, re-mastering source |
| Mezzanine | MOV | 4096x2160 | Rec.2020 PQ / DCI-P3 | 10-bit | ProRes 4444 XQ | Festival, cinema screening |
| Exhibition | MOV / MP4 | 4096x2160 | Rec.2020 PQ | 10-bit | H.265 CRF 15 or ProRes 422 HQ | Gallery looping playback |
| Web | MP4 | 1920x1080 | sRGB | 8-bit | H.264 CRF 18 | Website, social media, documentation |
| Print | TIFF | 4096x2160+ | sRGB / AdobeRGB | 16-bit | LZW | Archival print, Hahnemuhle baryta |

### Gold Master (EXR Sequence)

The authoritative archive from which all other deliverables are derived.

| Property | Value |
|----------|-------|
| Format | OpenEXR 2.0 multi-part |
| Channels | Beauty RGB + all AOVs (multi-layer) |
| Color space | ACEScg (ACES 1.3) |
| Bit depth | 16-bit half-float |
| Compression | ZIP (lossless) |
| Frame range | 1-720 (30 sec @ 24 fps) |
| Naming | `{shot}/gold/{shot}.{frame:04d}.exr` |
| Checksum | SHA-256 per frame, manifest JSON |
| Storage | Dual copies: local NAS + cloud (S3 Glacier Deep Archive) |

### Checksum Manifest

```json
{
  "shot": "shot_01",
  "frames": 720,
  "format": "exr",
  "colorspace": "ACEScg",
  "checksums": {
    "shot_01.0001.exr": "sha256:a1b2c3...",
    "shot_01.0002.exr": "sha256:d4e5f6...",
    "...": "..."
  },
  "generated": "2026-xx-xx",
  "pipeline_version": "oco-viz 1.0"
}
```

### Mezzanine (ProRes 4444 XQ)

| Property | Value |
|----------|-------|
| Format | QuickTime MOV |
| Codec | ProRes 4444 XQ |
| Resolution | 4096x2160 (4K DCI) |
| Frame rate | 24 fps |
| Color space | Rec.2020 PQ (HDR) or DCI-P3 (cinema) |
| Bit depth | 10-bit per channel |
| Audio | 48 kHz / 24-bit PCM stereo (drone) |
| Estimated size | ~80 GB per 30-sec shot |

### Exhibition (H.265 or ProRes 422 HQ)

Optimized for gallery looping playback on media servers (BrightSign, Mac Mini, dedicated player).

| Property | H.265 Option | ProRes 422 HQ Option |
|----------|-------------|---------------------|
| Container | MP4 | MOV |
| Resolution | 4096x2160 | 4096x2160 |
| Frame rate | 24 fps | 24 fps |
| CRF / Bitrate | CRF 15 (~80-120 Mbps) | ~220 Mbps |
| Color space | Rec.2020 PQ | Rec.2020 PQ |
| Audio | AAC 256 kbps | PCM 48/24 |
| Loop | Seamless (GOP structure aligned) | Native |
| Estimated size | ~30 GB / 30 sec | ~80 GB / 30 sec |

**H.265 preferred** for media server compatibility and storage efficiency. ProRes 422 HQ as fallback for players that do not decode H.265 at 4K.

### Web (H.264)

| Property | Value |
|----------|-------|
| Container | MP4 |
| Codec | H.264 High Profile |
| Resolution | 1920x1080 |
| Frame rate | 24 fps |
| CRF | 18 |
| Color space | sRGB (Rec.709) |
| Audio | AAC 128 kbps |
| Estimated size | ~150 MB per 30-sec shot |

### Print (TIFF)

Selected frames exported as archival-quality stills for Hahnemuhle baryta or gallery print.

| Property | Value |
|----------|-------|
| Format | TIFF |
| Bit depth | 16-bit per channel |
| Color space | sRGB or AdobeRGB (ICC tagged) |
| Resolution | 300 DPI at target print size |
| Compression | LZW (lossless) |
| ICC Profile | Embedded, matched to printer/paper combination |
| Black point | Absolute (preserve true black void) |

---

## OCIO Configuration

All color transformations use OpenColorIO (OCIO) with the ACES 1.3 config.

```
# Environment
OCIO=/path/to/aces_1.3/config.ocio

# Working space
working_space: ACEScg

# Output transforms per deliverable
gold:       ACEScg (no transform — native working space)
mezzanine:  ACES 1.3 Output - Rec.2020 (PQ) or Output - P3-D65
exhibition: ACES 1.3 Output - Rec.2020 (PQ)
web:        ACES 1.3 Output - sRGB
print:      ACES 1.3 Output - sRGB (or custom ICC via Nuke CMSTestPattern)
```

---

**Document Type:** Compositing and Finishing Specification
**Depends On:** `plan/render_farm_spec.md`, `plan/lookdev_bible.md`, `plan/visual_language.yaml`
**Feeds Into:** Nuke comp templates, exhibition installation, print production
