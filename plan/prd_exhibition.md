# Exhibition PRD v3.0: "Soot" — Sasol Secunda CO2 Atmospheric Visualization

**Version**: 3.0
**Status**: Active
**Supersedes**: [`plan/prd.md`](prd.md) (v2.0 baseline)
**Last Updated**: February 2026

---

## Executive Summary

This PRD scopes all remaining work to take the oco-viz pipeline from its current state — a functional VTK-based volumetric renderer with Soot transfer functions, advection, and OpenVDB export — to a gallery-wall-ready exhibition piece. The work is organized into nine phases, from shot design lock through conservation packaging, with a single critical path suitable for a one-person team.

> **Stage 0 — VTK Pre-Viz (current):** The VTK pipeline produces study-grade pre-visualization imagery. This is sufficient for creative direction, timing, composition, and transfer function iteration. It is *not* exhibition-quality — that requires the Karma XPU production renderer (Stage 1+, Waves 12-13). All quality claims in this document should be read against this staging: "exhibition-quality" refers to the target output of the full pipeline, not the current VTK stage alone.

**Subject**: Sasol Secunda coal-to-liquids complex, Mpumalanga, South Africa. 57 Mt CO2/year — one of the largest single-point sources on Earth. Made visible as choking industrial soot against black void.

**Visual language**: "Soot" — anthropocene industrial dread. Achromatic. No external lighting. Internal smoldering only. See [`plan/visual_language.yaml`](visual_language.yaml) for the machine-readable specification.

**Target output**: 6-shot sequence, 4:5 aspect ratio, Karma XPU rendered, exhibition-grade prints on Hahnemuhle Photo Rag Baryta 315 gsm, and a looping video installation. Each deliverable must survive projection at 4K on a gallery wall and scrutiny on baryta paper at arm's length.

---

## Current State

### Built (Waves 1-6, done)

| Module | Capability | Key Files |
|--------|-----------|-----------|
| Config | Pydantic v2 schemas, YAML layered loading, tier system | `src/oco_viz/config/schema.py` |
| Data | xarray/zarr pipelines, CAMS forecast, ERA5 winds, OCO-3 L2 | `src/oco_viz/data/` |
| Plume | Gaussian plume, turbulent compositor, MacCormack advection | `src/oco_viz/plume/` |
| Render | VTK GPU volume rendering, Soot TF, scattering, frame writer | `src/oco_viz/render/` |
| Post | ACES Narkowicz tonemap, bloom, fog, 16-bit PNG output | `src/oco_viz/postprocess/tonemap.py` |
| Sequencer | Animation sequencer, easing, VDB single-grid export | `src/oco_viz/sequencer/vdb_export.py` |

### Remaining (Waves 7-9, in tickets)

Waves 7-9 cover composition automation, overlay rendering, and validation pipeline. These must complete before exhibition pipeline work begins.

### Gap Analysis

| Capability | Current | Required for Exhibition |
|-----------|---------|----------------------|
| Color management | Narkowicz ACES approximation | Full ACES/OCIO, ACEScg working space, EXR output |
| VDB export | Single `density` grid, Float32 | Multi-grid (density/vel/temperature/dissolution_mask), metadata, domain falloff |
| Scene export | None | USD scene with camera, MaterialX Soot shader |
| Renderer | VTK software/GPU | Karma XPU with OIDN 2.3 temporal denoise |
| Compositing | PIL frame writer | Nuke MCP multi-pass, grain, OCIO output transforms |
| Output format | 16-bit PNG, 16:9 | EXR multi-pass, 4:5 aspect, print-ready TIFF |
| Print pipeline | None | ICC profiled, baryta paper, Dmax optimization |
| Installation spec | None | Technical rider, display/acoustic/spatial requirements |

---

## Phase 0a: Shot Design & Creative Lock

**Goal**: Lock the 6-shot "Descent of Carbon" arc before any production rendering begins. No pixels are wasted on unlocked creative direction.

**Deliverables**:

- 6-shot storyboard with camera motion language per shot (see [`plan/shot_design.md`](shot_design.md))
- 4:5 aspect ratio confirmed for all shots (portrait orientation, gallery wall)
- Camera motion vocabulary: static hold, glacial drift, imperceptible push-in, orbital sweep
- "Ghost light" specification — the sole internal smoldering source, positioned per-shot for compositional weight
- Print hero frame selection — 2-3 frames designated for archival print from the full sequence
- Motion timing locked at scout resolution (128 cubed) before proceeding

