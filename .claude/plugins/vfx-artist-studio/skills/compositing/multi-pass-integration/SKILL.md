---
name: multi-pass-integration
user-invocable: false
type: instruction
primary_owner: compositor
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Multi-Pass AOV Integration -- Accountable Beauty Reconstruction

Every pixel in the final image is the sum of measurable contributions from specific
render passes. No magic -- every visual element traces to an AOV. If a pixel cannot be
decomposed into its constituent passes, the comp is broken. If a pass was painted over
in comp, the render is broken and must be fixed upstream.

> "If you can't account for every photon, you don't understand the image."

---

## Principle

Multi-pass integration treats the final beauty image as an equation, not an artwork.
The compositor does not create light, shadow, or atmosphere -- the renderer did that.
The compositor assembles the renderer's output faithfully, applies grain restoration to
counteract denoiser sterility, and delivers a mathematically verifiable result. The
reconstructed beauty must match the rendered Beauty AOV within tolerance. If it does not,
passes are missing, misweighted, or corrupted.

The AOV slate is defined in `compositing-standards.yaml` and `karma-render-profiles.yaml`.
Every AOV listed there must be present in the multi-layer EXR before compositing begins.
A missing AOV is a pipeline failure -- it is never the compositor's job to synthesize a
missing pass.

---

## Procedure

### Step 1 -- Load All AOVs from Multi-Layer EXR

Load the multi-layer EXR and extract every AOV channel. Verify the channel layout matches
the specification in `compositing-standards.yaml`:

```
Beauty.R, Beauty.G, Beauty.B
NoisyBeauty.R, NoisyBeauty.G, NoisyBeauty.B
emission.R, emission.G, emission.B
scatter.R, scatter.G, scatter.B
density.Y
velocity.X, velocity.Y, velocity.Z
temperature.Y
```

Deep samples are stored in a separate deep EXR file per frame
(`{shot}.{frame:04d}.deep.exr`).

### Step 2 -- Verify AOV Completeness

Check all required AOVs against the `aov_slate` from `karma-render-profiles.yaml`:

| AOV | LPE | Format | Channels | Purpose |
|-----|-----|--------|----------|---------|
| Beauty | `lpe:C.*` | float16 | RGB | Final denoised beauty |
| NoisyBeauty | `lpe:C.* (pre-OIDN)` | float16 | RGB | Grain restoration source |
| emission | `lpe:Ce.*` | float16 | RGB | Curvature-driven glow isolation |
| scatter | `lpe:Cd.*` | float16 | RGB | Translucent interior light transport |
| density | volume density AOV | float32 | mono | Raw density for comp adjustments |
| deep | deep camera output | deep EXR | per-sample | Volumetric DOF and deep compositing |
| velocity | velocity AOV | float16 | RGB (xyz) | Motion vectors for temporal denoiser |
| temperature | temperature AOV | float32 | mono | Diagnostic and re-grade potential |

If any AOV is missing, halt compositing and report the failure upstream. Do not proceed
with an incomplete AOV slate.

### Step 3 -- Assemble Beauty from Passes

Reconstruct the beauty image from its constituent LPE passes:

```
ReconstructedBeauty = emission + scatter
```

For the achromatic soot pipeline, the beauty reconstruction is straightforward because
the material model has a limited number of light transport paths. The emission pass
captures curvature-driven glow and the scatter pass captures translucent interior
light transport. Their sum must equal the rendered Beauty within tolerance.

### Step 4 -- Apply Grain Restoration

OIDN temporal denoising produces a clean but sterile image. Restore organic grain
character by blending the pre-denoiser NoisyBeauty over the denoised Beauty:

```
FinalBeauty = lerp(Beauty, NoisyBeauty, grain_blend_factor)
```

The grain blend factor is 10-15% (0.10-0.15). This restores the micro-texture that
denoising removes while preserving the temporal stability that denoising provides.

### Step 5 -- Validate Reconstruction

Compare the reconstructed beauty to the rendered Beauty AOV:

