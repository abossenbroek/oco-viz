# Render Farm Specification

## Karma XPU Production Rendering for Soot Exhibition

**Version:** 1.0
**Renderer:** Karma XPU (sole production renderer)
**Farm:** AWS Deadline or HQueue
**Target:** 720 frames (30 sec @ 24 fps), 4K DCI (4096x2160)

---

## Renderer Selection

### Karma XPU -- Sole Renderer

Karma XPU is the sole production renderer. RenderMan is removed from the critical path.

**Rationale:**

- GPU+CPU hybrid rendering: full CUDA acceleration on RTX 6000 Ada.
- Native USD/Solaris integration: no scene translation overhead.
- MaterialX `standard_volume` support for the Soot Crust dual-state shader (see `plan/lookdev_bible.md`, Technique 6).
- OIDN 2.3 integration for temporal denoising.
- Single renderer simplifies farm configuration, AOV naming, and compositing templates.

**RenderMan RIS upgrade path (optional):** If near-black bit-depth proves insufficient in Karma XPU (quantization artifacts in the 0.0-0.02 density range where exhibition TF has its steepest opacity ramp), evaluate RenderMan RIS with its deep sample architecture. This is a contingency, not a planned dependency.

---

## Tier Settings

### Resolution and Quality

| Parameter | Scout | Preview | Final |
|-----------|-------|---------|-------|
| VDB Resolution | 128^3 | 512^3 | 1024^3 |
| Render Resolution | 1920x1080 (HD) | 2048x1080 (2K DCI) | 4096x2160 (4K DCI) |
| Samples per Pixel | 64 spp | 256 spp | 512 spp + OIDN |
| ML Denoiser | None | Optional OIDN | OIDN 2.3 temporal |
| Approx. Frame Time | ~30 sec | ~4 min | ~22 min |
| Volume Step Size | 1.0x voxel size | 0.75x voxel size | 0.5x voxel size |
| Shadow Step Size | 2.0x voxel size | 1.0x voxel size | 0.5x voxel size |
| Max Volume Bounces | 2 | 4 | 8 |
| Scattering Bounces | 1 | 2 | 4 |
| Pixel Filter | box, 1px | gaussian, 2px | gaussian, 3px |

### Volume Rendering Step Size

Step size directly controls volumetric quality and render time.

```
step_size = step_multiplier * voxel_spacing
```

Where `voxel_spacing = world_size / resolution` (meters).

| Tier | Step Multiplier | Effect |
|------|-----------------|--------|
| Scout | 1.0x | Fast, acceptable for timing/motion validation |
| Preview | 0.75x | Good quality, reveals lighting and material issues |
| Final | 0.5x | Maximum quality, no stepping artifacts at 4K |

**Critical:** Step size below 0.5x voxel size yields diminishing returns with 2x+ render time increase. Do not go below 0.25x without explicit justification.

---

## ML Denoiser: OIDN 2.3

### Why OIDN (Not OptiX)

Intel Open Image Denoise 2.3 is preferred over NVIDIA OptiX denoiser because:

1. **Grain preservation on achromatic content.** OptiX tends to over-smooth low-contrast monochrome imagery, destroying the Paper Grain Manifold (Technique 1) and film grain added in compositing. OIDN 2.3 better preserves fine detail in low-variance regions.
2. **Temporal stability.** OIDN 2.3 supports temporal advection using the velocity grid as a motion buffer, eliminating frame-to-frame flicker.
3. **NoisyBeauty grain restoration.** The NoisyBeauty AOV (pre-denoiser beauty) is retained for compositing. A motion-tracked 10-15% blend of NoisyBeauty over the denoised Beauty restores organic grain character while maintaining the denoiser's noise floor reduction.

### OIDN Configuration

```python
# Karma XPU OIDN settings (Solaris ROP)
oidn_enabled = True
oidn_temporal = True                # temporal accumulation
oidn_motion_buffer = "vel"          # OpenVDB velocity grid name
oidn_guide_albedo = True            # albedo AOV guide channel
oidn_guide_normal = True            # normal (density gradient) guide channel
oidn_prefilter = "none"             # do not pre-filter guide channels
oidn_hdr = True                     # HDR input (ACEScg linear)
oidn_clean_aux = False              # noisy aux is fine for volumes
```

### AOV Guide Channels

| Guide Channel | Source | Purpose |
|---------------|--------|---------|
| Albedo | MaterialX `standard_volume` scattering color | Tells denoiser where material boundaries are |
| Normal | Density gradient direction `normalize(grad(density))` | Tells denoiser surface orientation for edge preservation |

These guide channels are critical for the Soot Crust shader. Without them, OIDN cannot distinguish the matte-black crust (low albedo, steep gradient) from the translucent interior (high albedo, shallow gradient), leading to over-smoothing of the crust edge.

