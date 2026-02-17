---
name: deep-compositing
user-invocable: false
type: instruction
primary_owner: compositor
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Deep Compositing -- Volumetric DOF and Element Integration

Deep Before Flat. Always resolve deep compositing before flattening to 2D. Deep data
preserves per-sample depth, enabling volumetric depth of field, holdouts, and precise
element integration that is physically impossible in flat 2D space. Once deep data is
flattened, the per-sample information is destroyed and cannot be reconstructed.

> "You can always flatten a deep image. You can never deepen a flat one."

---

## Principle

Deep compositing stores multiple color and opacity samples per pixel, each tagged with
a depth value. For volumetric rendering of CO2 plumes, this means that a single pixel
may contain dozens of depth samples spanning the full extent of the volume. This
per-sample data enables three operations that are impossible in flat 2D compositing:

1. **Volumetric DOF** -- Defocus is applied per-sample based on distance from the focal
   plane. Each depth sample receives its own circle-of-confusion, producing physically
   correct bokeh through the volume rather than the uniform blur of a 2D DOF pass.

2. **Deep Merge** -- Two volumetric elements can be merged with correct depth ordering
   at the sub-pixel level. Overlapping volumes interpenetrate correctly without manual
   roto or edge work.

3. **Deep Holdout** -- A solid or volumetric element can cut a hole in another volume
   at the correct depth, preserving samples in front of and behind the holdout.

All deep operations must be completed before the image is flattened to 2D. The
flattening step collapses all depth samples into a single RGBA value per pixel --
after flattening, no depth-aware operation is possible.

---

## Procedure

### Step 1 -- Load Deep EXR with Per-Sample Data

Load the deep EXR file (`{shot}.{frame:04d}.deep.exr`) which contains per-sample
RGBA + depth data. Verify that the file is a genuine deep image (not a flat EXR with
a depth channel):

| Check | Expected | Failure Action |
|-------|----------|----------------|
| Sample count per pixel | Variable (1-128+) | If uniform 1, this is a flat image |
| Depth range | Matches scene scale (meters) | If all samples at same depth, degenerate |
| Alpha per sample | 0.0 - 1.0 | If all 1.0, volume is fully opaque (incorrect) |

### Step 2 -- Resolve Volumetric DOF Using Depth Samples

Apply depth of field to the deep image before flattening. Each depth sample receives a
circle-of-confusion (CoC) proportional to its distance from the focal plane:

```
CoC = abs(depth - focal_distance) * (aperture / focal_distance)
```

Samples near the focal plane remain sharp. Samples far from the focal plane blur
proportionally. Because each sample has its own depth, the DOF effect is volumetric --
the front of the plume can be sharp while the rear falls into soft bokeh, or vice versa.

Key parameters:

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `dof_focal_distance` | Distance from camera to focal plane (meters) | Scene-dependent |
| `dof_aperture` | Lens aperture for CoC calculation | 0.05 - 0.2 |
| `dof_max_coc` | Maximum circle of confusion (pixels) | 32 |
| `dof_quality` | Number of samples for bokeh kernel | 64 - 256 |

### Step 3 -- Apply Deep Merge for Element Integration

If multiple volumetric elements need to be combined (e.g., separate VDB passes, matte
elements, or cross-shot insertions), merge them using deep merge:

| Operation | Use Case | Behavior |
|-----------|----------|----------|
| Deep Merge | Two volumes occupying overlapping space | Interleave samples by depth, composite correctly |
| Deep Holdout | Solid element cutting through volume | Remove volume samples behind holdout surface |
| Deep Crop | Depth-range isolation | Keep only samples within specified depth range |

Deep merge interleaves samples from both images sorted by depth and composites them
in front-to-back order. This produces correct results even where the volumes
interpenetrate -- something that flat compositing cannot achieve.

### Step 4 -- Flatten to 2D

After all deep operations are complete, flatten the deep image to a standard 2D RGBA
image. Flattening composites all depth samples per pixel in front-to-back order:

```
for each pixel:
    sort samples by depth (front to back)
    composited_color = (0, 0, 0, 0)
    for each sample in sorted order:
        composited_color = over(sample, composited_color)
    output[pixel] = composited_color
```

After flattening, the image enters the flat compositing pipeline (multi-pass-integration,
grain restoration, delivery formatting).

---

## Parameters

