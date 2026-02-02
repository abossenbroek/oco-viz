# PRD: Sasol Secunda CO2 Atmospheric Visualization — "Soot"

**Version**: 2.0
**Status**: Draft
**Author**: [Author]
**Last Updated**: [Date]

---

## Problem Statement

Sasol Secunda's coal-to-liquids complex emits approximately 57 Mt of CO2 per year — one of the largest single-point sources on Earth. Yet this colossal output is invisible. The gas disperses unmarked into the atmosphere, leaving no visual trace of its scale or consequence.

Making it visible — rendering CO2 as choking industrial soot against a black void — forces confrontation with the anthropocene. OCO-2 and OCO-3 satellite observations provide the concentration measurements; CAMS reanalysis provides the 3D atmospheric context. This visualization transforms those datasets into an immersive, exhibition-quality experience where viewers feel the weight of industrial emissions as oppressive particulate matter.

**Core challenge**: OCO-3 provides column-integrated XCO2 (single value per footprint), not vertical profiles. Reconstructing 3D structure requires coupling satellite observations with atmospheric transport physics and reanalysis fields.

---

## Visual Language Reference

This project follows the **"Soot"** visual language — a machine-readable specification defined in [`plan/visual_language.yaml`](visual_language.yaml).

**Concept**: Anthropocene industrial dread. CO2 rendered as heavy, choking industrial particulate — not decorative vapor, but the suffocating residue of fossil combustion.

**Mood keywords**: industrial, choking, oppressive, smoldering, heavy, suffocating, granular, creeping, inexorable, dread

**Design affirmations** (self-check during development):
- The plume feels industrial and oppressive with weight and texture
- The palette is strictly grey-scale on black
- Edges dissolve into granular soot particles (exhibition tier)
- The volume feels heavy, thick, and choking
- Light is internal and suffocated
- Motion is slow, creeping, and inexorable

---

## Goals

| ID | Goal | Success Metric |
|----|------|----------------|
| G1 | Produce exhibition-quality immersive video showing 3D CO2 plume evolution above Sasol Secunda | Completed video, 30+ seconds, showing visible plume advection at gallery resolution |
| G2 | Achieve anthropocene dread: CO2 rendered as oppressive industrial soot against black void | Viewer emotional response — weight, discomfort, confrontation with scale |
| G3 | Export volumetric data for downstream creative tools | VDB sequence loadable in TouchDesigner |
| G4 | Validate pipeline against OCO-2/OCO-3 observations | Modeled column XCO2 within 20% of observed enhancements (sketch/study tier) |

---

## Non-Goals

| ID | Explicitly Out of Scope |
|----|------------------------|
| NG2 | Real-time interactivity |
| NG3 | Publication-grade scientific accuracy (peer-review ready) |
| NG4 | C++ implementation |
| NG5 | Custom shader development |
| NG6 | Multi-facility visualization |

---

## User Stories

**Primary User**: Artist/creator producing anthropocene installation work about industrial CO2 emissions.

1. *As a creator*, I want CO2 rendered as choking industrial particulate so viewers feel the weight of emissions.

2. *As a creator*, I want three fidelity tiers (sketch/study/exhibition) so I can iterate fast and deliver gallery-quality output.

3. *As a creator*, I want monochrome grey-scale on black void so the material speaks through texture, not color.

4. *As a creator*, I want granular soot dissolution at plume edges so the boundary feels like disintegrating ash.

5. *As a creator*, I want to remix the volumetric data in TouchDesigner, so I can add my own creative elements.

6. *As a creator*, I want the plume behavior to be physically plausible, so the visualization has credibility.

