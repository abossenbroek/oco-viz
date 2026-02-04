# RFC: CO2 Atmospheric Visualization Architecture

**RFC ID**: CO2-VIZ-001
**Status**: Proposed
**Author**: [Author]
**Created**: [Date]

---

## Context

We need to create a 3D video visualization of CO2 transport above Sasol Secunda using OCO-2/OCO-3 satellite data and CAMS reanalysis. The visualization follows the **"Soot" visual language** — anthropocene industrial dread, rendering CO2 as oppressive industrial particulate on black void. Three fidelity tiers (sketch/study/exhibition) serve different stages of the creative process.

**Key constraint**: OCO-3 provides column-integrated measurements only. 3D reconstruction requires atmospheric transport modeling.

---

## Decision Drivers

1. **Development velocity**: POC must ship in ~3 weeks
2. **Visual identity**: "Soot" — monochrome grey-scale, internal smoldering light, granular dissolution
3. **Fidelity tiers**: Sketch (fast iteration) / Study (TF refinement) / Exhibition (gallery-quality)
4. **Downstream flexibility**: Artist needs to remix in TouchDesigner
5. **Scientific plausibility**: Plume behavior must be physically defensible
6. **Infrastructure simplicity**: Single cloud GPU, no cluster

---

## Decisions

### Decision 1: Rendering Stack

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| A: PyVista (high-level VTK) | Fast development, good docs | Hides VTK scattering parameters |
| B: Raw VTK Python bindings | Full control, scattering access | More boilerplate |
| C: PlotOptiX | RTX ray tracing, best quality | Experimental volume support, strict HW requirement |
| D: Blender Cycles via bpy | Highest quality ceiling | Complex pipeline, slow renders |
| E: ParaView pvpython | Built-in scattering, battle-tested | Less flexible for custom post-processing |

**Decision**: **Option B (Raw VTK)** with PyVista for prototyping.

**Rationale**:
- VTK 9.2+ includes GPU volumetric scattering via `GlobalIlluminationReach` and `VolumetricScatteringBlending`
- PyVista doesn't expose these parameters; raw VTK access required
- Hybrid approach: use PyVista for data loading/setup, drop to VTK for renderer configuration
- PlotOptiX quality is better but "experimental" volume support is risk for POC timeline
- Blender quality ceiling not needed for POC scope

**Consequences**:
- (+) Access to VTK scattering without custom shaders
- (+) PyVista ecosystem for data handling
- (-) Must manage VTK objects directly for rendering
- (-) Documentation for advanced VTK features is sparse

---

### Decision 2: Transport Model

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| A: HYSPLIT | Industry standard, runs locally | Setup complexity, binary output format |
| B: WRF-Chem | Highest fidelity, coupled met-chem | Massive compute requirement, weeks of setup |
| C: CAMS Reanalysis | Pre-computed, global, NetCDF | 80km resolution too coarse for point source |
| D: Gaussian plume (parametric) | Instant, no external deps | Not physically accurate for complex terrain/met |
| E: STILT | Good for source attribution | Backward trajectories, not forward dispersion |

**Decision**: **Option A (HYSPLIT)** with **Option D (Gaussian plume)** as fallback.

**Rationale**:
- HYSPLIT is the standard tool for point-source dispersion
- Runs on single machine with ERA5 input
- Gaussian plume provides working visualization if HYSPLIT setup exceeds time budget
- CAMS resolution insufficient — Sasol plume is <50km scale
- WRF-Chem quality not needed for artistic POC

**Consequences**:
- (+) Physically-based dispersion with real meteorology
- (+) Fallback path ensures POC ships regardless
- (-) HYSPLIT binary output requires parsing
- (-) ERA5->ARL format conversion is friction

---

### Decision 2a: Background CO2 Field (Amendment)

**Context**: Original Decision 2 rejected CAMS reanalysis (80 km) as too coarse for point-source resolution. This amendment adds CAMS *high-resolution forecast* (~9 km) as a **background layer only**.

**Architecture**:
```
Layer 1: CAMS 9km background    -> large-scale 3D CO2 field (~420 ppm)
Layer 2: Gaussian plume model   -> Secunda point-source enhancement (+5-15 ppm)
Layer 3: Turbulent compositor   -> sub-grid filamentary structure
Overlay: OCO-2/OCO-3 footprints -> validation markers
```