### DOF Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `dof_focal_distance` | float | -- | scene-dependent | Distance to focal plane in meters |
| `dof_aperture` | float | 0.1 | 0.01 - 0.5 | Aperture for CoC calculation |
| `dof_max_coc` | int | 32 | 8 - 64 | Maximum circle of confusion in pixels |
| `dof_quality` | int | 128 | 64 - 256 | Bokeh kernel sample count |
| `dof_bokeh_shape` | string | circular | circular / hexagonal | Bokeh kernel shape |

### Deep Merge Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `deep_merge_tolerance` | float | 0.0001 | 0.00001 - 0.001 | Depth tolerance for sample consolidation |
| `deep_merge_max_samples` | int | 256 | 64 - 1024 | Max samples per pixel after merge |
| `deep_merge_consolidation` | bool | true | -- | Consolidate near-depth samples to save memory |

### Deep Holdout Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `holdout_mode` | string | opaque | opaque / volumetric |
| `holdout_depth_bias` | float | 0.001 | Depth bias to prevent z-fighting at holdout boundary |

---

## Anti-Patterns

### 1. Flattening Before Deep Operations

**Symptom:** Volumetric DOF produces a uniform blur across the entire plume instead of
depth-varying defocus. Or, merged elements show incorrect depth ordering with visible
compositing seams.

**Cause:** The deep EXR was flattened to 2D before DOF or merge operations were applied.
Once flattened, per-sample depth is lost and cannot be recovered.

**Fix:** Enforce the deep-before-flat rule. All deep operations (DOF, merge, holdout,
crop) must operate on the deep image. Flattening is the final step before the image
enters the flat compositing pipeline.

### 2. Losing Per-Sample Data

**Symptom:** Deep operations produce correct results on test frames but fail on production
frames with higher sample counts. Memory usage spikes or the deep merge silently drops
samples.

**Cause:** Deep merge consolidation is too aggressive, or max_samples is set too low for
the scene complexity. Samples are being discarded or merged when they should be preserved.

**Fix:** Set `deep_merge_max_samples` high enough for the scene (256-1024 for volumetric
CO2 plumes). Monitor sample counts per pixel after merge -- if they hit the max, increase
the limit or reduce consolidation tolerance.

### 3. DOF in 2D Space

**Symptom:** Depth of field is applied as a post-process blur on the flattened image. The
blur is uniform for all parts of the plume at the same screen position, regardless of
their actual depth. Nearby and distant parts of the volume receive identical defocus.

**Cause:** Using a 2D depth-of-field effect (Z-depth-driven blur on a flat image) instead
of per-sample deep DOF. 2D DOF cannot distinguish between multiple volume samples at the
same pixel but different depths.

**Fix:** Apply DOF before flattening, operating on per-sample deep data. Each sample
receives its own CoC based on its true depth. This produces physically correct volumetric
bokeh.

### 4. The Phantom Holdout

**Symptom:** A deep holdout appears to work on most of the image but leaves visible
artifacts at the holdout boundary -- faint halos or depth-fighting flicker.

**Cause:** Holdout depth bias is zero or too small, causing z-fighting between the holdout
surface and volume samples at the same depth. Or, holdout mode is set to opaque when the
holdout element is itself volumetric.

**Fix:** Apply a small depth bias (`holdout_depth_bias` = 0.001) to prevent z-fighting.
If the holdout element is volumetric (not a solid surface), use volumetric holdout mode
which computes per-sample alpha interaction instead of a binary depth cut.

---

## Validation Checklist

- [ ] Deep EXR loaded with variable sample counts per pixel (not flat)
- [ ] Sample depth range matches scene scale in meters
- [ ] All deep operations (DOF, merge, holdout) completed before flattening
- [ ] Volumetric DOF shows depth-varying defocus (front vs. rear of plume differ)
- [ ] Deep merge preserves correct depth ordering at element boundaries
- [ ] Sample count per pixel does not hit `deep_merge_max_samples` limit
- [ ] Holdout boundaries are clean (no halos or z-fighting artifacts)
- [ ] Flattened output is standard 2D RGBA with no residual deep data
- [ ] Pure black void (0,0,0) preserved after flattening -- no sample noise in void
- [ ] Deep merge tolerance appropriate for scene scale (default 0.0001)
- [ ] DOF focal distance set to a motivated depth within the plume structure
- [ ] Output conforms to `comp_delivery` schema from output-schemas
