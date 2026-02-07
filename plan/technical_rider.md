# Technical Rider: "Soot" Installation

**Version**: 1.0
**Status**: Production
**Work Title**: *Soot* (2026)
**Document Purpose**: Complete technical specification for gallery installation, covering display, acoustic, spatial, synchronization, environmental, and maintenance requirements.

---

## 1. Display Technology

### Primary Option: Laser Projector

| Parameter | Specification |
|-----------|---------------|
| **Recommended Models** | Christie Eclipse (4K, 15,000:1 native contrast) or Sony SRX-T615 |
| **Minimum Native Contrast** | 10,000:1 (ANSI) — lower contrast will not achieve pure black void |
| **Resolution** | 4K (3840 x 4800 native for 4:5; or 3840 x 2160 rotated for tall-format) |
| **Brightness** | 10,000-15,000 lumens (adjusted to room size; overpowered projector dimmed is better than underpowered at full) |
| **Light Source** | Laser phosphor (no lamp — eliminates hot-spot and lamp decay color shift) |
| **Colorspace** | Rec.709 minimum, DCI-P3 preferred (even for achromatic work, wider gamut ensures purer blacks in the grey ramp) |
| **Throw Ratio** | Calculated per venue — rear projection preferred to eliminate viewer shadow |
| **Lens** | Fixed or short-throw depending on venue depth. No keystone correction (optical alignment only) |
| **Screen** | Stewart Filmscreen StudioTek 130 G4 (gain 1.3, grey base) or equivalent grey-base screen for enhanced black levels |

### Alternative Option: Direct-View LED Wall

| Parameter | Specification |
|-----------|---------------|
| **Pixel Pitch** | 1.2mm or finer (viewing distance > 2m) |
| **Panel Technology** | MicroLED or COB (chip-on-board) — avoids LED "grain" visible at close range |
| **Native Black** | True black (pixel-off) — LED walls achieve infinite contrast |
| **Minimum Size** | 2.4m W x 3.0m H (for 4:5 at comfortable viewing distance) |
| **Recommended Size** | 3.2m W x 4.0m H (gallery-scale impact) |
| **Processing** | Brompton Tessera SX40 or equivalent with per-pixel calibration |
| **Mounting** | Freestanding ground-support structure or wall-mount with 100mm standoff |
| **Viewing Angle** | 160 degrees minimum (critical for off-axis gallery viewing) |

### Display Selection Decision Matrix

| Criterion | Laser Projector | LED Wall |
|-----------|----------------|----------|
| Black level | Very good (grey-base screen) | Perfect (pixel-off) |
| Scale flexibility | Easy to resize via throw | Fixed to panel count |
| Viewer proximity | Shadow risk (front); space needed (rear) | No shadow, close viewing |
| Cost (purchase) | Lower | Higher |
| Cost (rental) | Lower | Moderate |
| Maintenance | Lens cleaning, filter replacement | Panel replacement if failed |
| Transport | 1 case + screen | Multiple panel cases |
| **Recommendation** | Venues with rear-projection depth | Venues without projection depth, or where true black is critical |

---

## 2. Acoustic System

### Sub-Bass Environment

*Soot* uses sound as a physical medium — felt in the body, not heard as music or effect.

| Parameter | Specification |
|-----------|---------------|
| **Frequency Range** | 20-40 Hz primary (sub-bass), 40-80 Hz secondary (low bass) |
| **Content** | Continuous drone — processed industrial recordings (coal combustion, turbine hum, stack exhaust). No melody, no rhythm, no recognizable source |
| **SPL Target** | 75-80 dB(C) at listener position — below pain threshold, above physical sensation threshold |
| **Speaker Type** | Subwoofer: 2x 18" (e.g., Meyer Sound 1100-LFC or d&b audiotechnik SL-SUB) |
| **Placement** | Floor-coupled, behind or beneath display. Sub-bass is omnidirectional; placement is for "weight" not directionality |
| **Isolation** | Rubber isolation mounts to decouple from gallery floor (prevents structural vibration complaints in adjacent spaces) |
| **Processing** | No EQ above 80 Hz. Brick-wall LPF at 100 Hz. The system produces only sub-bass |

### Sound Design Sync

