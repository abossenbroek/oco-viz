# RFC: CO2 Atmospheric Visualization Architecture

**RFC ID**: CO2-VIZ-001  
**Status**: Proposed  
**Author**: [Author]  
**Created**: [Date]

---

## Context

We need to create a 3D video visualization of CO2 transport above Sasol Secunda using OCO-2/OCO-3 satellite data. The visualization must show physically plausible plume behavior with atmospheric rendering quality suitable for artistic/public communication.

**Key constraint**: OCO-3 provides column-integrated measurements only. 3D reconstruction requires atmospheric transport modeling.

---

## Decision Drivers

1. **Development velocity**: POC must ship in ~3 weeks
2. **Visual quality**: Must include atmospheric haze/scattering effects
3. **Downstream flexibility**: Artist needs to remix in TouchDesigner
4. **Scientific plausibility**: Plume behavior must be physically defensible
5. **Infrastructure simplicity**: Single cloud GPU, no cluster

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
- (-) ERA5→ARL format conversion is friction

---

### Decision 3: Atmospheric Effects Strategy

**Options Considered**:

| Option | Pros | Cons |
|--------|------|------|
| A: VTK scattering only | Single render pass | Quality ceiling ~60% of target |
| B: Post-processing only | Fast renders, full control | Fakes 3D lighting |
| C: VTK scattering + post-processing | Best quality, additive | Longer render, more code |
| D: Multi-pass compositing | Maximum control | Complex pipeline, debugging hard |

**Decision**: **Option C (VTK scattering + post-processing pipeline)**.

**Rationale**:
- VTK scattering provides physically-based volumetric shadows
- Post-processing adds atmospheric haze (depth fog), bloom, tonemapping
- Combined approach achieves ~75-80% of path-traced quality
- Post-processing is cheap to iterate on after render

**VTK Parameters** (key settings):
```
GlobalIlluminationReach: 0.3-0.5  # Secondary ray length
VolumetricScatteringBlending: 1.5-2.0  # Fog-like scattering
ScatteringAnisotropy: 0.7  # Forward scattering (atmospheric)
```

**Post-Processing Pipeline**:
```
Raw frame → Depth fog → ACES tonemap → Bloom → Output
```

**Consequences**:
- (+) Quality meets artistic requirements
- (+) Can tune post-processing without re-rendering
- (-) Render time ~5-10x slower than basic shading
- (-) Depth buffer extraction adds complexity

---

### Decision 4: Data Flow Architecture