**Decision**: Use CAMS `cams-global-atmospheric-composition-forecasts` (9 km) as the background CO2 field. Point-source dispersion remains Gaussian plume (Decision 2). CAMS does **not** assimilate OCO-2/OCO-3 (it uses GOSAT), so OCO observations remain independent for validation.

**Rationale**:
- No single dataset provides observation-based 3D CO2 at 1 km — layered composition is the same method NASA SVS uses at regional scale
- CAMS high-res forecast resolves synoptic-scale gradients that make the background realistic
- Anomaly-mode normalization (subtract background, normalize enhancement) keeps existing transfer function presets working while the background becomes transparent
- Absolute-mode normalization with ultra-low opacity (peak 0.20) prevents the 10 km column from going solid opaque

**Consequences**:
- (+) Visualization shows ALL atmospheric CO2 transport, not only point-source plume
- (+) OCO-2/OCO-3 validation overlay is scientifically defensible (independent data)
- (-) Additional data dependency (CDS API for CAMS forecasts)
- (-) Regridding pipeline adds complexity (hybrid-sigma -> altitude, 9 km -> 1 km)

---

### Decision 3: Atmospheric Effects Strategy

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| A: VTK scattering only | Single render pass | Quality ceiling ~60% of target |
| B: Post-processing only | Fast renders, full control | Fakes 3D lighting |
| C: VTK scattering + post-processing | Best quality, additive | Longer render, more code |
| D: Multi-pass compositing | Maximum control | Complex pipeline, debugging hard |

**Decision**: **Option C (VTK scattering + post-processing pipeline)**, with **tier-specific pipelines**.

**Rationale**:
- VTK scattering provides physically-based volumetric shadows
- Post-processing pipeline is tier-specific — exhibition tier removes depth fog entirely
- Exhibition tier uses pure black background with internal smoldering light only
- Study tier retains basic fog as optional development aid
- ACES tonemap retained across tiers for exposure control on grey-scale
- Bloom retuned for grey-scale: threshold targets peak luminance regions, no color bloom
- Shallow DOF added for exhibition tier

**Tier-Specific Post-Processing Pipelines**:
```
Sketch:     Raw wireframe -> Output
Study:      Raw volume -> ACES tonemap -> Output
Exhibition: Raw volume -> Particle dissolution -> Shallow DOF -> ACES tonemap -> Output
```

**VTK Parameters** (Soot aesthetic — see Appendix for full config):
```
GlobalIlluminationReach: 0.5-0.7  # Increased for internal glow effect
VolumetricScatteringBlending: 1.5-2.0
ScatteringAnisotropy: 0.3-0.4  # Reduced — less forward-scattering, more occluded/suffocated
```

**Exhibition Tier Specifics**:
- `renderer.SetBackground(0, 0, 0)` — pure black void
- No ground plane, no sky gradient
- No depth fog (removed from pipeline)
- No external directional lights — internal smoldering only
- Shallow DOF with focus on plume center of mass

**Study Tier Specifics**:
- Basic volume rendering with grey-scale TF
- Fog optional for development visibility
- ACES tonemap for consistent exposure

**Consequences**:
- (+) Quality meets exhibition requirements at top tier
- (+) Fast iteration at sketch/study tiers
- (+) Can tune post-processing without re-rendering
- (-) Render time ~5-10x slower than basic shading at exhibition tier
- (-) Particle dissolution system requires additional development

---

### Decision 4: Data Flow Architecture

**Decision**: Staged pipeline with Zarr intermediate storage.

