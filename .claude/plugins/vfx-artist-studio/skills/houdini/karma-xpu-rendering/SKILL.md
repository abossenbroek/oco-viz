---
name: karma-xpu-rendering
user-invocable: false
type: instruction
primary_owner: houdini-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Karma XPU Rendering -- Render Configuration Per Tier

Karma XPU is the sole production renderer for the oco-viz Soot exhibition pipeline. Every
render setting -- samples, step size, bounces, denoiser, AOVs -- is specified per tier
(scout, preview, final) in the `karma-render-profiles.yaml` knowledge file. These settings
are not suggestions; they are the validated production configuration for RTX 6000 Ada
(48 GB VRAM) hardware. Deviating from the profile without explicit justification
introduces quality risk that compounds across 720 frames.

> "Render settings are engineering decisions, not creative preferences."

---

## Principle

The oco-viz pipeline renders volumes through Karma XPU's GPU+CPU hybrid architecture.
Each tier serves a distinct validation purpose: scout validates motion and timing,
preview validates lighting and materials, final delivers exhibition quality. The tier
settings are calibrated so that each tier accurately predicts the next -- a preview
that looks good will produce a good final render, and a scout that shows bad timing
will not improve at higher resolution. OIDN 2.3 temporal denoising is mandatory at
final tier, using the velocity grid as a motion buffer to eliminate frame-to-frame
flicker.

---

## Procedure

### Step 1 -- Select Tier Profile

Choose the tier based on the current validation stage:

| Tier | Resolution | SPP | Step Size | Bounces | Denoiser | Frame Time |
|------|-----------|-----|-----------|---------|----------|------------|
| Scout | 1920x1080 (HD) | 64 | 1.0x voxel | 2 vol / 1 scat | None | ~30 sec |
| Preview | 2048x1080 (2K DCI) | 256 | 0.75x voxel | 4 vol / 2 scat | OIDN optional | ~4 min |
| Final | 4096x2160 (4K DCI) | 512 | 0.5x voxel | 8 vol / 4 scat | OIDN 2.3 temporal | ~22 min |

**Step size formula:** `step_size = step_multiplier * voxel_spacing` where
`voxel_spacing = world_size / resolution` in meters.

### Step 2 -- Configure OIDN 2.3 Temporal Denoising

OIDN 2.3 is required at final tier and optional at preview:

| Setting | Value | Purpose |
|---------|-------|---------|
| `enabled` | true | Activate denoiser |
| `temporal` | true (final) / false (preview) | Temporal accumulation across frames |
| `motion_buffer` | "vel" | OpenVDB velocity grid name for temporal advection |
| `guide_albedo` | true | MaterialX scattering color as guide channel |
| `guide_normal` | true | Density gradient direction as guide channel |
| `prefilter` | "none" | Do not pre-filter guide channels |
| `hdr` | true | HDR input (ACEScg linear) |
| `clean_aux` | false | Noisy aux is acceptable for volumes |

**Why OIDN over OptiX:** OIDN 2.3 preserves grain in low-contrast monochrome content
(the Soot palette). OptiX over-smooths achromatic imagery, destroying the Paper Grain
Manifold (Technique 1) and film grain. OIDN's temporal mode uses the velocity grid to
advect denoiser state across frames, eliminating flicker.

**Guide channels are critical for Soot Crust:** Without albedo and normal guides, OIDN
cannot distinguish the matte-black crust (low albedo, steep gradient) from the
translucent interior (high albedo, shallow gradient), leading to over-smoothing of the
crust edge.

### Step 3 -- Configure AOV Slate

All AOVs are rendered per frame and packed into a single multi-layer EXR:

| AOV Name | LPE / Source | Format | Purpose |
|----------|-------------|--------|---------|
| `Beauty` | `lpe:C.*` | float16 RGB | Final denoised beauty (primary deliverable) |
| `NoisyBeauty` | `lpe:C.*` (pre-OIDN) | float16 RGB | Pre-denoiser beauty for grain restoration |
| `emission` | `lpe:Ce.*` | float16 RGB | Emission LPE -- curvature-driven glow isolation |
| `scatter` | `lpe:Cd.*` | float16 RGB | Diffuse/scatter LPE -- translucent interior |
| `density` | Volume density AOV | float32 mono | Raw density for comp adjustments |
| `deep` | Deep camera output | deep EXR | Per-sample depth for volumetric DOF |
| `velocity` | Velocity AOV | float16 RGB (xyz) | Motion vectors for temporal denoiser |
| `temperature` | Temperature AOV | float32 mono | Diagnostic: verify Kelvin values |