**Decision**: Staged pipeline with Zarr intermediate storage.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA ACQUISITION                              │
│                                                                      │
│  OCO-2/3 (NASA)   ERA5 (Copernicus)     HYSPLIT (local)            │
│       │                  │                    │                     │
│       └──────────────────┼────────────────────┘                     │
│                          │                                          │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │   COORDINATE TRANSFORM │                              │
│              │   • lat/lon → local km │                              │
│              │   • pressure → altitude│                              │
│              │   • regrid to Cartesian│                              │
│              └───────────┬───────────┘                              │
│                          │                                          │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │   concentration.zarr   │  ← Checkpoint               │
│              │   [time, z, y, x]      │                              │
│              │   ~10-20 GB            │                              │
│              └───────────┬───────────┘                              │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────────┐
│                          ▼           RENDERING                       │
│              ┌───────────────────────┐                              │
│              │   VTK Volume Renderer  │                              │
│              │   • GPU ray casting    │                              │
│              │   • Scattering enabled │                              │
│              └───────────┬───────────┘                              │
│                          │                                          │
│                          ▼                                          │
│              ┌───────────────────────┐                              │
│              │   Post-Processing      │                              │
│              │   • Depth fog          │                              │
│              │   • Tonemapping        │                              │
│              │   • Bloom              │                              │
│              └───────────┬───────────┘                              │
│                          │                                          │
│              ┌───────────┴───────────┐                              │
│              ▼                       ▼                              │
│     frames/*.png              vdb/*.vdb                             │
│     (final 2D)              (3D for TD)                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Rationale**:
- Zarr checkpoint enables re-rendering without re-processing
- Chunked storage streams large datasets without full RAM load
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
| Origin | -26.52°S, 29.17°E | Sasol Synfuels facility |
| Horizontal extent | 100 km × 100 km | Captures plume at typical wind speeds for 6-12 hours |
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

## Interfaces

### Concentration Array Contract

```python
# Zarr structure
concentration.zarr/
├── concentration    # float32 [time, z, y, x]
├── time             # datetime64[ns] [time]
├── x                # float32 [x] — km from origin
├── y                # float32 [y] — km from origin  
├── z                # float32 [z] — meters altitude
└── .zattrs          # metadata (origin_lat, origin_lon, units)
```

**Chunks**: `(24, 60, 100, 100)` — one day of hourly data per chunk.

### Renderer Interface

```python
class VolumeRenderer(Protocol):
    def configure(
        self,
        transfer_function: TransferFunction,
        scattering_reach: float = 0.4,
        scattering_blend: float = 1.8,
        anisotropy: float = 0.7
    ) -> None: ...
    
    def render_frame(
        self,
        concentration: np.ndarray,  # [z, y, x]
        camera: Camera,
        timestamp: datetime | None = None
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
    ) -> np.ndarray:          # [H, W, 3] uint8 0-255
        ...

# Composition
pipeline = Compose([
    DepthFog(density=0.3, color=(0.7, 0.8, 0.9)),
    ACEStonemap(exposure=0.6),
    Bloom(threshold=0.6, intensity=0.3),
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
- Pipeline complexity (Python → VDB → Blender scene → render)
- 5-60 minute per-frame render times
- Over-engineered for POC scope

**Recommendation**: Reserve for post-POC "hero" renders if needed.

### CAMS Global Reanalysis Instead of HYSPLIT

Pre-computed global CO2 fields, no model setup required. Rejected because:
- 80 km resolution — Sasol plume is sub-grid
- Cannot resolve point-source dispersion
- Would show regional patterns, not facility-specific plume

---

## Open Technical Questions

| ID | Question | Impact | Proposed Resolution |
|----|----------|--------|---------------------|
| TQ1 | Does VTK EGL work reliably on g5.xlarge AMI? | Blocks headless | Test in Phase 0; OSMesa fallback |
| TQ2 | pyopenvdb wheel available for Linux + Python 3.11? | Blocks VDB export | Build from source if needed; defer to P1 |
| TQ3 | ERA5→ARL conversion tooling current state? | Blocks HYSPLIT | Test era5_request scripts; alternative: direct ERA5 with PySPLIT |
| TQ4 | Optimal scattering parameters for atmospheric viz? | Quality | Empirical tuning in Phase 3 |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HYSPLIT setup exceeds time budget | Medium | High | Synthetic Gaussian plume generator as standalone path to visualization |
| VTK scattering quality insufficient | Low | Medium | Post-processing pipeline provides quality floor |
| OCO-3 coverage sparse in chosen period | Medium | Medium | Pre-screen dates before committing; extend window; fuse OCO-2 + OCO-3 for improved temporal coverage |
| Memory pressure at 90-day scale | Low | Medium | Zarr streaming; process in temporal batches |
| EGL/headless rendering fails | Low | High | OSMesa software fallback (slower but works) |

---

## Implementation Phases

### Phase 0: Environment + Synthetic Pipeline (2 days)
**Exit Criteria**: 
- Headless VTK renders on g5.xlarge
- Synthetic plume → PNG frame → MP4 video end-to-end
- VTK scattering parameters accessible and functional

### Phase 1: Data Acquisition (3 days)  
**Exit Criteria**:
- OCO-3 files downloaded, quality-filtered, readable
- ERA5 winds downloaded for target period
- HYSPLIT producing 3D output OR synthetic fallback committed

### Phase 2: Processing Pipeline (3 days)
**Exit Criteria**:
- 4D concentration array in Zarr
- Coordinates validated (Sasol at origin, altitudes physical)
- Sample timestep renders correctly

### Phase 3: Rendering + Atmospheric Effects (4 days)
**Exit Criteria**:
- Scattering enabled, parameters tuned
- Post-processing pipeline functional
- Single frame meets quality bar

### Phase 4: Animation + Export (3 days)
**Exit Criteria**:
- Full sequence rendered
- Video encoded, plays smoothly
- VDB sequence exports (if P1 achieved)

### Phase 5: Validation + Polish (3 days)
**Exit Criteria**:
- OCO-3 observations overlaid for validation
- Timestamp/annotations present
- Stakeholder review passed

---

## Appendix: VTK Scattering Configuration

```python
import vtk

# Get mapper from PyVista actor
mapper = actor.GetMapper()

# Enable volumetric scattering (VTK 9.2+)
mapper.SetGlobalIlluminationReach(0.4)      # 0-1, fraction of volume diagonal
mapper.SetVolumetricScatteringBlending(1.8) # 0-2, surface vs volume shading
mapper.UseJitteringOn()                      # Reduce banding artifacts

# Configure volume property
prop = actor.GetProperty()
prop.SetScatteringAnisotropy(0.7)           # -1 to 1, forward scattering
prop.SetShade(True)
prop.SetAmbient(0.3)
prop.SetDiffuse(0.7)
prop.SetSpecular(0.2)

# Performance: reduce sample distance for quality, increase for speed
mapper.SetSampleDistance(0.5)  # Smaller = higher quality, slower
```

---

## Appendix: Post-Processing Reference

```python
import numpy as np
from scipy.ndimage import gaussian_filter

def depth_fog(rgb, depth, density=0.3, fog_color=(0.7, 0.8, 0.9)):
    """Exponential depth fog for atmospheric perspective."""
    depth_norm = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
    fog_factor = 1.0 - np.exp(-density * depth_norm)
    fog = np.array(fog_color).reshape(1, 1, 3)
    return rgb * (1 - fog_factor[..., np.newaxis]) + fog * fog_factor[..., np.newaxis]

def aces_tonemap(rgb, exposure=0.6):
    """ACES filmic tonemapping."""
    rgb = rgb * exposure
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((rgb * (a * rgb + b)) / (rgb * (c * rgb + d) + e), 0, 1)

def bloom(rgb, threshold=0.6, sigma=20, intensity=0.3):
    """Gaussian bloom on bright regions."""
    luminance = 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]
    bright_mask = (luminance > threshold).astype(float)
    glow = gaussian_filter(rgb * bright_mask[..., np.newaxis], sigma=(sigma, sigma, 0))
    return np.clip(rgb + glow * intensity, 0, 1)
```