```
+-----------------------------------------------------------------+
|                        DATA ACQUISITION                         |
|                                                                 |
|  OCO-2/3 (NASA)   ERA5 (Copernicus)   CAMS (Copernicus)       |
|       |                  |                    |                 |
|       +------------------+--------------------+                 |
|                          |                                      |
|                          v                                      |
|              +------------------------+                         |
|              |   COORDINATE TRANSFORM  |                         |
|              |   - lat/lon -> local km  |                         |
|              |   - pressure -> altitude |                         |
|              |   - regrid to Cartesian  |                         |
|              +----------+-------------+                         |
|                          |                                      |
|                          v                                      |
|              +------------------------+                         |
|              |   concentration.zarr    |  <- Checkpoint          |
|              |   [time, z, y, x]       |                         |
|              |   ~10-20 GB             |                         |
|              +----------+-------------+                         |
|                          |                                      |
+--------------------------+--------------------------------------+
                           |
+--------------------------+--------------------------------------+
|                          v           RENDERING                  |
|              +------------------------+                         |
|              |   Tier Selection        |                         |
|              |   sketch/study/exhibit  |                         |
|              +----------+-------------+                         |
|                          |                                      |
|              +-----------+-----------+                          |
|              v           v           v                          |
|          Sketch       Study     Exhibition                     |
|          wireframe    volume    volume+particles               |
|              |           |           |                          |
|              v           v           v                          |
|              +------------------------+                         |
|              |   Tier Post-Processing  |                         |
|              +----------+-------------+                         |
|                          |                                      |
|              +-----------+-----------+                          |
|              v                       v                          |
|     frames/*.png              vdb/*.vdb                        |
|     (final 2D)              (3D for TD)                        |
|                                                                 |
+-----------------------------------------------------------------+
```

**Rationale**:
- Zarr checkpoint enables re-rendering without re-processing
- Chunked storage streams large datasets without full RAM load
- Tier selection at render time — same data, different quality levels
- Clear separation: data team owns above line, viz team owns below

---

### Decision 5: Temporal Scope

**Options Considered**:

| Option | Frames (hourly) | Storage | Render Time |
|--------|-----------------|---------|-------------|
| A: 7 days | 168 | ~2 GB | ~30 min |
| B: 30 days | 720 | ~8 GB | ~2 hr |
| C: 90 days | 2,160 | ~20 GB | ~6 hr |
| D: 365 days | 8,760 | ~80 GB | ~24 hr |

**Decision**: **Option C (90 days)** as target, **Option B (30 days)** as MVP.

**Rationale**:
- 30 days likely has only 3-8 OCO-3 overpasses — sparse validation
- 90 days captures seasonal wind variation, more validation points
- 90 days at 30fps = 72 seconds — appropriate video length
- Can always render subset for faster iteration

**Consequences**:
- (+) Sufficient OCO-3 coverage for validation
- (+) Visible seasonal/weather pattern changes
- (-) 6hr render time requires overnight batch or parallelization
- (-) ERA5 download larger (~10 GB)

---

### Decision 6: Grid Specification

**Decision**: Regular Cartesian grid, local coordinates centered on Sasol.

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Origin | -26.52 S, 29.17 E | Sasol Synfuels facility |
| Horizontal extent | 100 km x 100 km | Captures plume at typical wind speeds for 6-12 hours |
| Vertical extent | 0 - 15 km | Surface to tropopause |
| Horizontal resolution | 1 km | Matches HYSPLIT output, sufficient for viz |
| Vertical resolution | 250 m | Resolves boundary layer structure |
| Grid dimensions | [100, 100, 60] | 600K voxels — fits comfortably in GPU memory |

**Coordinate system**:
- X: Eastward (km)
- Y: Northward (km)
- Z: Altitude above sea level (m)
- Time: Hours since simulation start

---

### Decision 7: Output Formats

**Decision**: Dual output — PNG frames + OpenVDB sequence.

| Output | Format | Purpose | Priority |
|--------|--------|---------|----------|
| Frames | PNG 16-bit | Final video input, post-processing headroom | P0 |
| Video | H.264 MP4 | Distribution | P0 |
| Volumes | OpenVDB | TouchDesigner remix | P1 |

**VDB Specification**:
- Grid name: `density`
- Data type: Float32
- Voxel size: 1000 m (matches grid)
- Store enhancement only (subtract background 415 ppm)
- Sparse storage — only active voxels

**Rationale**:
- PNG 16-bit preserves dynamic range for post-processing
- VDB sparse storage efficient for plume (5% of domain non-empty)
- Same source data, different consumers

---

### Decision 8: Visual Language ("Soot")

**Context**: The visualization requires a cohesive aesthetic direction that serves the anthropocene communication goal. Ad-hoc tuning of individual parameters (transfer function colors, light angles, fog density) produces inconsistent results. A formalized visual language provides deterministic creative constraints.

**Decision**: Adopt the **"Soot" visual language** as the binding aesthetic specification for all rendering decisions.

**Core Principles**:

