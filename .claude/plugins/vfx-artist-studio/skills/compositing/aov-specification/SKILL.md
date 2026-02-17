---
name: aov-specification
user-invocable: false
type: instruction
primary_owner: compositor
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# AOV Specification -- The Render Contract

AOV Completeness -- missing AOVs are pipeline failures, not comp problems. The AOV slate
is defined at render time and must be complete before any frame enters compositing. If a
required AOV is absent, the frame is defective. The compositor does not proceed with
defective frames and does not synthesize missing passes.

The AOV specification is the contract between the renderer and the compositor. It defines
exactly which passes will be produced, in what format, at what bit depth, and with what
channel layout. This contract is immutable per shot -- changes to the AOV slate require
re-rendering all affected frames.

> "An incomplete AOV slate is a broken render. Fix it at the source."

---

## Principle

Every pixel in the final beauty image must decompose into contributions from named AOVs.
This decomposition enables: (1) surgical comp adjustments to specific light transport
paths, (2) mathematical verification that the comp is faithful to the render, and
(3) diagnostic isolation when a visual artifact appears.

The AOV slate for oco-viz is defined in two knowledge files:
- `compositing-standards.yaml` -- AOV naming convention and EXR channel layout
- `karma-render-profiles.yaml` -- per-tier render settings and full AOV slate definition

These two files are the single source of truth for AOV specification. Any discrepancy
between them is a configuration defect that must be resolved before rendering.

---

## Required AOV Slate

### Primary AOVs

| AOV Name | LPE Expression | Format | Channels | Purpose |
|----------|---------------|--------|----------|---------|
| `Beauty` | `lpe:C.*` | float16 | RGB | Final denoised beauty (primary deliverable) |
| `NoisyBeauty` | `lpe:C.* (pre-OIDN)` | float16 | RGB | Pre-denoiser beauty for grain restoration |
| `emission` | `lpe:Ce.*` | float16 | RGB | Emission LPE -- curvature-driven glow isolation |
| `scatter` | `lpe:Cd.*` | float16 | RGB | Diffuse/scatter LPE -- translucent interior transport |

### Data AOVs

| AOV Name | Source | Format | Channels | Purpose |
|----------|--------|--------|----------|---------|
| `density` | volume density AOV | float32 | mono (Y) | Raw density field for comp adjustments |
| `deep` | deep camera output | deep EXR | per-sample | Per-sample depth for volumetric DOF |
| `velocity` | velocity AOV | float16 | RGB (xyz) | Motion vectors for temporal denoiser and motion blur |
| `temperature` | temperature AOV | float32 | mono (Y) | Diagnostic Kelvin values, creative re-grade potential |

### Supplementary AOVs

| AOV Name | Source | Format | Channels | Purpose |
|----------|--------|--------|----------|---------|
| `CryptoObject` | cryptomatte | float32 | RGB | Object-level isolation mattes |
| `depth` | camera depth | float32 | mono | Per-pixel camera distance (flat, not deep) |
| `N` | surface normal | float16 | RGB (xyz) | Normal direction for relighting and diagnostics |
| `albedo` | surface albedo | float16 | RGB | Denoiser guide and diagnostic |

---

## EXR Channel Layout

### Multi-Layer EXR

All primary and data AOVs are stored in a single multi-layer EXR per frame, with
the exception of deep data which occupies a separate file:

```
{shot}/render/{shot}.{frame:04d}.exr           -- multi-layer flat EXR
{shot}/render/{shot}.{frame:04d}.deep.exr      -- deep EXR (separate file)
```

Channel naming follows the `{AOV}.{channel}` convention:

```
Beauty.R, Beauty.G, Beauty.B
NoisyBeauty.R, NoisyBeauty.G, NoisyBeauty.B
emission.R, emission.G, emission.B
scatter.R, scatter.G, scatter.B
density.Y
velocity.X, velocity.Y, velocity.Z
temperature.Y
CryptoObject.R, CryptoObject.G, CryptoObject.B
depth.Y
N.X, N.Y, N.Z
albedo.R, albedo.G, albedo.B
```

### LPE Expressions

Light Path Expressions define which light transport paths contribute to each AOV:

| AOV | LPE | Description |
|-----|-----|-------------|
| Beauty | `lpe:C.*` | All camera-visible light paths |
| emission | `lpe:Ce.*` | Camera-visible emission (incandescence, glow) |
| scatter | `lpe:Cd.*` | Camera-visible diffuse scattering (translucency) |

The Beauty AOV equals the sum of all LPE-decomposed AOVs. For the achromatic soot
pipeline: `Beauty = emission + scatter`. This identity must hold within the
`beauty_reconstruction_tolerance` defined in multi-pass-integration.

---

## Procedure

### Step 1 -- Define AOV Slate at Render Setup

Before any rendering begins, verify that the Karma XPU render configuration includes
all required AOVs from `karma-render-profiles.yaml`. The Houdini TD is responsible for
configuring the render node with the complete slate.

### Step 2 -- Validate Format Requirements

Each AOV has specific format requirements that affect precision and file size:

| Format | Bit Depth | Dynamic Range | Use For |
|--------|-----------|---------------|---------|
| float16 (half) | 16-bit | ~10 stops | Color AOVs (Beauty, emission, scatter) |
| float32 (full) | 32-bit | ~38 stops | Data AOVs (density, temperature, depth) |
| deep EXR | variable | per-sample | Volumetric depth data |