**NoisyBeauty is mandatory.** A 10-15% blend of NoisyBeauty over denoised Beauty
restores organic grain character while maintaining noise floor reduction.

### Step 4 -- Configure Adaptive Sampling

Adaptive sampling must use the `variance` metric, not luminance-weighted variance:

| Setting | Scout | Preview | Final |
|---------|-------|---------|-------|
| `enabled` | true | true | true |
| `threshold` | 0.05 | 0.02 | 0.01 |
| `min_samples` | 16 | 64 | 128 |
| `max_samples` | 64 | 256 | 512 |
| `metric` | -- | -- | variance |

**Why variance, not luminance-weighted:** The Soot aesthetic operates in the near-black
range (0.0-0.68). Luminance-weighted variance under-samples dark pixels because their
luminance contribution is low. Pure variance ensures dark regions receive sufficient
samples, preventing noise and banding in the critical 0.0-0.02 density range.

### Step 5 -- Run Pure Black Test

Before every render submission, render a single frame with an empty scene (no VDB loaded):

```
ALL pixels must be (0.0, 0.0, 0.0) with ZERO noise floor
```

If any pixel is non-zero, the scene has light leaks, ambient contribution, or renderer
bias. Diagnose and fix before proceeding.

**Background settings:**

| Setting | Value |
|---------|-------|
| `background_color` | (0.0, 0.0, 0.0) |
| `background_emission` | 0.0 |
| `environment_map` | None (no HDRI, no sky) |
| `ambient_occlusion` | false (AO implies ambient light) |

---

## Verified Code Templates

### Karma ROP Configuration in Hython