| Principle | Implementation |
|-----------|---------------|
| **Monochrome constraint** | R=G=B at all density levels. No color. Peak at #c8c8c8 (dirty near-white). |
| **Black void** | Pure black background (0,0,0). No ground plane, sky gradient, or environmental context. |
| **Internal smoldering** | No external directional lights. Light appears suffocated by density — deep interiors brighter than surfaces. |
| **Granular dissolution** | Volume boundaries break into discrete soot particles rather than smooth falloff. Exhibition tier only. |
| **Heavy motion** | Slow, creeping tempo. Heavy easing. Glacial camera drift. No fast cuts. |
| **Oppressive scale** | Close framing, fill 60-80% of frame. Viewer loses sense of scale — the soot is everything. |

**References**:
- **Refik Anadol**: Monumental turbulent volumes, geological folding, particle dissolution
- **William Kentridge**: Charcoal on black, industrial residue, weight of material
- **Pixar Soul**: Inner luminosity structure, made industrial and suffocated
- **Japanese/South African nightmare**: Slow dread, encroaching wrongness

**Fidelity Tier System**:

| Tier | Purpose | Treatment |
|------|---------|-----------|
| Sketch | Fast iteration, form exploration | Wireframe or point cloud on black |
| Study | Density/TF refinement | Volume rendering with grey-scale TF |
| Exhibition | Gallery-quality output | Full volume + particle dissolution + turbulent detail + shallow DOF |

**Consequences**:
- (+) Deterministic creative constraints prevent parameter drift
- (+) All team members work toward same aesthetic target
- (+) Machine-readable spec (`plan/visual_language.yaml`) enables automated validation
- (-) Constrains future color-based visualizations (by design — fork for color work)
- (-) Exhibition tier performance requirements are higher

---

### Decision 9: Transfer Function Architecture

**Context**: The existing approach uses per-preset transfer functions (ember.json, storm.json, default_plume.json, atmospheric.json) with varied color palettes. The Soot visual language requires a single achromatic transfer function with tier-specific parameter overrides.

**Decision**: Introduce a **`soot.json` transfer function** as the primary TF for all Soot pipeline rendering. Existing presets are retained as legacy/reference but not used in the Soot pipeline.

**Specification**:

| Property | Value |
|----------|-------|
| Color model | Achromatic (R=G=B at every density level) |
| Background | Pure black (0,0,0) at zero density |
| Peak color | #c8c8c8 at density 1.0 (dirty near-white, never clean white) |
| Opacity range | 0.0 to 0.45 (never reaches 1.0 — volumes always have depth) |
| Opacity curve | Gradual: stays near zero at low density, rises slowly through mid-range |

**Color Points**:
```
Density  R     G     B
0.0      0     0     0
0.1      26    26    26    (#1a1a1a)
0.3      61    61    61    (#3d3d3d)
0.5      107   107   107   (#6b6b6b)
0.8      158   158   158   (#9e9e9e)
1.0      200   200   200   (#c8c8c8)
```

**Opacity Points**:
```
Density  Opacity
0.0      0.00
0.1      0.00
0.2      0.05
0.5      0.20
0.8      0.35
1.0      0.45
```

**Tier Overrides**:
- **Sketch**: No transfer function (single flat grey)
- **Study**: `soot.json` as-is
- **Exhibition**: `soot.json` + particle dissolution at low-opacity boundary regions

**Legacy Presets**:
- `ember.json`, `storm.json`, `default_plume.json`, `atmospheric.json` — retained in `configs/transfer_functions/` for reference and non-Soot experiments. Not loaded by default in Soot pipeline.

**Consequences**:
- (+) Single source of truth for Soot palette
- (+) Achromatic constraint is machine-verifiable (R=G=B)
- (+) Opacity ceiling of 0.45 ensures volumes always show internal depth
- (-) Cannot represent colored visualizations — by design for Soot

---

## Interfaces

### Concentration Array Contract

```python
# Zarr structure
concentration.zarr/
  concentration    # float32 [time, z, y, x]
  time             # datetime64[ns] [time]
  x                # float32 [x] -- km from origin
  y                # float32 [y] -- km from origin
  z                # float32 [z] -- meters altitude
  .zattrs          # metadata (origin_lat, origin_lon, units)
```

**Chunks**: `(24, 60, 100, 100)` — one day of hourly data per chunk.

### Renderer Interface

