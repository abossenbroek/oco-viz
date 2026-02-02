# PRD: Sasol Secunda CO2 Atmospheric Visualization

**Version**: 1.0  
**Status**: Draft  
**Author**: [Author]  
**Last Updated**: [Date]

---

## Problem Statement

Sasol Secunda is one of the world's largest single-point CO2 emitters (~57 Mt/year). OCO-3 satellite observations capture column-integrated CO2 measurements over the facility, but these 2D measurements cannot convey the 3D atmospheric transport that determines environmental impact. 

An artistic visualization showing CO2 plume behavior in 3D over time would communicate this impact more effectively than static data products.

**Core challenge**: OCO-3 provides column-integrated XCO2 (single value per footprint), not vertical profiles. Reconstructing 3D structure requires coupling satellite observations with atmospheric transport physics.

---

## Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G1 | Produce video showing 3D CO2 plume evolution above Sasol Secunda | Completed video, 30+ seconds, showing visible plume advection |
| G2 | Achieve visual quality suitable for artistic/public communication | Atmospheric haze and light scattering effects present |
| G3 | Export volumetric data for downstream creative tools | VDB sequence loadable in TouchDesigner |
| G4 | Validate pipeline against OCO-3 observations | Modeled column XCO2 within 20% of observed enhancements |

---

## Non-Goals

| ID | Explicitly Out of Scope |
|----|------------------------|
| NG1 | Cinematic/photorealistic rendering (Monte Carlo path tracing) |
| NG2 | Real-time interactivity |
| NG3 | Publication-grade scientific accuracy (peer-review ready) |
| NG4 | C++ implementation |
| NG5 | Custom shader development |
| NG6 | Multi-facility visualization |

---

## User Stories

**Primary User**: Artist/creator producing visual communication about industrial CO2 emissions.

1. *As a creator*, I want to see a 3D plume rising from Sasol and dispersing with wind, so that viewers understand emissions don't stay local.

2. *As a creator*, I want atmospheric haze effects so the visualization looks polished, not like a scientific debugging tool.

3. *As a creator*, I want to remix the volumetric data in TouchDesigner, so I can add my own creative elements.

4. *As a creator*, I want the plume behavior to be physically plausible, so the visualization has credibility.

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | System SHALL render 3D volumetric CO2 concentration fields | P0 |
| FR2 | System SHALL animate concentration evolution over minimum 30-day period | P0 |
| FR3 | System SHALL export rendered frames as PNG sequence | P0 |
| FR4 | System SHALL export volumetric data as OpenVDB sequence | P1 |
| FR5 | System SHALL apply transfer function mapping concentration to color/opacity | P0 |
| FR6 | System SHALL include volumetric lighting with scattering approximation | P1 |
| FR7 | System SHALL include depth-based atmospheric haze | P1 |
| FR8 | System SHALL encode PNG sequence to H.264 video | P0 |
| FR9 | System SHALL overlay timestamp on rendered frames | P2 |
| FR10 | System SHALL mark Sasol facility location in visualization | P2 |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1 | Single frame render time | < 10 seconds on A10G |
| NFR2 | Full sequence render time | < 8 hours for 30 days |
| NFR3 | Output resolution | 1920 × 1080 minimum |
| NFR4 | Temporal resolution | Minimum 1 frame per hour of simulation |
| NFR5 | Spatial resolution | 1 km horizontal, 250 m vertical |
| NFR6 | Domain extent | 100 km × 100 km × 15 km |

---

## Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| C1 | Python-only implementation | POC velocity; team expertise |
| C2 | Must run headless on Linux | Cloud GPU deployment (AWS g5) |
| C3 | No proprietary software dependencies | Budget; reproducibility |
| C4 | NVIDIA GPU required | VTK GPU volume rendering; future OptiX path |

---

## Dependencies

### External Data Dependencies

| Dependency | Source | Risk | Mitigation |
|------------|--------|------|------------|
| OCO-3 L2 Lite | NASA Earthdata | Low — public, stable API | Cache downloaded files |
| OCO-2 L2 Lite | NASA Earthdata | Low — public, stable API | Cache downloaded files; same format as OCO-3 |
| ERA5 winds | Copernicus CDS | Medium — rate limits, queue times | Pre-download full period; allow 48hr |
| HYSPLIT model | NOAA ARL | Medium — setup complexity | Synthetic plume as fallback |