```python
#!/usr/bin/env hython
"""Configure Karma XPU ROP for a specific tier."""
from __future__ import annotations

import sys

import hou  # type: ignore[import-untyped]


# Tier profiles from karma-render-profiles.yaml
TIER_PROFILES = {
    "scout": {
        "resolution": (1920, 1080),
        "spp": 64,
        "step_multiplier": 1.0,
        "shadow_step_multiplier": 2.0,
        "max_volume_bounces": 2,
        "scattering_bounces": 1,
        "pixel_filter": "box",
        "pixel_filter_width": 1.0,
        "denoiser_enabled": False,
        "adaptive_threshold": 0.05,
        "adaptive_min": 16,
        "adaptive_max": 64,
    },
    "preview": {
        "resolution": (2048, 1080),
        "spp": 256,
        "step_multiplier": 0.75,
        "shadow_step_multiplier": 1.0,
        "max_volume_bounces": 4,
        "scattering_bounces": 2,
        "pixel_filter": "gaussian",
        "pixel_filter_width": 2.0,
        "denoiser_enabled": True,
        "denoiser_temporal": False,
        "adaptive_threshold": 0.02,
        "adaptive_min": 64,
        "adaptive_max": 256,
    },
    "final": {
        "resolution": (4096, 2160),
        "spp": 512,
        "step_multiplier": 0.5,
        "shadow_step_multiplier": 0.5,
        "max_volume_bounces": 8,
        "scattering_bounces": 4,
        "pixel_filter": "gaussian",
        "pixel_filter_width": 3.0,
        "denoiser_enabled": True,
        "denoiser_temporal": True,
        "adaptive_threshold": 0.01,
        "adaptive_min": 128,
        "adaptive_max": 512,
    },
}


def configure_karma_rop(
    stage_node: hou.Node,
    tier: str,
    voxel_spacing: float,
    frame_range: tuple[int, int] = (1, 720),
    output_dir: str = "$HIP/render",
) -> hou.Node:
    """Create and configure a Karma XPU ROP for the specified tier.

    Parameters
    ----------
    stage_node : hou.Node
        The LOP node providing the USD stage.
    tier : str
        Render tier: "scout", "preview", or "final".
    voxel_spacing : float
        VDB voxel spacing in meters (world_size / resolution).
    frame_range : tuple[int, int]
        Start and end frame numbers.
    output_dir : str
        Output directory for rendered EXR files.
    """
    if tier not in TIER_PROFILES:
        msg = f"Unknown tier '{tier}'. Must be: {list(TIER_PROFILES.keys())}"
        raise ValueError(msg)

    profile = TIER_PROFILES[tier]

    # Create Karma ROP
    karma = stage_node.parent().createNode("karmarendersettings", f"karma_{tier}")
    karma.setInput(0, stage_node)

    # Resolution
    res_x, res_y = profile["resolution"]
    karma.parm("resolutionx").set(res_x)
    karma.parm("resolutiony").set(res_y)

    # Sampling
    karma.parm("samplesperpixel").set(profile["spp"])

    # Volume step size
    step_size = profile["step_multiplier"] * voxel_spacing
    shadow_step = profile["shadow_step_multiplier"] * voxel_spacing
    karma.parm("volumestepsize").set(step_size)
    karma.parm("shadowstepsize").set(shadow_step)

    # Bounces
    karma.parm("maxvolumebounces").set(profile["max_volume_bounces"])
    karma.parm("scatteringbounces").set(profile["scattering_bounces"])

    # Pixel filter
    karma.parm("pixelfilter").set(profile["pixel_filter"])
    karma.parm("pixelfilterwidth").set(profile["pixel_filter_width"])

    # Adaptive sampling
    karma.parm("adaptivethreshold").set(profile["adaptive_threshold"])
    karma.parm("adaptiveminsamples").set(profile["adaptive_min"])
    karma.parm("adaptivemaxsamples").set(profile["adaptive_max"])

    # Denoiser
    if profile["denoiser_enabled"]:
        karma.parm("denoiseenable").set(True)
        karma.parm("denoisetype").set("oidn")
        if profile.get("denoiser_temporal"):
            karma.parm("denoisetemporal").set(True)
            karma.parm("denoisemotionbuffer").set("vel")
        karma.parm("denoisealbedo").set(True)
        karma.parm("denoisenormal").set(True)

    # Background (pure black void)
    karma.parm("backgroundcolor").set((0.0, 0.0, 0.0))

    # Frame range
    karma.parm("f1").set(frame_range[0])
    karma.parm("f2").set(frame_range[1])

    # Output path
    shot_name = hou.hipFile.basename().replace(".hip", "")
    karma.parm("picture").set(
        f"{output_dir}/{shot_name}.$F4.exr",
    )

    return karma


def add_aov_slate(karma_rop: hou.Node) -> None:
    """Add the full AOV slate to a Karma ROP.

    Parameters
    ----------
    karma_rop : hou.Node
        The Karma render settings node.
    """
    aovs = [
        ("Beauty", "lpe:C.*", "float16"),
        ("NoisyBeauty", "lpe:C.*", "float16"),  # pre-OIDN
        ("emission", "lpe:Ce.*", "float16"),
        ("scatter", "lpe:Cd.*", "float16"),
        ("density", "volume_density", "float32"),
        ("velocity", "velocity", "float16"),
        ("temperature", "temperature", "float32"),
    ]

    for i, (name, lpe, fmt) in enumerate(aovs):
        karma_rop.parm(f"aov{i}_name").set(name)
        karma_rop.parm(f"aov{i}_lpe").set(lpe)
        karma_rop.parm(f"aov{i}_format").set(fmt)


def main() -> int:
    """Configure Karma ROP from command line."""
    tier = sys.argv[1] if len(sys.argv) > 1 else "scout"
    voxel_spacing = float(sys.argv[2]) if len(sys.argv) > 2 else 0.01

    hou.hipFile.load(sys.argv[3] if len(sys.argv) > 3 else "scene.hip")

    stage = hou.node("/stage/scene")
    if not stage:
        print("ERROR: /stage/scene not found", file=sys.stderr)
        return 1

    try:
        karma = configure_karma_rop(stage, tier, voxel_spacing)
        add_aov_slate(karma)
    except (hou.OperationFailed, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    hou.hipFile.save()
    print(f"SUCCESS: Karma {tier} ROP configured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## Parameters

### Tier Settings (from karma-render-profiles.yaml)

| Parameter | Scout | Preview | Final |
|-----------|-------|---------|-------|
| `resolution` | 1920x1080 | 2048x1080 | 4096x2160 |
| `samples_per_pixel` | 64 | 256 | 512 |
| `volume_step_multiplier` | 1.0 | 0.75 | 0.5 |
| `shadow_step_multiplier` | 2.0 | 1.0 | 0.5 |
| `max_volume_bounces` | 2 | 4 | 8 |
| `scattering_bounces` | 1 | 2 | 4 |
| `pixel_filter` | box | gaussian | gaussian |
| `pixel_filter_width` | 1.0 | 2.0 | 3.0 |
| `denoiser_enabled` | false | true (optional) | true (required) |
| `denoiser_temporal` | -- | false | true |
| `adaptive_threshold` | 0.05 | 0.02 | 0.01 |
| `adaptive_min_samples` | 16 | 64 | 128 |
| `adaptive_max_samples` | 64 | 256 | 512 |
| `adaptive_metric` | -- | -- | variance |
| `approx_frame_time` | ~30 sec | ~4 min | ~22 min |

### OIDN 2.3 Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `motion_buffer` | string | vel | VDB grid name for temporal advection |
| `guide_albedo` | bool | true | Use MaterialX scattering color as guide |
| `guide_normal` | bool | true | Use density gradient as guide |
| `prefilter` | string | none | Do not pre-filter guide channels |
| `hdr` | bool | true | HDR input (ACEScg linear) |
| `clean_aux` | bool | false | Noisy aux acceptable for volumes |

### Background Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `background_color` | color3 | (0, 0, 0) | Pure black background |
| `background_emission` | float | 0.0 | No background emission |
| `environment_map` | string | null | No HDRI or sky |
| `ambient_occlusion` | bool | false | Disabled (AO implies ambient light) |

---

## Anti-Patterns

### 1. The Luminance-Weighted Adaptive

**Symptom:** Near-black regions of the render show visible noise, fireflies, or banding.
The plume's low-density halo is grainy while the bright interior is clean.

**Cause:** Adaptive sampling uses luminance-weighted variance as the convergence metric.
Dark pixels have low luminance, so the adaptive sampler concludes they have "converged"
and reduces sample count -- but the actual variance in the near-black range is still
perceptually significant.

**Fix:** Use pure `variance` metric at final tier. This ensures dark regions in the
0.0-0.02 density range receive full sample allocation. The min_samples floor of 128
provides a safety net for the darkest pixels.

### 2. The Missing NoisyBeauty

**Symptom:** The denoised beauty is clean but sterile. The organic grain character of
the Soot aesthetic is lost. The render looks digital and processed.

**Cause:** Only the denoised Beauty AOV is rendered. The pre-denoiser NoisyBeauty is
not captured.

**Fix:** Always render NoisyBeauty alongside Beauty. In compositing, blend 10-15%
of NoisyBeauty over Beauty using motion-tracked grain restoration. This restores the
organic texture that OIDN removes while maintaining the denoiser's noise floor reduction.

### 3. The Skipped Black Test

**Symptom:** Final renders show a faint ambient glow in what should be pure black void.
The #000000 background has a non-zero noise floor. Gallery projection reveals the
contamination as a visible grey haze.

**Cause:** No empty-scene render was done before submitting the full sequence. A light
leak, stray ambient contribution, or renderer bias went undetected.

**Fix:** Before every render submission, render one frame with no VDB loaded. Every
pixel must be exactly (0.0, 0.0, 0.0). Any non-zero pixel indicates light leaks
(check environment_map, ambient_occlusion, background_emission). Fix the source, do
not attempt to subtract the bias in compositing.

### 4. The Wrong Step Size

**Symptom:** Visible stepping artifacts in the volume -- horizontal or vertical banding
visible in smooth density gradients, especially at low density.

**Cause:** Volume step size too large for the render resolution. Using scout-tier step
size (1.0x voxel) at final-tier resolution (4K).

**Fix:** Use the step multiplier from the tier profile:
`step_size = multiplier * voxel_spacing`. Final tier uses 0.5x, which eliminates
stepping artifacts at 4K. Do not go below 0.25x without justification -- diminishing
returns with 2x+ render time increase.

---

## Validation Checklist

- [ ] Tier profile selected from karma-render-profiles.yaml
- [ ] Resolution matches tier: HD (scout), 2K DCI (preview), 4K DCI (final)
- [ ] Samples per pixel matches tier: 64 / 256 / 512
- [ ] Volume step size = multiplier * voxel_spacing (not hardcoded)
- [ ] Shadow step size set per tier
- [ ] Max volume bounces set per tier: 2 / 4 / 8
- [ ] Scattering bounces set per tier: 1 / 2 / 4
- [ ] OIDN 2.3 enabled at final tier with temporal mode
- [ ] Motion buffer set to "vel" for temporal denoiser
- [ ] Guide channels (albedo, normal) enabled for OIDN
- [ ] Adaptive sampling metric is "variance" (not luminance-weighted) at final
- [ ] All 8 AOVs configured: Beauty, NoisyBeauty, emission, scatter, density, deep, velocity, temperature
- [ ] NoisyBeauty captured (pre-OIDN) for grain restoration
- [ ] Background color is (0, 0, 0), no environment map, no AO
- [ ] Pure black test passed: empty scene renders all-zero pixels
- [ ] EXR output path follows naming convention: {shot}/{shot}.$F4.exr