```python
class VolumeRenderer(Protocol):
    def configure(
        self,
        transfer_function: TransferFunction,
        tier: Literal["sketch", "study", "exhibition"] = "study",
        scattering_reach: float = 0.6,
        scattering_blend: float = 1.8,
        anisotropy: float = 0.35,
    ) -> None: ...

    def render_frame(
        self,
        concentration: np.ndarray,  # [z, y, x]
        camera: Camera,
        timestamp: datetime | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:  # (rgb, depth)
        """Returns RGB image and depth buffer for post-processing."""
        ...
```

### Post-Processing Interface

```python
class PostProcessor(Protocol):
    def process(
        self,
        rgb: np.ndarray,      # [H, W, 3] float32 0-1
        depth: np.ndarray,    # [H, W] float32
        tier: Literal["sketch", "study", "exhibition"] = "study",
    ) -> np.ndarray:          # [H, W, 3] uint8 0-255
        ...

# Tier-specific compositions
sketch_pipeline = Compose([])  # Pass-through

study_pipeline = Compose([
    ACEStonemap(exposure=0.6),
])

exhibition_pipeline = Compose([
    ParticleDissolution(threshold=0.05, particle_count=2000),
    ShallowDOF(focal_distance="plume_centroid", aperture=2.8),
    ACEStonemap(exposure=0.6),
])
```

---

## Alternatives Rejected

### Using VAPOR Instead of VTK

VAPOR is purpose-built for atmospheric NetCDF and handles WRF/MPAS natively. Rejected because:
- Limited programmatic control for batch rendering
- No scattering model
- Valuable for exploration but not final rendering

**Recommendation**: Use VAPOR for data exploration and validation before committing to VTK render pipeline.

### Blender Cycles for Rendering

Highest quality ceiling via path-traced multi-scattering. Rejected because:
- Pipeline complexity (Python -> VDB -> Blender scene -> render)
- 5-60 minute per-frame render times
- Over-engineered for POC scope

**Recommendation**: Reserve for post-POC "hero" renders if needed.

### CAMS Global Reanalysis Instead of HYSPLIT

Pre-computed global CO2 fields, no model setup required. Rejected because:
- 80 km resolution — Sasol plume is sub-grid
- Cannot resolve point-source dispersion
- Would show regional patterns, not facility-specific plume

### Color Transfer Functions for Exhibition

Multi-color palettes (ember, storm) were considered for exhibition tier. Rejected because:
- Soot visual language mandates achromatic palette
- Color distracts from material texture and weight
- Monochrome constraint forces quality to come from density, lighting, and dissolution — not color

---

## Open Technical Questions

| ID | Question | Impact | Proposed Resolution |
|----|----------|--------|---------------------|
| TQ1 | Does VTK EGL work reliably on g5.xlarge AMI? | Blocks headless | Test in Phase 0; OSMesa fallback |
| TQ2 | pyopenvdb wheel available for Linux + Python 3.11? | Blocks VDB export | Build from source if needed; defer to P1 |
| TQ3 | ERA5->ARL conversion tooling current state? | Blocks HYSPLIT | Test era5_request scripts; alternative: direct ERA5 with PySPLIT |
| TQ4 | Optimal scattering parameters for Soot aesthetic? | Quality | Empirical tuning — reduced anisotropy, increased illumination reach |
| TQ5 | Particle dissolution performance at exhibition resolution? | Render time | Profile GPU instancing vs. point cloud overlay |
| TQ6 | Shallow DOF implementation — VTK native or post-process? | Pipeline | Post-process likely simpler; test VTK focal distance API |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HYSPLIT setup exceeds time budget | Medium | High | Synthetic Gaussian plume generator as standalone path |
| VTK scattering quality insufficient for Soot | Low | Medium | Post-processing pipeline + particle dissolution as quality floor |
| OCO-3 coverage sparse in chosen period | Medium | Medium | Pre-screen dates; fuse OCO-2 + OCO-3 |
| Memory pressure at 90-day scale | Low | Medium | Zarr streaming; process in temporal batches |
| EGL/headless rendering fails | Low | High | OSMesa software fallback (slower but works) |
| Particle dissolution performance | Medium | Medium | LOD, pre-compute positions, GPU instancing |

---

## Implementation Phases

### Phase 0: Environment + Synthetic Pipeline (2 days)
**Exit Criteria**:
- Headless VTK renders on g5.xlarge
- Synthetic plume -> PNG frame -> MP4 video end-to-end
- VTK scattering parameters accessible and functional
- Soot transfer function (`soot.json`) renders correctly