---

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | System SHALL render 3D volumetric CO2 concentration fields | P0 |
| FR2 | System SHALL animate concentration evolution over minimum 30-day period | P0 |
| FR3 | System SHALL export rendered frames as PNG sequence | P0 |
| FR4 | System SHALL export volumetric data as OpenVDB sequence | P1 |
| FR5 | System SHALL apply monochrome grey-scale transfer function mapping concentration to color/opacity, with peak at dirty near-white (#c8c8c8) | P0 |
| FR6 | System SHALL implement internal smoldering volumetric lighting — light suffocated by density, deep interiors brighter than surfaces | P1 |
| FR7 | System SHALL include depth-based atmospheric haze (study tier only; exhibition tier uses pure black void) | P2 |
| FR8 | System SHALL encode PNG sequence to H.264 video | P0 |
| FR9 | System SHALL overlay timestamp on rendered frames (study tier only; no annotations in exhibition) | P2 |
| FR10 | System SHALL mark Sasol facility location in visualization (study tier only) | P2 |
| FR11 | System SHALL support three fidelity tiers: sketch, study, and exhibition | P0 |
| FR12 | System SHALL render plume with monochrome grey-scale transfer function on pure black background | P0 |
| FR13 | System SHALL implement granular particle dissolution at volume boundaries (exhibition tier) | P1 |
| FR14 | System SHALL support internal smoldering light model with no external directional light (exhibition tier) | P1 |
| FR15 | System SHALL implement slow/creeping animation tempo with heavy easing | P1 |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1 | Single frame render time | < 10 seconds on A10G |
| NFR2 | Full sequence render time | < 8 hours for 30 days |
| NFR3 | Output resolution | 1920 x 1080 minimum |
| NFR4 | Temporal resolution | Minimum 1 frame per hour of simulation |
| NFR5 | Spatial resolution | 1 km horizontal, 250 m vertical |
| NFR6 | Domain extent | 100 km x 100 km x 15 km |

---

## Fidelity Tiers

| Aspect | Sketch | Study | Exhibition |
|--------|--------|-------|------------|
| **Purpose** | Fast iteration, form exploration | Density/TF refinement | Gallery-quality output |
| **Treatment** | Wireframe or point cloud on black | Volume rendering with grey-scale TF | Full volume + particle dissolution + turbulent detail |
| **Color** | Single grey, no transfer function | Full Soot palette | Full Soot palette with opacity curves |
| **Particles** | No | No | Granular soot dissolution at edges |
| **Turbulence** | None | Basic noise | Multi-octave, geological folding |
| **Lighting** | None | Basic volume shading | Internal smoldering only |
| **Composition** | Default camera | Adjustable | Fill frame, shallow DOF, asymmetric |
| **Motion** | Fast preview | Standard | Slow, creeping, glacial camera |
| **Annotations** | Yes | Minimal | None |
| **Background** | Black | Black (fog optional for dev visibility) | Pure black void |

---

## Data Sources

| Source | Product | Role | Access |
|--------|---------|------|--------|
| OCO-2 | XCO2 column averages (L2 Lite) | Primary concentration — sun-synchronous, predictable repeats | NASA Earthdata |
| OCO-3 | XCO2 SAM/target mode (L2 Lite) | High-resolution plume structure — ISS precessing orbit | NASA Earthdata |
| ECD | Emission Change Detection | Temporal dynamics — positive delta drives dissolution and turbulence | NASA Earthdata |
| CAMS | Global CO2 reanalysis / high-res forecast (9 km) | Background ambient soot — large-scale 3D CO2 field | Copernicus CDS |
| ERA5 | Reanalysis winds | Meteorological forcing for transport | Copernicus CDS |

**Note**: CAMS does not assimilate OCO-2/OCO-3 (it uses GOSAT), so OCO observations remain independent for validation.

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
| CAMS forecast | Copernicus CDS | Medium — rate limits | Pre-download; synthetic background as fallback |
| HYSPLIT model | NOAA ARL | Medium — setup complexity | Synthetic plume as fallback |

### Software Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
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
| R2 | OCO-3 coverage over Secunda sparse in chosen period | Medium | Medium | Pre-check coverage before committing to date range; extend window if needed; fuse OCO-2 + OCO-3 |
| R3 | VTK scattering quality insufficient for Soot aesthetic | Low | Medium | Post-processing pipeline + particle dissolution system as quality floor |
| R4 | pyopenvdb installation issues on Linux | Medium | Low | VDB export is P1, not P0; can defer |
| R5 | ERA5 download queue exceeds 48hr | Low | Medium | Submit request on day 1; synthetic wind as interim |
| R6 | Particle dissolution performance at exhibition resolution | Medium | Medium | LOD system; pre-compute particle positions; GPU instancing |

---

## Success Criteria

### MVP (Minimum Viable Product)

- [ ] Video renders showing 3D plume with visible temporal evolution
- [ ] Plume direction correlates with wind direction
- [ ] Monochrome grey-scale transfer function on black background
- [ ] Runs end-to-end on AWS g5.xlarge

### Target

- [ ] All MVP criteria
- [ ] Three fidelity tiers functional (sketch/study/exhibition)
- [ ] Internal smoldering lighting model (no external directional light)
- [ ] VDB export sequence validates in TouchDesigner
- [ ] ACES tonemap for exposure control on grey-scale

### Stretch

- [ ] All Target criteria
- [ ] Granular particle dissolution at volume boundaries (exhibition tier)
- [ ] Shallow depth of field (exhibition tier)
- [ ] Slow creeping camera motion with heavy easing
- [ ] ECD-driven temporal turbulence variation

---

## Open Questions

| ID | Question | Owner | Status |
|----|----------|-------|--------|
| OQ1 | What specific 30-90 day period has best OCO-2/OCO-3 coverage over Secunda? | Data | Open — multi-satellite search across OCO-2 + OCO-3 addresses sparse coverage |
| OQ2 | Is HYSPLIT or CAMS reanalysis faster path to 3D concentrations? | Eng | Closed — layered architecture adopted: CAMS 9 km background + Gaussian plume + turbulent noise. See RFC Decision 2a. |
| OQ3 | Should we use VAPOR for exploration before committing to VTK render pipeline? | Eng | Open |
| OQ4 | What frame rate / time compression ratio produces best artistic result? | Art | Open |
| OQ5 | Optimal particle count and dissolution radius for exhibition tier? | Art/Eng | Open |

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

**Visual identity evolved to "Soot"** — anthropocene industrial dread aesthetic. Monochrome grey-scale on black void, internal smoldering light, granular particle dissolution. Three fidelity tiers (sketch/study/exhibition) replace single-quality pipeline.

---

## Appendix: Key Technical Insight

OCO-3 measures **column-integrated** XCO2. The satellite cannot distinguish whether CO2 is at 500m or 5km altitude. The 3D vertical structure in this visualization comes entirely from the atmospheric transport model (HYSPLIT/CAMS), constrained/validated by OCO-3 total column observations.

This is scientifically appropriate — transport models encode the physics of how emissions disperse. The satellite provides ground truth for total amounts. Neither alone produces 3D; combining them does.