**Quality gate**: Director sign-off on scout playback at 24 fps. Motion timing, shot transitions, and overall arc approved before any preview-resolution work.

**Exit criteria**: Shot design document complete, scout approved, no creative ambiguity remaining.

---

## Phase 0: Complete Current Waves 7-9

**Goal**: Finish all existing ticket work before beginning the exhibition pipeline.

**Scope**: Waves 7 (composition automation), 8 (overlay rendering), and 9 (validation pipeline) as specified in `plan/tickets/7-*.yaml` through `plan/tickets/9-*.yaml`.

**Rationale**: The exhibition pipeline builds on the foundation these waves establish. Composition automation (Wave 7) provides the camera targeting that Phase 0a's shot design depends on. Validation (Wave 9) provides the scientific credibility that distinguishes this work from pure generative art.

**Exit criteria**: All Wave 7-9 tickets at status `done`. `pixi run ci` passes.

---

## Phase 1: Scene-Referred Pipeline & Color Management

**Goal**: Replace the current Narkowicz ACES approximation with a proper scene-referred color pipeline. Every pixel from VTK generation through final delivery lives in a defined color space with traceable transforms.

### 1.1 ACES/OCIO Integration

| Component | Specification |
|-----------|--------------|
| Working space | ACEScg (AP1 primaries, linear) |
| OCIO config | `aces_1.3` (bundled, not custom) |
| Input transform | VTK linear RGB -> ACEScg (identity for achromatic Soot) |
| View transform | ACES 1.3 Output Transform (Rec.709 for video, P3 for projection) |
| Rendering intent | Scene-referred throughout; display-referred only at final output |

### 1.2 EXR Writer

Replace `save_frame_16bit` (PIL-based PNG) with OpenEXR output:

| Parameter | Value |
|-----------|-------|
| Format | OpenEXR 2.x, half-float (Float16) per channel |
| Compression | DWAA (lossy, fast, small files) or ZIP (lossless for hero frames) |
| Channels | R, G, B (beauty) + depth (Z) + density AOV + emission AOV |
| Metadata | OCIO colorspace tag, frame number, timestamp, tier |

### 1.3 Print-Ready TIFF

For archival print pipeline (Phase 6), add TIFF output:

| Parameter | Value |
|-----------|-------|
| Format | TIFF, 16-bit per channel |
| Color space | Adobe RGB (1998) for print, embedded ICC |
| Resolution | 300 DPI at target print dimensions |
| Sharpening | Unsharp mask tuned for baryta inkjet (radius 0.8px, amount 40%) |

### Code Changes

| File | Change |
|------|--------|
| `src/oco_viz/render/frame_writer.py` | Add `save_frame_exr()`, `save_frame_tiff()` |
| `src/oco_viz/postprocess/tonemap.py` | Replace Narkowicz with OCIO `aces_1.3` processor |
| `src/oco_viz/config/schema.py` | Add `ColorManagementConfig` with OCIO config path |
| `configs/base.yaml` | Add `color_management` section |

---

## Phase 1b: OpenVDB Production-Grade Export

**Goal**: Upgrade the current single-grid VDB export to a production multi-grid format suitable for Houdini/Karma ingestion without manual cleanup.

### Multi-Grid Specification

| Grid | Type | Unit | Purpose |
|------|------|------|---------|
| `density` | Float32 scalar | Normalized 0-1 | Primary volume density |
| `vel` | Vec3f | m/s | Velocity field for motion blur and advection |
| `temperature` | Float32 scalar | Kelvin | Internal emission temperature (smoldering glow) |
| `dissolution_mask` | Float32 scalar | Normalized 0-1 | Edge dissolution intensity for Soot Crust lookdev |

### Metadata

Every VDB file must carry embedded metadata:

```
origin_lat, origin_lon, voxel_size_m, timestamp_iso,
tier, wave, git_sha, colorspace (ACEScg),
domain_extent_km, grid_resolution
```

### Domain Boundary Falloff