### Phase 1: Data Acquisition (3 days)
**Exit Criteria**:
- OCO-3 files downloaded, quality-filtered, readable
- ERA5 winds downloaded for target period
- HYSPLIT producing 3D output OR synthetic fallback committed

### Phase 2: Processing Pipeline (3 days)
**Exit Criteria**:
- 4D concentration array in Zarr
- Coordinates validated (Sasol at origin, altitudes physical)
- Sample timestep renders correctly with Soot TF

### Phase 3: Rendering + Soot Aesthetic (4 days)
**Exit Criteria**:
- Internal smoldering lighting model functional
- All three fidelity tiers produce output
- Single exhibition frame meets Soot quality bar

### Phase 4: Animation + Export (3 days)
**Exit Criteria**:
- Full sequence rendered with slow/creeping tempo
- Video encoded, plays smoothly
- VDB sequence exports (if P1 achieved)

### Phase 5: Exhibition Polish (3 days)
**Exit Criteria**:
- Particle dissolution at volume boundaries (exhibition tier)
- Shallow DOF functional (exhibition tier)
- Soot developer self-check passes (see `plan/visual_language.yaml`)

---

## Appendix: VTK Scattering Configuration (Soot)

```python
import vtk

# Get mapper from PyVista actor
mapper = actor.GetMapper()

# Enable volumetric scattering (VTK 9.2+)
# Increased reach for internal smoldering glow
mapper.SetGlobalIlluminationReach(0.6)      # 0-1, increased for internal glow
mapper.SetVolumetricScatteringBlending(1.8)  # 0-2, surface vs volume shading
mapper.UseJitteringOn()                       # Reduce banding artifacts

# Configure volume property — Soot aesthetic
prop = actor.GetProperty()
prop.SetScatteringAnisotropy(0.35)           # Reduced — less forward-scattering,
                                              # more occluded/suffocated look
prop.SetShade(True)
prop.SetAmbient(0.4)                          # Slightly increased for internal glow
prop.SetDiffuse(0.5)                          # Reduced — less external light response
prop.SetSpecular(0.0)                         # No specular — soot is matte

# Performance: reduce sample distance for quality, increase for speed
mapper.SetSampleDistance(0.5)  # Smaller = higher quality, slower

# Exhibition tier: pure black background, no ground plane
renderer = vtk.vtkRenderer()
renderer.SetBackground(0, 0, 0)              # Pure black void
renderer.RemoveAllLights()                    # No external directional lights
# Internal glow comes from scattering parameters + ambient only
```

---

## Appendix: Post-Processing Reference (Soot)

```python
import numpy as np
from scipy.ndimage import gaussian_filter

def aces_tonemap(rgb, exposure=0.6):
    """ACES filmic tonemapping — grey-scale exposure control."""
    rgb = rgb * exposure
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e), 0, 1)

def bloom_greyscale(rgb, threshold=0.7, sigma=20, intensity=0.2):
    """Bloom on bright grey-scale regions — no color bloom."""
    luminance = rgb[..., 0]  # R=G=B, any channel is luminance
    bright_mask = (luminance > threshold).astype(float)
    glow = gaussian_filter(rgb * bright_mask[..., np.newaxis], sigma=(sigma, sigma, 0))
    return np.clip(rgb + glow * intensity, 0, 1)

def shallow_dof(rgb, depth, focal_depth, aperture=2.8):
    """Shallow depth of field — exhibition tier."""
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    blur_amount = np.abs(depth_norm - focal_depth) * (10.0 / aperture)
    # Per-pixel gaussian blur approximation
    blurred = gaussian_filter(rgb, sigma=(8, 8, 0))
    blend = np.clip(blur_amount, 0, 1)[..., np.newaxis]
    return rgb * (1 - blend) + blurred * blend

# NOTE: depth_fog is NOT used in exhibition tier.
# Retained for study tier development visibility only.
def depth_fog(rgb, depth, density=0.3, fog_color=(0.2, 0.2, 0.2)):
    """Exponential depth fog — study tier only. Grey fog, not blue-white."""
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    fog_factor = 1.0 - np.exp(-density * depth_norm)
    fog = np.array(fog_color).reshape(1, 1, 3)
    return rgb * (1 - fog_factor[..., np.newaxis]) + fog * fog_factor[..., np.newaxis]
```