| Shot | Acoustic Event |
|------|----------------|
| 01 The Monolith | Fundamental drone at 28 Hz, slow fade in |
| 02 The River | Add 38 Hz harmonic, slight amplitude modulation (wind turbulence) |
| 03 Internal Suffocation | Peak SPL (80 dB(C)), compression — bass fills listener's chest |
| 04 The God's Eye | Drone recedes to 72 dB(C), thinning — the satellite's remove |
| 05 Dissolution | Harmonic dissolution — frequencies narrow to 22 Hz fundamental only |
| 06 The Fade | Fade to silence over 8 seconds. Final 2 seconds: silence |

### Acoustic Isolation from Adjacent Galleries

- Sub-bass travels through walls and floors. Coordinate with venue to identify structural resonances
- Minimum 20 dB attenuation at gallery boundary (measurement required during tech install)
- If attenuation insufficient: reduce SPL to 70 dB(C) or add mass-loaded vinyl barriers behind subwoofers

---

## 3. Spatial Design

### Generic Gallery Template

Minimum room dimensions for installation viability:

| Parameter | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Width** | 6m | 8m | Display wall + viewing distance |
| **Depth** | 8m | 12m | Rear projection throw (if projector); viewing zone |
| **Height** | 3.5m | 4.5m | Accommodate 4:5 display at scale |
| **Entry** | Single point, light-trapped | Double-door vestibule | See Ambient Light Control below |
| **Exit** | Opposite wall from entry | Same side as entry (loop flow) | Depends on venue floor plan |

### Floor Plan — Generic Gallery (8m x 12m)

```
                    12m
    ┌──────────────────────────────────┐
    │                                  │
    │   ┌──────────────────────┐       │
    │   │                      │       │
    │   │    DISPLAY SURFACE   │       │
    │   │    (3.2m x 4.0m)     │       │
    │   │                      │       │
    │   └──────────────────────┘       │
    │                                  │
    │         PRIMARY VIEWING          │  8m
    │           ZONE (4-6m)            │
    │                                  │
    │     ┌─────────┐  ┌─────────┐    │
    │     │  SUB L  │  │  SUB R  │    │
    │     └─────────┘  └─────────┘    │
    │                                  │
    │  ◄── ENTRY (light-trapped) ──►   │
    └──────────────────────────────────┘
```

### Castello di Rivoli Configuration (Large Gallery)

For a Castello di Rivoli-scale room (~15m x 20m, 5.5m ceiling):

- Display: LED wall, 4.8m W x 6.0m H (4:5), centered on long wall
- Viewing zone: 6-10m from display (entire room becomes the installation)
- Subwoofers: 4x 18" (2 per side), floor-coupled behind LED wall
- Entry: Existing gallery door with added light-trap curtain (heavy black velvet, double-layer)
- Bench: Single oak bench, centered, 6m from display — for sustained viewing (exhibition loops 90s)

### MoMA Configuration (Standard Gallery)

For a MoMA-scale room (~10m x 12m, 4m ceiling):

- Display: Rear-projection on Stewart grey-base screen, 3.2m W x 4.0m H
- Projector: Christie Eclipse, rear-mounted on ceiling bracket, 8m throw
- Viewing zone: 4-8m from screen
- Subwoofers: 2x 18", floor-coupled behind screen wall
- Entry: Standard MoMA gallery threshold with light-trap vestibule addition
- No seating (MoMA standard for time-based media under 5 minutes)

---

## 4. Synchronization

### Unattended Loop (Primary Configuration)

| Parameter | Specification |
|-----------|---------------|
| **Playback Device** | BrightSign XT5 (XT1145) |
| **Media Format** | ProRes 4444 (master) transcoded to H.265 Main 10 for BrightSign |
| **Resolution** | 3840 x 4800 (4:5 native) or 3840 x 2160 (scaled per display) |
| **Frame Rate** | 24 fps (cinematic cadence) |
| **Loop Mode** | Seamless loop with 2-second black inter-loop gap (encoded into media file) |
| **Audio Sync** | Embedded audio track (48 kHz, 24-bit, 2ch for sub-bass LFE routing) |
| **Autostart** | Power-on auto-play, no user interaction required |
| **Schedule** | BrightSign scheduled on/off to match gallery hours |
| **Network** | Ethernet to BrightSign for remote monitoring and content update (optional; not required for playback) |