Cosine-ramp falloff over outermost 8% of each axis. Prevents hard box edges that break the volumetric illusion. The falloff applies to the density grid only — velocity and temperature extend to the full domain for physical consistency at boundaries.

### Quality Gates (Delivery Only)

| Gate | Check | Threshold |
|------|-------|-----------|
| Sparsity | Active voxel ratio | < 20% (> 80% sparse) |
| Value range | density in [0, 1], temperature in [200K, 3000K] | Strict bounds |
| Grid completeness | All 4 grids present | Required |
| Metadata | All required fields present | Required |
| Falloff | Boundary voxels < 0.01 density | Spot check outer 2 slices |

Exploration VDBs skip all gates for iteration speed.

### Code Changes

| File | Change |
|------|--------|
| `src/oco_viz/sequencer/vdb_export.py` | Multi-grid export, metadata embedding, domain falloff |
| `src/oco_viz/config/schema.py` | Add `VDBExportConfig` with grid list, falloff params |

---

## Phase 1c: Lookdev Bible — "The Soot Crust"

**Goal**: Define and implement the 7 signature techniques that give the Soot aesthetic its distinctive character. This is the lookdev specification that all downstream rendering must match.

See [`plan/lookdev_bible.md`](lookdev_bible.md) for the full specification. The 7 techniques:

1. **Crust formation** — Hardened outer shell with sub-surface translucency
2. **Internal smoldering** — Deep interior glow, light suffocated by density
3. **Granular dissolution** — Edge breakup into discrete soot particles
4. **Geological folding** — Multi-octave turbulence with sedimentary character
5. **Achromatic depth** — Full tonal range within strict R=G=B constraint
6. **Gravity settling** — Downward drift at plume base, heavy particulate behavior
7. **Temporal creep** — Imperceptible motion that reveals itself over 10+ seconds

Each technique maps to specific MaterialX shader parameters and VDB grid requirements documented in the lookdev bible.

---

## Phase 2: USD Scene Export & Houdini Bridge

**Goal**: Export complete USD scenes from oco-viz that load directly into Houdini Solaris for Karma XPU rendering, with no manual setup required.

### USD Exporter

| Component | Specification |
|-----------|--------------|
| Format | USD binary (.usdc) |
| Volume | VDB reference prim (points to Phase 1b VDB files) |
| Camera | Translated from `CameraConfig` — FOV, aspect 4:5, near/far clip |
| Material | MaterialX Soot shader (see below) |
| Lights | **None** — no light prims. Internal smoldering comes from emission in the shader |
| Animation | Per-frame VDB file references, camera keyframes with easing |

### MaterialX Soot Shader

Built on `standard_volume` (MaterialX 1.39+):

| Parameter | Value | Source |
|-----------|-------|--------|
| `absorption` | Achromatic, driven by density grid | `visual_language.yaml` palette |
| `scattering` | Forward bias, anisotropy 0.8 | Higher than VTK (0.35) to compensate for path-traced multi-bounce |
| `emission` | Temperature-driven via `temperature` grid, heavily attenuated | Smoldering glow spec |
| `density_scale` | Non-linear ramp (exponential curve, not linear) | Lookdev bible technique #5 |
| `dissolution` | Driven by `dissolution_mask` grid | Lookdev bible technique #3 |

### Key Decision: No Light Prims

The Soot aesthetic demands that all illumination comes from within the volume. In Karma XPU, this means the `emission` channel of the `standard_volume` shader is the sole light source. No environment lights, no directional lights, no area lights. The renderer sees only volume self-illumination plus multi-bounce scattering.

This is the single most important aesthetic decision in the pipeline. Violating it — adding even a dim fill light — immediately breaks the Soot look.

---

## Phase 3: Production Rendering Pipeline

**Goal**: Configure Karma XPU as the sole production renderer with settings that deliver exhibition quality within the render budget.

### Renderer: Karma XPU (Sole)

**Decision**: Karma XPU is the only supported renderer. RenderMan is dropped from the critical path. Rationale: single-renderer pipeline eliminates shader translation risk, simplifies quality assurance, and Karma XPU's native VDB + MaterialX support makes it the natural fit for this pipeline.

### Render Settings