---

## Multi-Pass / LPE Strategy

### AOV Manifest

All passes rendered per frame. AOV naming follows Karma/Solaris conventions.

| AOV Name | LPE / Source | Format | Purpose |
|----------|-------------|--------|---------|
| `Beauty` | `C.*` | float16 RGB | Final denoised beauty (primary deliverable) |
| `NoisyBeauty` | `C.*` (pre-OIDN) | float16 RGB | Pre-denoiser beauty for grain restoration |
| `emission` | `Ce.*` | float16 RGB | Emission LPE -- curvature-driven glow isolation |
| `scatter` | `Cd.*` | float16 RGB | Diffuse/scatter LPE -- translucent interior light transport |
| `density` | Volume density AOV | float32 mono | Raw density field for comp adjustments |
| `deep` | Deep camera output | deep EXR | Per-sample depth for volumetric DOF and deep compositing |
| `velocity` | Velocity AOV | float16 RGB (xyz) | Motion vectors for temporal denoiser and motion blur |
| `temperature` | Temperature AOV | float32 mono | Diagnostic: verify Kelvin values, creative re-grade potential |

### LPE Expressions

```
# Karma XPU LPE syntax
Beauty:       lpe:C.*
Emission:     lpe:Ce.*
Scatter:      lpe:Cd.*
```

### EXR Channel Layout

All AOVs packed into a single multi-layer EXR per frame:

```
Beauty.R, Beauty.G, Beauty.B
NoisyBeauty.R, NoisyBeauty.G, NoisyBeauty.B
emission.R, emission.G, emission.B
scatter.R, scatter.G, scatter.B
density.Y
velocity.X, velocity.Y, velocity.Z
temperature.Y
```

Deep samples stored in separate deep EXR file per frame.

**File naming:**

```
{shot}/render/{shot}.{frame:04d}.exr        # multi-layer AOVs
{shot}/render/{shot}.{frame:04d}.deep.exr    # deep samples
```

---

## The Black Void Challenge

