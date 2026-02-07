# Conservation Package Specification: "Soot"

**Version**: 1.0
**Status**: Production
**Work Title**: *Soot* (2026)
**Document Purpose**: MoMA/Tate-grade conservation package for long-term institutional preservation. Follows Variable Media Network best practices, Tate's time-based media conservation guidelines, and MoMA's digital art acquisition protocols.

---

## 1. Conservation Philosophy

*Soot* is a time-based media artwork with dependencies on specific software, hardware, and data sources. Following the Variable Media Network approach, this conservation package distinguishes between what is **essential** (must be preserved or faithfully reproduced) and what can **migrate** (may change with technology while maintaining the work's identity).

### Essential (Must Be Preserved)

| Element | Why Essential |
|---------|--------------|
| **Soot achromatic palette** | R=G=B at all densities; peak at #c8c8c8; never clean white. This IS the work's visual identity |
| **Pure black void** | Background #000000, no ground plane, no sky, no gradient. The void is structural, not decorative |
| **Internal illumination only** | No external light sources. Light suffocated by density. Inverts the convention |
| **90-second "Descent of Carbon" sequence** | 6-shot structure, timing, emotional arc. The sequence is the narrative |
| **4:5 "Monolith" aspect ratio** | Vertical large-format. The frame orientation is a compositional decision, not a technical default |
| **Sub-bass acoustic (20-40 Hz)** | Sound as physical medium, felt not heard. Essential to the embodied experience |
| **Glacial camera motion** | Cubic Heavy motion language: max 0.05 deg/sec, breath holds. The tempo is the emotional register |
| **Source data provenance** | NASA OCO-3/OCO-2, ECMWF CAMS. The satellite origin is part of the work's meaning |
| **Gallery darkness** | < 1.0 lux ambient. The work requires perceptual void — it does not merely prefer it |

### Migratable (May Change with Technology)

| Element | Migration Path |
|---------|---------------|
| **Playback hardware** | BrightSign XT5 today; future hardware acceptable if it achieves seamless loop, auto-play, and sufficient decoding quality |
| **Display technology** | Laser projector or LED wall today; future display acceptable if it achieves true black (#000000 or equivalent), 4:5 native or mapped, and minimum 4K resolution |
| **Rendering software** | VTK + oco-viz Python pipeline today; re-rendering on future platforms acceptable if output matches the visual language specification |
| **Codec/container** | ProRes 4444 / H.265 today; future codecs acceptable if they preserve 10-bit+ depth and lossless or visually lossless quality |
| **Print technology** | Epson UltraChrome Pro12 on Hahnemuhle Baryta today; future printers and papers acceptable if Dmax >= 2.2 on archival substrate |
| **Operating system** | Linux/macOS today; any OS that runs the pipeline or plays back the media |

---

## 2. Source Code Archive

### Git Repository Snapshot

| Deliverable | Specification |
|-------------|---------------|
| **Repository** | Complete git repository of `oco-viz` at exhibition version tag |
| **Format** | `git bundle` (single-file, self-contained) + `.tar.gz` of working tree |
| **Tag** | `v1.0-exhibition` (annotated tag on exact commit used for exhibition renders) |
| **Includes** | All source code, configuration files, YAML ticket specs, plan documents, gallery scripts |
| **Excludes** | `.git/hooks` (may contain system-specific paths), `.env` files, credentials |
| **Location in Archive** | `/source/oco-viz-v1.0-exhibition.bundle` and `/source/oco-viz-v1.0-exhibition.tar.gz` |

### Docker Image

| Deliverable | Specification |
|-------------|---------------|
| **Base Image** | Python 3.11 on Debian Bookworm |
| **Contents** | Complete frozen environment: all Python packages at pinned versions, VTK, PyVista, xarray, pyopenvdb, scipy, numpy, ffmpeg |
| **Format** | Docker image saved as `.tar.gz` via `docker save` |
| **Dockerfile** | Included alongside the image for reproducible builds |
| **Verification** | Image must be tested: `docker run oco-viz:exhibition python -c "import oco_viz; print(oco_viz.__version__)"` |
| **Location in Archive** | `/source/docker/oco-viz-exhibition.tar.gz` and `/source/docker/Dockerfile` |

### Dependency Manifest

| Deliverable | Specification |
|-------------|---------------|
| **pixi.lock** | Exact locked dependency versions from pixi package manager |
| **pyproject.toml** | Project configuration with all dependency constraints |
| **requirements-frozen.txt** | `pip freeze` output from the Docker image for pip-based reproducibility |
| **System packages** | List of OS-level packages (Debian) required: `libvtk9-dev`, `ffmpeg`, etc. |
| **Location in Archive** | `/source/dependencies/` |

---

## 3. Data Archive

### Raw Scientific Data

| Dataset | Format | Size (approx) | Location in Archive |
|---------|--------|---------------|---------------------|
| **OCO-3 L2 Lite v11.1r** | NetCDF-4 / HDF5 | 2-5 GB | `/data/raw/oco3/` |
| **OCO-2 L2 Lite v11.1r** | NetCDF-4 / HDF5 | 2-5 GB | `/data/raw/oco2/` |
| **CAMS Global CO2 Reanalysis** | NetCDF-4 (GRIB converted) | 10-30 GB | `/data/raw/cams/` |
| **ERA5 Reanalysis Winds** | NetCDF-4 (GRIB converted) | 5-15 GB | `/data/raw/era5/` |

### Provenance Metadata

Each raw data file is accompanied by a provenance sidecar file (`*.provenance.json`):

```json
{
  "source": "NASA Earthdata",
  "product": "OCO-3 L2 Lite v11.1r",
  "download_date": "2026-XX-XX",
  "download_url": "https://...",
  "sha256": "...",
  "temporal_range": "2024-01-01 to 2024-03-31",
  "spatial_extent": {
    "lat_min": -28.0,
    "lat_max": -25.0,
    "lon_min": 28.0,
    "lon_max": 31.0
  },
  "processing_notes": "Column-integrated XCO2. Does NOT provide vertical profile."
}
```

### Processed Data

| Dataset | Format | Location in Archive |
|---------|--------|---------------------|
| **4D concentration grid** | xr.Dataset as NetCDF-4 | `/data/processed/concentration_4d.nc` |
| **VDB volume sequence** | OpenVDB | `/data/processed/vdb/` |
| **VTK volume grids** | VTI (VTK ImageData) | `/data/processed/vtk/` |

---

## 4. Disk Image

### Exhibition Playback System Image

| Deliverable | Specification |
|-------------|---------------|
| **Type** | Bit-for-bit disk image of the exhibition playback system's primary storage |
| **Format** | `.img` (raw) or `.dmg` (macOS) or `.iso` (bootable) |
| **Contents** | Operating system, drivers, BrightSign configuration, media files, autostart scripts |
| **Verification** | SHA-256 of the disk image file |
| **Storage** | On archival-grade spinning disk (not SSD — SSDs lose data without power after ~5-10 years) |
| **Location in Archive** | `/system/disk-image/` |

### Playback Hardware Documentation

A detailed specification of the exhibition playback hardware, sufficient to source equivalent replacements:

| Component | Make/Model | Firmware Version | Notes |
|-----------|-----------|-----------------|-------|
| Media player | BrightSign XT1145 | [version] | Primary playback |
| Display | [Specific projector/LED model] | [version] | Per-venue |
| Audio amplifier | [Model] | [version] | Sub-bass only |
| Subwoofers | [Model, qty] | — | 18", floor-coupled |
| Network switch | [Model] | — | Optional, for monitoring |
| UPS | [Model] | — | BrightSign protection |

---

## 5. Variable Media Questionnaire

*Adapted from the Guggenheim's Variable Media Questionnaire and Tate's acquisition documentation framework.*

### 5.1 Work Identity

| Question | Response |
|----------|----------|
| **What is the work?** | A 90-second continuous-loop volumetric video installation with sub-bass acoustic, presented in a light-controlled gallery space. The work visualizes CO2 emissions from Sasol Secunda using satellite data rendered in the "Soot" achromatic visual language |
| **What is the work's ideal state?** | A dark gallery with pure black void (< 1.0 lux ambient), display showing the 6-shot "Descent of Carbon" sequence at 4:5 aspect ratio, sub-bass drone at 75-80 dB(C), continuous loop. Viewer encounters the plume as material presence in a perceptual void |
| **What must remain the same for the work to remain itself?** | See "Essential" list in Section 1. The achromatic palette, pure black void, internal illumination, 90-second sequence structure, 4:5 aspect ratio, sub-bass acoustic, glacial camera motion, and gallery darkness |
| **What can change?** | See "Migratable" list in Section 1. Playback hardware, display technology, rendering software, codec, print technology, operating system |

### 5.2 Display

| Question | Response |
|----------|----------|
| **Can the display technology change?** | Yes, provided it achieves: true black (#000000), 4:5 aspect ratio (native or mapped), minimum 4K resolution, no visible pixel grid at intended viewing distance |
| **Can the display size change?** | Yes, within limits. Minimum: 2.4m x 3.0m (image area). Maximum: constrained by venue. The plume must dominate the viewer's field of vision at the intended viewing distance (4-8m) |
| **Is projection acceptable?** | Yes, provided rear-projection (no viewer shadows) and grey-base screen (enhanced black levels). Front projection acceptable only in rooms where viewer traffic does not cross the projection path |
| **Is LED acceptable?** | Yes. Preferred for true black. Maximum pixel pitch: 1.2mm at intended viewing distance |

### 5.3 Sound

| Question | Response |
|----------|----------|
| **Is sound essential?** | Yes. The sub-bass is felt in the body and is integral to the installation's embodied experience. However, the work can be exhibited without sound if acoustic constraints make sub-bass impossible (e.g., residential building, shared gallery wall). In this case, the absence should be acknowledged in installation documentation |
| **Can the speakers change?** | Yes, provided they reproduce 20-40 Hz cleanly at 75-80 dB(C) at the listener position |
| **Can the sound content change?** | No. The audio track is a fixed composition synchronized to the visual sequence. It is not generative or variable |

### 5.4 Space

| Question | Response |
|----------|----------|
| **Is gallery darkness essential?** | Yes. < 1.0 lux ambient is a functional requirement. The black void is structural, not decorative. If the venue cannot achieve this, the work should not be shown |
| **Is the room size fixed?** | No. Minimum dimensions specified in technical rider. The work scales to the room |
| **Is seating required?** | Recommended (single bench) for exhibition loops. Not required |
| **Is the entry/exit flow prescribed?** | Entry through light-trap vestibule is essential. Wall text in exit vestibule, not in viewing space |

### 5.5 Future Scenarios

| Scenario | Artist's Guidance |
|----------|------------------|
| **Hardware obsolescence** | Replace with equivalent-spec hardware. Prioritize: true black display, sub-bass reproduction, seamless loop playback |
| **Codec obsolescence** | Transcode from ProRes 4444 master to contemporary codec. Verify: 10-bit+ depth, visually lossless, no banding in shadow regions |
| **Re-rendering** | Acceptable if the original pipeline cannot produce output on contemporary hardware. Use the visual_language.yaml as the definitive specification. The re-rendered output must pass visual comparison against the archived exhibition master |
| **Paper/print obsolescence** | Source paper with equivalent or better Dmax on archival cotton rag base. Generate new ICC profile. Proof against archived EXR master |
| **Resolution increase** | If display technology exceeds 4K, re-render at higher resolution from the same VDB sequence. The data supports arbitrary resolution |

---

## 6. Video Documentation

### In-Situ Capture

| Deliverable | Specification |
|-------------|---------------|
| **Full-loop recording** | One complete 90-second loop captured from the viewer's position, including ambient sound. 4K minimum, ProRes 422 or H.265 CRF18 |
| **Room documentation** | Static wide shot showing the full installation: display, room, light traps, viewer scale. 60 seconds minimum |
| **Detail shots** | Close-ups of: display surface, subwoofer placement, light trap entry, wall text panel, BrightSign/equipment rack. 10 seconds each |
| **Viewer interaction** | One loop captured with viewer(s) present, showing scale and engagement pattern. Consent required |
| **Audio capture** | Separate high-quality audio recording of the sub-bass in situ (48kHz/24-bit, binaural or stereo pair at ear height) |
| **Location in Archive** | `/documentation/video/` |

### Full Walkthrough

| Deliverable | Specification |
|-------------|---------------|
| **Entry-to-exit walkthrough** | Continuous single-take recording from gallery corridor through light trap, viewing experience (minimum 1 full loop), and exit. Captures the complete spatial choreography |
| **Narrated technical walkthrough** | Artist or technician walks through equipment, connections, calibration procedures, and troubleshooting steps. 15-30 minutes |
| **Location in Archive** | `/documentation/video/` |

---

## 7. Checksums

### SHA-256 Manifest

Every master file in the archive has a SHA-256 checksum recorded in a manifest file.

| File Category | Manifest Location |
|---------------|-------------------|
| **Source code** | `/checksums/source.sha256` |
| **Raw data** | `/checksums/data-raw.sha256` |
| **Processed data** | `/checksums/data-processed.sha256` |
| **Master media** | `/checksums/media-master.sha256` |
| **Docker image** | `/checksums/docker.sha256` |
| **Disk image** | `/checksums/disk-image.sha256` |
| **Documentation** | `/checksums/documentation.sha256` |

### Manifest Format

```
sha256  filename
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  source/oco-viz-v1.0-exhibition.bundle
...
```

### Verification Procedure

```bash
cd /archive/root
sha256sum -c checksums/source.sha256
sha256sum -c checksums/data-raw.sha256
# ... repeat for each manifest
```

All checksums must pass. Any failure indicates data corruption and must be investigated before the archive is considered valid.

---

## 8. Hardware Specification

### Exhibition Playback System

| Component | Specification | Quantity |
|-----------|---------------|----------|
| **Media Player** | BrightSign XT1145 | 2 (1 primary + 1 cold spare) |
| **Storage** | 128GB Class 10 SD card (BrightSign) | 4 (2 per unit, 1 primary + 1 backup) |
| **Display** | Per technical rider (projector or LED) | 1 |
| **Subwoofers** | 18" powered (Meyer 1100-LFC or d&b SL-SUB) | 2 |
| **UPS** | 1500VA (APC Smart-UPS or equivalent) | 1 |
| **Network Switch** | Managed gigabit (optional, for monitoring) | 1 |
| **Cabling** | HDMI 2.0 (display), XLR (audio), Ethernet (monitoring) | Per venue |

### Redundancy

| Component | Primary | Backup | Swap Time |
|-----------|---------|--------|-----------|
| BrightSign | Unit A (installed) | Unit B (pre-loaded, on-site) | < 5 minutes |
| SD Card | Card A (in Unit A) | Card B (duplicate, sealed) | < 2 minutes |
| Display | Per venue | Per venue (rental backup if available) | 2-4 hours |
| Subwoofer | Unit A | No spare (continues without sound if failed) | N/A |

---

## 9. Installation Manual

### Pre-Installation Checklist

- [ ] Venue confirms room dimensions meet minimum (6m x 8m x 3.5m)
- [ ] Venue confirms dedicated power circuits (see technical rider Section 7)
- [ ] Venue confirms gallery can achieve < 1.0 lux ambient
- [ ] Display technology selected and confirmed (projector or LED)
- [ ] Light trap materials ordered (black velvet, hardware)
- [ ] Sub-bass system confirmed and noise isolation assessed
- [ ] Technical contact designated at venue

### Installation Procedure

**Day 1: Infrastructure**
1. Paint walls and ceiling Museum Black (or confirm existing black)
2. Install light trap vestibule at entry (and exit if separate)
3. Run power to display position, audio position, and BrightSign position
4. Mount display (projector on ceiling/rear bracket, or LED wall assembly)
5. Position and cable subwoofers (floor-coupled, behind or beneath display)

**Day 2: Calibration**
1. Power on display, feed test pattern (SMPTE color bars, then full black, then full white)
2. Focus and align projector (if used) — no keystone, optical alignment only
3. Calibrate display colorspace (Rec.709 or DCI-P3, using colorimeter)
4. Verify black level: < 0.005 cd/m2 on projector, 0.0 on LED
5. Load media onto BrightSign SD card, insert, power on
6. Verify seamless loop playback (watch 3+ full loops)
7. Calibrate audio: SPL meter at listener position, target 75-80 dB(C) weighted
8. Verify sub-bass frequency response: 20-40 Hz clean, no rattle or room modes

**Day 3: Environment**
1. Close all light sources, seal all gaps
2. Measure ambient light: < 1.0 lux at viewing position, < 0.5 lux at display
3. Walk the viewer flow: entry, adaptation, threshold, viewing zone, exit
4. Verify wall text placement in exit vestibule
5. Run full exhibition configuration for 4+ hours unattended
6. Final walkthrough and approval

### Troubleshooting

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| No image on display | BrightSign not outputting | Check power, HDMI cable, SD card seated. Power cycle |
| Image but no loop | SD card corrupt or wrong content | Swap to backup SD card |
| Visible grey in "black" areas | Ambient light leak | Find and seal light source. Check curtains, exit signs, emergency lighting |
| Banding in dark regions | Display bit depth insufficient | Verify 10-bit input. Check HDMI cable supports 4K 10-bit. Adjust BrightSign output settings |
| No sub-bass | Amplifier off or cable disconnected | Check power and XLR connections. Verify BrightSign audio output enabled |
| Room buzzing/rattling | Sub-bass exciting room resonance | Reduce SPL. Apply damping material to rattling fixtures. Adjust subwoofer position |

---

## 10. Dependencies List

### Software Dependencies (Exact Versions)

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.11.x | Runtime |
| VTK | 9.2.x | Volume rendering |
| PyVista | 0.43.x | High-level VTK interface |
| xarray | 2024.1.x | Scientific data arrays |
| pyopenvdb | 11.0.x | VDB export |
| numpy | 1.26.x | Numerical computation |
| scipy | 1.12.x | Interpolation, splines |
| ffmpeg | 5.x | Video encoding |
| Pydantic | 2.x | Config schemas |
| attrs | 23.x | Config schemas |
| ruff | [version] | Linting |
| mypy | [version] | Type checking |
| pyright | [version] | Type checking |
| pytest | [version] | Testing |
| pixi | [version] | Package management |
| Docker | [version] | Containerization |

*Exact versions are pinned in `pixi.lock` and `requirements-frozen.txt` in the source code archive.*

### Hardware Dependencies

| Component | Specification | Minimum Alternative |
|-----------|--------------|---------------------|
| GPU (rendering) | NVIDIA A10G or better | Any NVIDIA GPU with VTK GPU volume rendering support |
| GPU (display) | Integrated in BrightSign or discrete in workstation | H.265 4K decode capability |
| Display | See technical rider | Any display achieving true black, 4:5, 4K+ |
| Audio | 18" subwoofer, 20 Hz response | Any speaker system reproducing 20-40 Hz at 75+ dB(C) |

---

## 11. Contact Information

| Role | Name | Email | Phone | Notes |
|------|------|-------|-------|-------|
| **Artist** | [Name] | [Email] | [Phone] | Primary contact for artistic decisions |
| **Technical Director** | [Name] | [Email] | [Phone] | Primary contact for technical issues, pipeline, rendering |
| **Print Studio** | [Name/Studio] | [Email] | [Phone] | Archival print production |
| **A/V Integrator** | [Name/Company] | [Email] | [Phone] | Per-venue installation support |

---

## 12. Archive Structure

The complete conservation package is organized as follows:

```
soot-conservation-package-v1.0/
├── README.md                           # This document
├── checksums/
│   ├── source.sha256
│   ├── data-raw.sha256
│   ├── data-processed.sha256
│   ├── media-master.sha256
│   ├── docker.sha256
│   ├── disk-image.sha256
│   └── documentation.sha256
├── source/
│   ├── oco-viz-v1.0-exhibition.bundle  # Git bundle
│   ├── oco-viz-v1.0-exhibition.tar.gz  # Working tree snapshot
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── oco-viz-exhibition.tar.gz   # Docker image
│   └── dependencies/
│       ├── pixi.lock
│       ├── pyproject.toml
│       └── requirements-frozen.txt
├── data/
│   ├── raw/
│   │   ├── oco3/                       # OCO-3 L2 Lite NetCDF
│   │   ├── oco2/                       # OCO-2 L2 Lite NetCDF
│   │   ├── cams/                       # CAMS reanalysis NetCDF
│   │   └── era5/                       # ERA5 winds NetCDF
│   └── processed/
│       ├── concentration_4d.nc         # 4D concentration grid
│       ├── vdb/                        # OpenVDB sequence
│       └── vtk/                        # VTK ImageData grids
├── media/
│   ├── master/
│   │   ├── descent-of-carbon.exr/      # 16-bit EXR frame sequence
│   │   ├── descent-of-carbon.mov       # ProRes 4444 master
│   │   └── descent-of-carbon.mp4       # H.265 Main 10 (playback)
│   ├── audio/
│   │   └── sub-bass-mix.wav            # 48kHz/24-bit master audio
│   └── print/
│       ├── hero-01-monolith.exr        # Print hero EXR
│       └── hero-04-gods-eye.exr        # Print hero EXR
├── system/
│   └── disk-image/
│       └── exhibition-playback.img     # Bit-for-bit system image
├── documentation/
│   ├── video/
│   │   ├── full-loop-in-situ.mov       # In-situ capture
│   │   ├── room-documentation.mov      # Static wide shot
│   │   ├── viewer-interaction.mov      # With viewers
│   │   ├── technical-walkthrough.mov   # Narrated tech walk
│   │   └── audio-binaural.wav          # In-situ audio capture
│   ├── plan/
│   │   ├── shot_design.md
│   │   ├── curatorial_framework.md
│   │   ├── technical_rider.md
│   │   ├── print_spec.md
│   │   ├── visual_language.yaml
│   │   └── prd.md
│   ├── variable-media-questionnaire.md # Section 5 of this document
│   └── installation-manual.md          # Section 9 of this document
├── certificates/
│   └── print-certificate-template.pdf  # Certificate of Authenticity template
└── contacts.md                         # Section 11 of this document
```

### Storage Media

The conservation package is stored on:

1. **Primary**: Archival-grade spinning hard disk (HGST Ultrastar or equivalent enterprise drive), stored in climate-controlled conditions (18-22 C, 35-45% RH)
2. **Secondary**: Second identical copy on separate drive, stored at a different physical location
3. **Tertiary**: Cloud storage (institutional repository or dedicated archive service) with geographic redundancy

Spinning disk is preferred over SSD for long-term cold storage: SSDs can lose data without power over periods of 5-10 years, while enterprise spinning disks maintain data integrity for decades in proper storage conditions.

### Verification Schedule

| Interval | Action |
|----------|--------|
| **Annual** | Verify all checksums against manifests. Report any failures |
| **Biennial** | Boot Docker image, verify pipeline runs. Play back master media, verify quality |
| **5-year** | Full conservation review: assess technology drift, update migration plan if needed |
| **10-year** | Consider format migration for any deprecated codecs or file formats |