| Parameter | Scout (128 cubed) | Preview (512 cubed) | Final (1024 cubed) |
|-----------|----------|---------|-------|
| Samples | 64 | 256 | 512 |
| Denoise | None | OIDN 2.3 | OIDN 2.3 temporal |
| Step size | 1.0x voxel | 0.5x voxel | 0.5x voxel |
| Max bounces | 4 | 6 | 8 |
| Scatter bounces | 1 | 2 | 4 |
| Resolution | 1080 short edge | 2160 short edge | 4320 short edge (4:5) |

### OIDN 2.3 Temporal Denoising

Intel Open Image Denoise 2.3 with temporal stability is mandatory for animation sequences. Without temporal mode, frame-to-frame noise pattern variation causes visible flicker — unacceptable for gallery projection.

Configuration: albedo + normal AOVs fed to OIDN alongside beauty pass. Temporal accumulation window of 3 frames.

### Multi-Pass LPE (Light Path Expressions)

| Pass | LPE | Purpose |
|------|-----|---------|
| Beauty | Full | Primary deliverable |
| Volume direct | `C<RV>L` | Volume single-scatter for re-grade |
| Volume indirect | `C<RV>{2,}L` | Multi-scatter contribution |
| Emission | `C<E>` | Self-illumination only |
| Depth (Z) | N/A | Compositing and DOF |
| Cryptomatte | N/A | Object isolation |

### The Black Void Challenge

Rendering a self-illuminated achromatic volume against pure black is technically demanding:

- **Noise convergence**: Emission-only scenes converge slowly. The 512-sample + OIDN strategy addresses this.
- **Black level**: Display black must be true 0,0,0. Any residual noise in empty regions reads as grey haze and destroys the void.
- **Banding**: 8-bit output in near-black gradients shows banding. EXR half-float output eliminates this.
- **Gamma**: The OCIO output transform handles the perceptual encoding. Do not apply additional gamma curves.

---

## Phase 4: Compositing & Finishing

**Goal**: Assemble multi-pass renders into final deliverables with grain, OCIO output transforms, and master file creation.

### Nuke MCP Pipeline

| Node | Function |
|------|----------|
| Read (EXR) | Load multi-pass renders |
| Merge (volume passes) | Combine direct + indirect + emission |
| Grade | Exposure trim per shot (±0.3 EV range) |
| Grain | Kodak 5219 grain profile, 0.5-0.8% intensity |
| OCIO Display | ACEScg -> Rec.709 (video) or ACEScg -> P3 (projection) |
| Write | Master deliverables (see below) |

### Film Grain Specification

Grain is not decorative — it is structural. The Soot aesthetic requires visible particulate texture at every scale. Grain prevents the volume from reading as "clean CG" and introduces the organic imperfection that fine-art printing demands.

| Parameter | Value |
|-----------|-------|
| Profile | Kodak Vision3 5219 (500T) |
| Intensity | 0.5% (projection), 0.8% (print — finer grain, closer viewing) |
| Grain size | Matched to output resolution (no upscaled grain) |
| Application | After grade, before OCIO output transform |

### OCIO Output Transforms

| Deliverable | Transform | Target |
|-------------|-----------|--------|
| Gallery projection | ACEScg -> ACES Output - Rec.709 | Calibrated projector, D65 |
| Print master | ACEScg -> Adobe RGB (1998) | Soft-proofed for baryta paper |
| Archive master | ACEScg (no transform) | Scene-referred preservation |
| Web preview | ACEScg -> sRGB | Monitoring only |

### Master Deliverables

| Deliverable | Format | Spec |
|-------------|--------|------|
| Projection master | ProRes 4444 XQ | 4:5 aspect, 3456x4320, 24 fps, loop point |
| Print masters | TIFF 16-bit | Per-shot hero frames, 300 DPI, Adobe RGB |
| Archive EXR | OpenEXR half-float | All passes, all frames, ACEScg |
| Preview | H.265 | 1080p sRGB, for documentation and web |

---

## Phase 5: Installation & Exhibition Technical Rider

**Goal**: Define the physical exhibition requirements. See [`plan/technical_rider.md`](technical_rider.md) for the full specification.

### Key Requirements