The Soot visual language demands pure black background (#000000) with volumetric content in the achromatic range 0.0-0.68. This creates specific technical challenges.

### Problem: Near-Black Quantization

At 16-bit half-float EXR, the smallest representable positive value is ~5.96e-8. However, the perceptual difference between 0.0 and 0.001 is significant in a dark gallery environment on a high-contrast display. Noise floor from the renderer can produce visible fireflies or banding in the 0.0-0.01 range.

### Solutions

**1. Dithering at 16-bit EXR:**

```
# Post-render dithering pass (Nuke or Python)
dither_amplitude = 0.5 / 65535  # 0.5 LSB at 16-bit
dither_noise = blue_noise_2d(width, height) * dither_amplitude
output = render + dither_noise
```

Blue noise dithering (not white noise) prevents visible pattern/grain in dark regions.

**2. Max-samples push in dark regions:**

Karma XPU's adaptive sampling must be configured to NOT reduce samples in dark regions. Override the adaptive threshold for pixels where estimated luminance < 0.01:

```
# Karma adaptive sampling overrides
adaptive_threshold = 0.01        # noise threshold for adaptive sampling
min_samples = 128                # minimum samples even in "converged" dark regions
max_samples = 512                # upper bound (matches final tier spp)
adaptive_metric = "variance"     # use variance, not luminance-weighted variance
```

The `variance` metric (not luminance-weighted) ensures dark regions receive sufficient samples. Luminance-weighted variance would under-sample dark pixels.

**3. Pure black test:**

Before every render submission, render a single frame with an empty scene (no VDB loaded). The result must be:

```
ALL pixels == (0.0, 0.0, 0.0) with ZERO noise floor
```

If any pixel is non-zero, the scene has light leaks, ambient contribution, or renderer bias. Fix before proceeding.

**4. Background handling:**

```
# Karma background settings
background_color = (0.0, 0.0, 0.0)
background_emission = 0.0
environment_map = None            # no HDRI, no sky
ambient_occlusion = False         # no AO (implies ambient light)
```

---

## Render Farm Orchestration

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Scheduler | AWS Deadline or HQueue | Job submission, dependency management, auto-retry |
| Compute | RTX 6000 Ada (48GB VRAM) | GPU rendering nodes |
| Storage | S3/EFS or shared NFS | VDB caches, EXR output |
| Monitoring | Deadline Monitor or HQueue web UI | Progress tracking, error detection |
| Notification | Webhooks (Slack/email) | Frame completion, error alerts |

### Job Submission

All render submissions via Hython (Houdini Python) for reproducibility:

```bash
hython render_submit.py \
    --hip {scene}.hip \
    --rop /stage/karma_rop \
    --frame-range 1-720 \
    --chunk-size 10 \
    --tier final \
    --priority 50
```

**Chunk size:** 10 frames per task. Balances farm utilization (enough parallelism) against task overhead (checkpoint/resume cost). GPU OOM is most likely on the first frame of a chunk (cold start), so smaller chunks limit wasted work on retry.

### Auto-Retry on GPU OOM

GPU out-of-memory is the most common render failure on volumetric scenes.

```
# Deadline/HQueue retry policy
max_retries = 3
retry_delay = 60  # seconds

# Retry escalation:
# Attempt 1: same settings
# Attempt 2: reduce max_samples to 384 (75% of final)
# Attempt 3: reduce render resolution to 3072x1620 (75% of 4K), upscale in comp
# Attempt 4 (manual): split frame into tiles, render tiles separately
```

### Webhooks

| Event | Action |
|-------|--------|
| Frame complete | POST to monitoring endpoint with frame number, render time, peak VRAM |
| Chunk complete | Trigger thumbnail generation for visual QA |
| Job error | Alert via Slack webhook with error log snippet |
| Job complete | Trigger compositing template auto-generation (see `plan/finishing_spec.md`) |
| Every 10th frame | Side-by-side comparison against preview render |

---

## Budget Estimate

### Final Tier (720 frames, 4K DCI, 512 spp + OIDN)

| Item | Calculation | Cost |
|------|-------------|------|
| Render time | 720 frames x 22 min/frame = 264 GPU-hours | -- |
| GPU cost | 264 hrs x ~$1.10/hr (RTX 6000 Ada spot) | ~$290 |
| Storage (EXR) | 720 frames x ~150 MB/frame (multi-layer) = ~105 GB | ~$3 |
| Storage (deep) | 720 frames x ~80 MB/frame = ~56 GB | ~$2 |
| Storage (VDB cache) | ~200 GB (1024^3 sequence) | ~$5 |
| Network egress | ~360 GB download | ~$33 |
| **Total final render** | | **~$333** |

### Contact Sheet Wedge (100 frames, see `plan/lookdev_bible.md` Technique 7)

| Item | Calculation | Cost |
|------|-------------|------|
| Render time | 100 frames x 22 min/frame = ~37 GPU-hours | -- |
| GPU cost | 37 hrs x ~$1.10/hr | ~$41 |

### Preview Tier (720 frames, 2K, 256 spp)

| Item | Calculation | Cost |
|------|-------------|------|
| Render time | 720 frames x 4 min/frame = 48 GPU-hours | -- |
| GPU cost | 48 hrs x ~$1.10/hr | ~$53 |

### Scout Tier (720 frames, HD, 64 spp)

| Item | Calculation | Cost |
|------|-------------|------|
| Render time | 720 frames x 0.5 min/frame = 6 GPU-hours | -- |
| GPU cost | 6 hrs x ~$1.10/hr | ~$7 |

### Total Per Shot (All Tiers)

| Phase | GPU-Hours | Estimated Cost |
|-------|-----------|----------------|
| Scout | 6 | $7 |
| Contact sheet wedge | 37 | $41 |
| Preview | 48 | $53 |
| Final | 264 | $333 |
| **Total per shot** | **355** | **~$434** |

**For a 6-shot exhibition ("Descent of Carbon"):** ~2,130 GPU-hours, ~$2,600 in compute. Add 20% contingency for re-renders: **~$3,120 total render budget.**

---

## Progressive Validation Integration

Follows the coding guide philosophy: "Fix it in pre, not post."

```
Scout (128^3, 64 spp, HD)
  |-- Approve: motion, timing, creative direction
  |-- Fail: regenerate VDB, do not proceed
  v
Contact Sheet Wedge (1024^3, 512 spp, 4K, 100 variations)
  |-- Approve: lookdev locked on paper (3-day time-box)
  |-- Fail: revise lookdev parameters, re-wedge
  v
Preview (512^3, 256 spp, 2K)
  |-- Approve: lighting, materials, technical settings
  |-- Fail: adjust settings, re-render affected frames
  v
Final (1024^3, 512 spp + OIDN, 4K)
  |-- QA: every 10th frame vs. preview side-by-side
  |-- Complete: trigger compositing pipeline
```

**Gate discipline:** Each tier must pass before the next begins. No skipping scout, no rendering final without preview approval. The contact sheet wedge (Technique 7) is a gate between scout and preview -- lookdev must be locked before committing to preview render time.

---

**Document Type:** Production Rendering Specification
**Depends On:** `plan/coding_guide_2026.md`, `plan/lookdev_bible.md`
**Feeds Into:** `plan/finishing_spec.md`, farm orchestration scripts