**Critical:** Data AOVs (density, temperature) must be float32. Float16 does not have
sufficient precision for density values near zero or temperature values in Kelvin
(293-3000K range). Using float16 for data AOVs introduces quantization artifacts.

### Step 3 -- Validate Channel Count

Each AOV must have the correct number of channels:

| AOV | Expected Channels | Failure if Wrong |
|-----|-------------------|-----------------|
| Beauty, emission, scatter | 3 (RGB) | Mono beauty is always wrong |
| density, temperature, depth | 1 (Y) | RGB density is a misconfiguration |
| velocity, N | 3 (XYZ) | Mono velocity loses directional information |

### Step 4 -- Run Completeness Check on Rendered Frames

After rendering, run the AOV completeness check on every frame:

```
for each frame:
    load EXR header
    for each required AOV:
        assert AOV channels present
        assert format matches specification
        assert channel count correct
    assert deep EXR file exists
    assert Beauty = emission + scatter (within tolerance)
```

Frames that fail the completeness check are flagged as defective and must be re-rendered.

---

## Parameters

### Validation Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `required_aovs` | list | from compositing-standards.yaml | -- | List of required AOV names |
| `format_requirements` | dict | per AOV specification | -- | Format per AOV (float16/float32) |
| `channel_requirements` | dict | per AOV specification | -- | Channel count per AOV |
| `beauty_reconstruction_tolerance` | float | 0.001 | 0.0005 - 0.005 | Max error for Beauty = sum(LPEs) |

### File Naming Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `aov_exr_pattern` | string | `{shot}/render/{shot}.{frame:04d}.exr` | Multi-layer EXR path |
| `deep_exr_pattern` | string | `{shot}/render/{shot}.{frame:04d}.deep.exr` | Deep EXR path |

---

## Anti-Patterns

### 1. Rendering Without Full AOV Slate

**Symptom:** Compositing begins and the compositor discovers that one or more required
AOVs are missing. The emission pass is absent, or NoisyBeauty was not configured, or
deep output was disabled.

**Cause:** The render configuration was not validated against the AOV specification
before rendering began. The Houdini TD configured the render node without checking
karma-render-profiles.yaml.

**Fix:** Run AOV completeness validation at render setup time (before any frames render)
and again after rendering (on every output frame). Missing AOVs are render configuration
defects -- fix the config and re-render.

### 2. Wrong Bit Depth

**Symptom:** Density values near zero show visible stepping or banding. Temperature
values cluster into discrete bands instead of smooth gradients. Data AOVs lose precision
in the ranges that matter most.

**Cause:** Data AOVs rendered in float16 instead of float32. Half-float has only 10 bits
of mantissa, which is insufficient for density values in the 0.0-0.01 range or
temperature values in the 293-3000K range.

**Fix:** Data AOVs (density, temperature, depth) must always be float32. Color AOVs
(Beauty, emission, scatter) can use float16 because their values are already
scene-referred with appropriate dynamic range.

### 3. Non-Standard AOV Names

**Symptom:** The compositor's node graph cannot find the expected AOV channels. The EXR
contains the data but under different names -- `diffuse` instead of `scatter`,
`Cf` instead of `Beauty`, `P.Z` instead of `depth`.

**Cause:** The render configuration uses renderer-default AOV names instead of the
project-standard names defined in compositing-standards.yaml.

**Fix:** Configure AOV names in the render node to match compositing-standards.yaml
exactly. The naming convention is the contract -- renderers may have different defaults,
but the output must conform to the project standard.

### 4. The Partial Slate

**Symptom:** Primary AOVs (Beauty, emission, scatter) are present but data AOVs
(velocity, temperature) are disabled "to save render time." The compositor cannot
perform motion-tracked grain restoration or temperature-based re-grading.

**Cause:** Optimizing render time by disabling AOVs that seem optional. No AOV in the
required slate is optional -- each serves a specific pipeline function.

**Fix:** Render the full slate. If render time is a concern, reduce resolution or
sample count, but never reduce the AOV slate. A fast render with missing passes is
less useful than a slow render with complete data.

---

## Validation Checklist

- [ ] All required AOVs present in rendered EXR (per compositing-standards.yaml)
- [ ] AOV names match project standard exactly (case-sensitive)
- [ ] Color AOVs (Beauty, NoisyBeauty, emission, scatter) in float16 format
- [ ] Data AOVs (density, temperature, depth) in float32 format
- [ ] Channel count correct for each AOV (RGB for color, mono for data, XYZ for vectors)
- [ ] Deep EXR file exists as separate file per frame
- [ ] EXR channel layout matches multi-layer naming convention (`{AOV}.{channel}`)
- [ ] Beauty = emission + scatter within reconstruction tolerance
- [ ] NoisyBeauty present for grain restoration workflow
- [ ] Velocity present for temporal denoiser and motion-tracked grain
- [ ] No renderer-default AOV names -- all names from compositing-standards.yaml
- [ ] AOV slate identical across all frames in the shot (no partial renders)
- [ ] AOV specification consistent between compositing-standards.yaml and karma-render-profiles.yaml