| Element | Specification |
|---------|--------------|
| Display | Portrait-oriented 4K+ projector or LED wall, 4:5 aspect |
| Black level | Native black < 0.005 cd/m2 (critical for void aesthetic) |
| Viewing distance | 2-3 meters (immersive scale, plume fills peripheral vision) |
| Room | Light-sealed, matte black walls, no ambient light bleed |
| Audio | Optional: low-frequency sub-bass drone, 20-40 Hz, felt not heard |
| Loop | Seamless loop with 3-second black dissolve between cycles |
| Backup | Redundant playback system, automated restart on failure |

---

## Phase 6: Archival Print Pipeline

**Goal**: Produce museum-grade prints that survive acquisition scrutiny. See [`plan/print_spec.md`](print_spec.md) for the full specification.

### Print Specification

| Parameter | Value |
|-----------|-------|
| Paper | Hahnemuhle Photo Rag Baryta 315 gsm |
| Printer | Epson P9570 (or equivalent 10-color pigment) |
| ICC profile | Custom profile for paper + ink combination |
| Dmax | Target > 2.3 (measured with spectrophotometer) |
| Black point | Maximized via GCR (grey component replacement) strategy |
| Edition | 3 + 1 AP per image (standard for photography editions) |
| Size | 100 x 125 cm (4:5 aspect, large-format presence) |

### Separate Print Render Pass

Exhibition projections and archival prints have different requirements. The print pass renders at higher spatial resolution with print-specific sharpening and a separate OCIO transform targeting the paper's gamut. This is a parallel render, not a reformat of the projection master.

---

## Phase 7: Conservation & Institutional Acquisition Package

**Goal**: Make the work acquirable by MoMA, Tate, or comparable institutions. See [`plan/conservation_package_spec.md`](conservation_package_spec.md) for the full specification.

### Package Contents

| Component | Format |
|-----------|--------|
| Source code | Git repository archive (full history) |
| Dependencies | Pinned lockfile, container image (Docker) |
| VDB sequence | Full resolution, all grids, with metadata |
| USD scenes | Complete scene files with MaterialX shaders |
| Render archives | EXR sequences (all passes, all frames) |
| Technical manual | Installation, calibration, troubleshooting |
| Artist statement | Conceptual framework and process documentation |
| Migration plan | 5-year technology refresh strategy |

### Key Principle

The conservation package must enable re-exhibition 20 years from now with no access to the original artist. Every parameter, every decision, every calibration step is documented. The work is the system, not just the output frames.

---

## Phase 8: Curatorial & Artist Statement

**Goal**: Provide the intellectual framework for exhibition. See [`plan/curatorial_framework.md`](curatorial_framework.md) for the full specification.

### Artist Statement Core

Sasol Secunda emits 57 million tonnes of CO2 per year — invisible. This work makes it visible. OCO-2 and OCO-3 satellites provide the measurements; atmospheric transport physics provides the 3D structure; the Soot aesthetic provides the confrontation. The CO2 is rendered not as decorative vapor but as what it would be if you could see it: choking industrial particulate, heavy and inexorable, filling the frame against black void.

The work sits at the intersection of three lineages: William Kentridge's charcoal materiality and industrial South African landscape; Refik Anadol's monumental data-driven volumes; and the satellite remote sensing tradition of making the invisible atmosphere legible. It is not scientific visualization (there is no colorbar, no axis, no legend) and it is not generative art (every particle traces back to a real satellite measurement). It occupies the space between — data sculpture rendered as dread.

### Achromatic Manifesto

Color is information. The absence of color is confrontation. The Soot palette — pure greyscale on black void — strips the visualization of every cue that might allow the viewer to categorize, aestheticize, or dismiss the image. There is no blue sky to provide comfort, no warm orange to suggest sunset beauty, no green to invoke nature's resilience. There is only density, texture, and luminance. The material speaks through weight, not wavelength.

---

## Production Critique Integration

### FX Supervisor Critique (Integrated)

The following decisions were made in response to FX Supervisor review:

| Critique | Decision | Rationale |
|----------|----------|-----------|
| RenderMan adds shader translation risk | Karma XPU sole renderer | Single-renderer pipeline eliminates dual-maintenance burden |
| Exploration VDBs shouldn't block on quality gates | Gates on delivery only | Iteration speed is critical during lookdev |
| Domain boundary artifacts | Cosine-ramp falloff | Prevents hard box edges from breaking volumetric illusion |
| Camera-relative detail | Procedural upres in frustum | Avoids regenerating full volume for detail refinement |
| Temporal flicker from denoising | OIDN 2.3 temporal mode | Frame-to-frame stability is mandatory for projection |