```
error = abs(ReconstructedBeauty - Beauty) / max(Beauty, epsilon)
assert max(error) < beauty_reconstruction_tolerance
```

If the reconstruction exceeds tolerance, investigate which pass is contributing
unexpected energy. Common causes: missing LPE, double-counted scatter, emission
leak from environment.

---

## Parameters

### Integration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_blend_factor` | float | 0.12 | 0.10 - 0.15 | NoisyBeauty blend ratio for grain restoration |
| `beauty_reconstruction_tolerance` | float | 0.001 | 0.0005 - 0.005 | Max relative error between reconstructed and rendered beauty |
| `aov_list` | list | from compositing-standards.yaml | -- | Required AOVs for completeness check |

### Deep Merge Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `deep_merge_order` | string | resolve-first | Deep resolve before flat merge |
| `deep_epsilon` | float | 0.0001 | Depth merge tolerance for overlapping samples |

### Grain Restoration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `grain_temporal_tracking` | bool | true | -- | Motion-track grain to prevent sliding |
| `grain_black_floor` | float | 0.0 | 0.0 | Grain must not lift the black floor |

---

## Anti-Patterns

### 1. The Comp Fix

**Symptom:** The compositor adjusts exposure, contrast, or color to compensate for a
lighting or material deficiency. The comp looks acceptable but the AOV reconstruction
no longer matches the rendered Beauty.

**Cause:** Treating compositing as a creative correction stage instead of a faithful
assembly stage. If the lighting is wrong, the lighting must be fixed in the render,
not patched in comp.

**Fix:** The compositor may apply only grain restoration and minor exposure trim
(< 0.3 stops per compositing-standards.yaml). Any larger correction is a render
issue and must be escalated to the VFX supe for upstream revision.

### 2. The Missing AOV

**Symptom:** Compositing proceeds with an incomplete AOV slate. The reconstructed beauty
does not match the rendered Beauty because a contributing pass is absent.

**Cause:** Rendering without the full AOV slate defined in karma-render-profiles.yaml, or
the EXR write node dropping channels silently.

**Fix:** Verify AOV completeness before compositing begins. If any AOV is missing, the
frame is defective and must be re-rendered. Never synthesize a missing AOV in comp.

### 3. The Over-Grained Restoration

**Symptom:** The final image appears noisy, especially in dark regions near the void
boundary. The grain restoration overwhelms the denoiser's temporal stability.

**Cause:** grain_blend_factor set above 0.15, or grain applied without motion tracking,
or grain applied uniformly including the pure-black background.

**Fix:** Keep grain_blend_factor in the 0.10-0.15 range. Apply grain restoration only
where density > 0 -- the pure black void must remain at exactly (0,0,0). Motion-track
the grain blend to prevent temporal sliding.

### 4. The Flat Merge First

**Symptom:** Deep compositing operations (volumetric DOF, deep holdouts) produce
incorrect results because the deep data was flattened before the operation was applied.

**Cause:** Flattening the deep EXR to a 2D image before performing deep operations.
Once flattened, per-sample depth information is lost and cannot be recovered.

**Fix:** Always resolve deep operations before flattening. The merge order is:
deep resolve first, then flat merge. See the deep-compositing skill for the full
deep workflow.

---

## Validation Checklist

- [ ] All required AOVs present in multi-layer EXR (per compositing-standards.yaml)
- [ ] Deep EXR file exists and contains per-sample depth data
- [ ] AOV format matches specification (float16 for color, float32 for data)
- [ ] Reconstructed beauty matches rendered Beauty within tolerance (0.001)
- [ ] Grain blend factor is within 0.10-0.15 range
- [ ] Grain restoration does not lift the black floor (void remains 0,0,0)
- [ ] Grain is motion-tracked to prevent temporal sliding
- [ ] Deep operations completed before flattening to 2D
- [ ] No comp fixes applied beyond grain restoration and minor exposure trim (< 0.3 stops)
- [ ] Every pixel in final comp traces to a specific AOV contribution
- [ ] Color space is ACEScg throughout compositing (display transform at output only)
- [ ] Output conforms to `comp_delivery` schema from output-schemas