### Software Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Runtime |
| VTK | 9.2+ | Volume rendering with scattering |
| PyVista | 0.43+ | High-level VTK interface |
| xarray | 2024.1+ | NetCDF/scientific arrays |
| pyopenvdb | 11.0+ | VDB export |
| ffmpeg | 5.0+ | Video encoding |

---

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| R1 | HYSPLIT setup takes >1 week | Medium | High | Synthetic plume generator works standalone; can ship POC without real transport |
| R2 | OCO-3 coverage over Secunda sparse in chosen period | Medium | Medium | Pre-check coverage before committing to date range; extend window if needed; fuse OCO-2 (sun-synchronous, predictable repeats) with OCO-3 (ISS precessing) for improved coverage |
| R3 | VTK scattering quality insufficient | Low | Medium | Post-processing pipeline (haze, bloom, tonemapping) as quality floor |
| R4 | pyopenvdb installation issues on Linux | Medium | Low | VDB export is P1, not P0; can defer |
| R5 | ERA5 download queue exceeds 48hr | Low | Medium | Submit request on day 1; synthetic wind as interim |

---

## Success Criteria

### MVP (Minimum Viable Product)

- [ ] Video renders showing 3D plume with visible temporal evolution
- [ ] Plume direction correlates with wind direction
- [ ] Basic transfer function distinguishes plume from background
- [ ] Runs end-to-end on AWS g5.xlarge

### Target

- [ ] All MVP criteria
- [ ] Volumetric scattering enabled (VTK GlobalIlluminationReach)
- [ ] Atmospheric haze via post-processing
- [ ] VDB export sequence validates in TouchDesigner
- [ ] OCO-3 overpasses marked when they occur

### Stretch

- [ ] All Target criteria
- [ ] ACES filmic tonemapping
- [ ] Bloom on high-concentration regions
- [ ] Camera motion (orbit or zoom)

---

## Open Questions

| ID | Question | Owner | Status |
|----|----------|-------|--------|
| OQ1 | What specific 30-90 day period has best OCO-2/OCO-3 coverage over Secunda? | Data | Open — multi-satellite search across OCO-2 + OCO-3 addresses sparse coverage |
| OQ2 | Is HYSPLIT or CAMS reanalysis faster path to 3D concentrations? | Eng | Closed — layered architecture adopted: CAMS 9 km background + Gaussian plume + turbulent noise. See RFC Decision 2a. |
| OQ3 | Should we use VAPOR for exploration before committing to VTK render pipeline? | Eng | Open |
| OQ4 | What frame rate / time compression ratio produces best artistic result? | Art | Open |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 0: Environment + Synthetic | 2 days | Rendering pipeline validated with fake data |
| 1: Data Acquisition | 3 days | All external data downloaded |
| 2: Processing Pipeline | 3 days | 4D concentration array on Cartesian grid |
| 3: Rendering + Scattering | 4 days | Single high-quality frame |
| 4: Animation + Post-processing | 3 days | Full video with atmospheric effects |
| 5: VDB Export + Polish | 3 days | TouchDesigner-ready output |

**Total**: ~18 working days

---

## Scope Evolution

**Visualization shows ALL atmospheric CO2 transport**, not only point-source plume. Layered architecture: CAMS background + parametric plume + turbulent noise. OCO-2/OCO-3 as independent validation overlay. Location-portable via `DomainConfig` (Secunda default, Seattle example).

---

## Appendix: Key Technical Insight

OCO-3 measures **column-integrated** XCO2. The satellite cannot distinguish whether CO2 is at 500m or 5km altitude. The 3D vertical structure in this visualization comes entirely from the atmospheric transport model (HYSPLIT), constrained/validated by OCO-3 total column observations.

This is scientifically appropriate — transport models encode the physics of how emissions disperse. The satellite provides ground truth for total amounts. Neither alone produces 3D; combining them does.