### FX Artist Critique (Integrated)

| Critique | Decision | Rationale |
|----------|----------|-----------|
| Multi-grid VDB for Houdini interop | density/vel/temperature/dissolution_mask | Standard Pyro grid layout, auto-connects in Houdini |
| MaterialX scattering anisotropy | 0.8 (not VTK's 0.35) | Path-traced multi-bounce requires higher forward bias |
| Render step size discipline | 0.5x voxel for final | Prevents banding and aliasing in dense regions |
| No light prims | Emission-only illumination | Soot aesthetic requires all light from within |

---

## Key Decisions

| ID | Decision | Alternatives Rejected |
|----|----------|----------------------|
| KD1 | Karma XPU sole renderer | RenderMan (shader translation risk), Blender Cycles (pipeline mismatch) |
| KD2 | OIDN 2.3 temporal denoise | OptiX (NVIDIA-only), Disney ML (RenderMan-coupled) |
| KD3 | 4:5 aspect ratio | 16:9 (landscape, less gallery presence), 1:1 (less compositional tension) |
| KD4 | No light prims in USD | Fill lights (break Soot look), environment (break void) |
| KD5 | MaterialX standard_volume | Custom OSL (portability risk), VEX (Houdini-locked) |
| KD6 | Quality gates on delivery only | Gates on all VDBs (blocks iteration), no gates (quality risk) |
| KD7 | Baryta paper for prints | Matte rag (lower Dmax), lustre (wrong surface quality for Soot) |
| KD8 | ACEScg working space | sRGB (insufficient dynamic range), linear Rec.709 (gamut too small) |

---

## Implementation Order

The phases are ordered for maximum de-risking. Each phase produces a testable artifact before the next begins.

```
Phase 0a  Shot Design & Creative Lock
    |
Phase 0   Complete Waves 7-9
    |
Phase 1   Scene-Referred Pipeline (ACES/OCIO, EXR)
    |
Phase 1b  VDB Production-Grade Export
    |
Phase 1c  Lookdev Bible (Soot Crust techniques)
    |
Phase 2   USD Scene Export & Houdini Bridge
    |
Phase 3   Production Rendering (Karma XPU)
    |
Phase 4   Compositing & Finishing (Nuke, grain, OCIO)
    |
Phase 5   Installation Technical Rider
    |
Phase 6   Archival Print Pipeline
    |
Phase 7   Conservation & Acquisition Package
    |
Phase 8   Curatorial & Artist Statement
```

Phases 0a and 8 can be worked in parallel with technical phases since they are creative/writing work. Phases 5-7 are documentation-heavy and can overlap with Phase 4 finishing.

---

## 1-Person Critical Path Variant

This project assumes a **1-person team** (artist-engineer). The critical path eliminates all parallelism and schedules work sequentially.

### Constraints

- No render farm — single workstation (Mac development) + single cloud GPU (Linux RTX 6000)
- No Nuke license assumed — DaVinci Resolve (free) or Natron (open source) as compositing fallback
- No Houdini Indie limitation for USD/Karma (Houdini Indie supports Karma XPU)

### Adjusted Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| 0a | 1 week | Shot design, scout approval |
| 0 | 2 weeks | Complete Waves 7-9 |
| 1 | 1 week | ACES/OCIO, EXR writer |
| 1b | 1 week | Multi-grid VDB export |
| 1c | 1 week | Lookdev bible implementation |
| 2 | 2 weeks | USD exporter, MaterialX shader |
| 3 | 2 weeks | Karma XPU setup, test renders, OIDN |
| 4 | 1 week | Compositing, grain, output transforms |
| 5 | 3 days | Technical rider (documentation) |
| 6 | 1 week | Print pipeline, ICC profiling, test prints |
| 7 | 3 days | Conservation package (documentation + archive) |
| 8 | 2 days | Artist statement (writing) |

**Total**: approximately 14 weeks (3.5 months)

### Risk Buffer

Add 30% buffer for unknowns: MaterialX shader tuning, OIDN temporal stability issues, print color matching iterations. Realistic total: **18 weeks**.

---

## Verification & Quality Gates

### Per-Phase Gates

| Phase | Gate | Method |
|-------|------|--------|
| 0a | Scout playback approved | Visual review at 24 fps, director sign-off |
| 0 | CI green | `pixi run ci` passes |
| 1 | Color round-trip | ACEScg -> Rec.709 -> ACEScg round-trip within 0.001 delta E |
| 1b | VDB loads in Houdini | Import test: all 4 grids auto-connect to Pyro shader |
| 1c | Lookdev matches visual_language.yaml | Side-by-side comparison against reference images |
| 2 | USD opens in Solaris | Camera, material, VDB refs intact after round-trip |
| 3 | Render matches preview | Final frame vs preview frame, same camera, perceptual match |
| 4 | Grain visible at projection size | View at 4K, grain reads as texture not noise |
| 5 | Technical rider reviewed | Venue confirms feasibility |
| 6 | Print Dmax > 2.3 | Spectrophotometer measurement on test strip |
| 7 | Package re-deployable | Fresh machine install from conservation package succeeds |
| 8 | Statement reviewed | Curatorial review, factual accuracy confirmed |

### Visual Quality Gate (All Phases)

Per CLAUDE.md Section 5.3: every rendering change must be reviewed by a dedicated Opus agent evaluating images without access to code changes. A single fail blocks the PR.

---

## Code Changes Summary

| Phase | Files Modified | Files Created |
|-------|---------------|---------------|
| 1 | `postprocess/tonemap.py`, `render/frame_writer.py`, `config/schema.py` | `render/exr_writer.py`, `postprocess/ocio_transform.py` |
| 1b | `sequencer/vdb_export.py`, `config/schema.py` | — |
| 1c | — | `render/lookdev.py` (MaterialX parameter mappings) |
| 2 | `config/schema.py` | `sequencer/usd_export.py`, `render/materialx_soot.py` |
| 3 | `config/schema.py` | `render/karma_config.py` |
| 4 | — | `postprocess/grain.py`, `postprocess/nuke_template.nk` |
| 6 | — | `render/print_pipeline.py` |

All new files follow the standard header (`from __future__ import annotations`), are covered by pytest, and pass `pixi run ci`.

---

## New Ticket Waves (10-14)

The phases above map to new ticket waves:

| Wave | Phase | Tickets |
|------|-------|---------|
| 10 | Phase 1 (ACES/OCIO, EXR) | 5 tickets |
| 11 | Phase 1b + 1c (VDB + Lookdev) | 5 tickets |
| 12 | Phase 2 (USD export) | 5 tickets |
| 13 | Phase 3 + 4 (Rendering + Compositing) | 5 tickets |
| 14 | Phase 5-8 (Installation, Print, Conservation, Curatorial) | 5 tickets |

Ticket YAMLs will be created in `plan/tickets/` following the existing format (see `plan/tickets/7-1.yaml` for template).

---

## References

| Document | Purpose |
|----------|---------|
| [`plan/prd.md`](prd.md) | v2.0 baseline (superseded) |
| [`plan/visual_language.yaml`](visual_language.yaml) | Soot aesthetic specification |
| [`plan/coding_guide_2026.md`](coding_guide_2026.md) | Pipeline architecture and quality principles |
| [`plan/rfc.md`](rfc.md) | Architecture decisions 1-9 |
| [`plan/shot_design.md`](shot_design.md) | 6-shot storyboard |
| [`plan/lookdev_bible.md`](lookdev_bible.md) | Soot Crust techniques |
| [`plan/render_farm_spec.md`](render_farm_spec.md) | Karma XPU render settings |
| [`plan/finishing_spec.md`](finishing_spec.md) | Nuke compositing specification |
| [`plan/technical_rider.md`](technical_rider.md) | Installation requirements |
| [`plan/print_spec.md`](print_spec.md) | Archival print pipeline |
| [`plan/conservation_package_spec.md`](conservation_package_spec.md) | Institutional acquisition package |
| [`plan/curatorial_framework.md`](curatorial_framework.md) | Artist statement and curatorial context |