### Live Generative (Alternative Configuration)

For venues with technical staff and interest in real-time rendering:

| Parameter | Specification |
|-----------|---------------|
| **Platform** | TouchDesigner (latest stable) on dedicated workstation |
| **Hardware** | NVIDIA RTX 4090 or A6000, 64GB RAM, NVMe SSD for VDB sequence |
| **Input** | VDB sequence loaded into TouchDesigner volume rendering |
| **Output** | SDI or HDMI 2.1 to display |
| **Advantage** | Real-time camera variation, responsive to sensor data (optional) |
| **Risk** | Requires on-site technical support; crash recovery; software updates |
| **Recommendation** | Use only at venues with dedicated A/V technician on staff |

---

## 5. Ambient Light Control

### Pure Black Void Requirement

The Soot visual language demands a pure black background (#000000). Any ambient light in the gallery space will raise the displayed black level, destroying the void and reducing the plume to a grey mass on a grey background. Light control is not aesthetic preference — it is a functional requirement of the work.

### Light Trap Specifications

| Element | Specification |
|---------|---------------|
| **Wall Paint** | Museum Black (Rosco Supersaturated or equivalent, <2% reflectance) |
| **Ceiling** | Museum Black or black fabric drop ceiling |
| **Floor** | Dark grey carpet (pure black floor is a trip hazard; dark grey is acceptable) |
| **Entry** | Double-curtain light trap: 2m vestibule with two layers of heavy black velvet (Commando Cloth, 16 oz), overlap minimum 600mm |
| **Exit** | Same specification as entry, or light-trapped corridor |
| **Emergency Lighting** | Recessed floor-level LED strips, red-filtered (<620nm), activated only on fire alarm. Not continuously on |
| **Gallery Lighting** | ALL ceiling/wall fixtures OFF. No accent lighting, no track lighting, no exit signs within sight line |
| **Exit Signs** | Recessed, positioned behind viewer sight line (above entry/exit doors, facing outward). Consult local fire code for minimum requirements |

### Ambient Light Target

| Measurement | Target | Method |
|-------------|--------|--------|
| **Ambient lux at display surface** | < 0.5 lux | Measured with lux meter, all sources active except display |
| **Ambient lux at viewing position** | < 1.0 lux | Measured at bench/standing position |
| **Display black level (on-screen)** | < 0.005 cd/m2 (projector) or 0.0 cd/m2 (LED) | Measured with colorimeter on black test pattern |

---

## 6. Viewer Flow and Spatial Choreography

### Experience Sequence

```
GALLERY CORRIDOR
    │
    ▼
LIGHT TRAP VESTIBULE (2m deep)
    Black velvet curtains, transition from gallery light to darkness
    Viewer pauses to adapt (30-60 seconds typical)
    │
    ▼
THRESHOLD MOMENT
    Viewer parts second curtain and enters the space
    First visual contact with the plume
    The display is the only light source in the room
    │
    ▼
FREE VIEWING ZONE (4-10m from display)
    No prescribed path within the space
    Bench available for sustained viewing (if venue allows)
    Sub-bass is physically felt upon entry
    │
    ▼
EXIT LIGHT TRAP
    Gradual re-adaptation to gallery light
    Wall text and data pedigree panel are in the exit vestibule
    (NOT in the viewing space — no text competes with the plume)
```

### Critical Placement of Wall Text

Wall text, data pedigree, and curatorial materials are placed in the **exit vestibule**, not in the installation space. This is deliberate:

- The viewing experience is pre-verbal. The plume is encountered as material, not as information
- Text in the viewing space creates a reading lamp effect, raising ambient light
- Placing text at the exit allows the viewer to process the experience before contextualizing it
- Data pedigree (satellite methodology, source chain) is available for those who seek it, but does not mediate the primary encounter

---

## 7. Power and Network

### Power Requirements

| Device | Power Draw | Circuit |
|--------|-----------|---------|
| Projector (Christie Eclipse) | 3,200W | Dedicated 20A/240V circuit |
| OR LED Wall (3.2m x 4.0m) | 1,800W | Dedicated 20A/240V circuit |
| Subwoofers (2x) | 2,400W peak (800W average) | Dedicated 20A circuit |
| BrightSign XT5 | 15W | Shared circuit (any outlet) |
| TouchDesigner workstation (if used) | 850W | Dedicated 15A circuit |
| UPS | — | See below |
| **Total (projector config)** | ~4,500W average | 3x dedicated circuits minimum |
| **Total (LED config)** | ~3,100W average | 2x dedicated circuits minimum |

### UPS (Uninterruptible Power Supply)

| Parameter | Specification |
|-----------|---------------|
| **Coverage** | BrightSign + network switch only (NOT projector/LED — they handle power loss gracefully) |
| **Capacity** | 1500VA / 900W (APC Smart-UPS or equivalent) |
| **Runtime** | 15 minutes (sufficient for power blip recovery) |
| **Purpose** | Prevent BrightSign filesystem corruption on unclean shutdown |

### Network

| Requirement | Specification |
|-------------|---------------|
| **Playback** | No network required (BrightSign plays from local storage) |
| **Monitoring** | Ethernet to BrightSign for remote health check (optional) |
| **Content Update** | Ethernet or USB for BrightSign firmware/content update |
| **Live Generative** | Ethernet required for TouchDesigner config (if used) |

### Backup Playback

| Layer | Device | Activation |
|-------|--------|------------|
| Primary | BrightSign XT5 | Auto-start on power |
| Secondary | Backup BrightSign XT5 (cold spare, pre-loaded, on-site) | Manual swap by gallery staff, < 5 minutes |
| Tertiary | USB drive with H.265 file, compatible with any media player | Emergency fallback |

---

## 8. Maintenance

### Daily Checks (Gallery Staff)

| Check | Method | Action if Failed |
|-------|--------|-----------------|
| Display powered on and showing content | Visual inspection | Power cycle BrightSign. If no image: check projector/LED power. Call technical contact |
| No ambient light leaks | Visual inspection from viewing position | Close curtain gaps, check for propped doors |
| Sub-bass audible/felt | Stand in viewing zone for 10 seconds | Check amplifier power. Verify audio cable connection |
| No warning indicators on BrightSign | Green status LED = OK | If red/amber: power cycle. If persistent: swap to backup unit |

### Weekly Checks (Technical Staff)

| Check | Method | Action if Failed |
|-------|--------|-----------------|
| Projector filter status (if applicable) | Projector diagnostic menu | Clean or replace filter |
| Projector lens clean | Visual inspection for dust/smudge | Clean with lens tissue and optical cleaning solution |
| Audio SPL at listening position | SPL meter, C-weighted | Adjust amplifier gain to target 75-80 dB(C) |
| BrightSign storage health | Remote dashboard or on-device menu | Replace SD card if errors detected |
| LED panel inspection (if applicable) | Visual check for dead pixels/tiles | Schedule panel replacement with vendor |
| Curtain integrity | Physical inspection of light traps | Repair gaps, replace worn velvet |

### Emergency Procedures

| Scenario | Immediate Action | Follow-Up |
|----------|-----------------|-----------|
| **Display failure** | Gallery staff: rope off space, place "Temporarily Closed" sign | Technical: diagnose within 4 hours. Swap to backup if available |
| **Audio failure** | Continue exhibition without sound (visual is primary medium) | Technical: diagnose within 24 hours |
| **BrightSign failure** | Swap to backup unit (pre-loaded, on-site) | Technical: diagnose failed unit, reload content if needed |
| **Power outage** | System recovers automatically on power restore (BrightSign auto-play, projector auto-on) | Verify full recovery after power restore |
| **Water/leak** | Power down all equipment immediately. Remove equipment from water path | Do not re-power until equipment is inspected and dried |
| **Fire alarm** | Gallery evacuation per venue protocol. Equipment powers down via building systems | Post-alarm: verify equipment integrity before restart |

### Technical Contact

A technical contact must be designated for each venue installation. This person:

- Has physical access to all equipment (behind screen wall, amp rack, BrightSign)
- Can power-cycle all devices
- Can swap BrightSign to backup unit
- Has remote access to BrightSign dashboard (if networked)
- Response time: < 4 hours during gallery hours, < 24 hours outside hours
