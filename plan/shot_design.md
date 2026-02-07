# Shot Design: "Descent of Carbon"

**Version**: 1.0
**Status**: Production
**Sequence Duration**: 90 seconds (2160 frames at 24fps)
**Aspect Ratio**: 4:5 "The Monolith" (vertical large-format)

---

## 1. Aspect Ratio and Safe Zones

### Primary Format: 4:5 "The Monolith"

The vertical large-format ratio inverts the landscape convention of scientific visualization. Emissions rise; the frame rises with them. The 4:5 proportion echoes the large-format photographic plate — Gursky, Ruff, Struth — grounding the digital volume in the material tradition of the Dusseldorf school.

| Delivery | Aspect | Resolution | Derivation |
|----------|--------|------------|------------|
| **Hero (Exhibition)** | 4:5 | 4800 x 6000 | Primary render |
| **Square (Instagram / Print)** | 1:1 | 4800 x 4800 | Center crop of 4:5 |
| **Vertical (LED Monolith)** | 9:16 | 3375 x 6000 | Extend sides from 4:5 |
| **Ultra-wide (LED Wall)** | 32:9 | 6000 x 1688 | Letterbox from 4:5, extend horizontal |

### Safe Zone Rules

- **Title Safe**: Inner 80% of frame (all text, credits, overlay markers)
- **Action Safe**: Inner 90% of frame (primary plume mass must land here)
- **Bleed Zone**: Outer 10% — soot wisps and trace-density particulate only
- The 1:1 center crop defines the "golden zone" — all critical compositional mass must read within this square

---

## 2. Shot List — "Descent of Carbon"

Six shots. 90 seconds. One continuous emotional arc: from industrial monument to dissolution into void.

### Shot 01 — "The Monolith"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 00:00 - 00:20 (480 frames) |
| **Duration** | 20 seconds |
| **Camera Move** | `boom_up_path()` — vertical rise along plume axis |
| **Camera Position** | Start: base of plume, looking up. End: mid-height, 30 offset from vertical |
| **Easing** | `ease_in_out_cubic` |
| **Angular Velocity** | 0.03 deg/sec (below max 0.05 deg/sec) |
| **Dolly Speed** | 0.8% camera-to-subject distance/sec |
| **Breath Hold** | 2-second hold at apex before cut |
| **VDB Resolution** | 512 (hero framing, close detail) |
| **Composition** | Plume fills 75% of frame vertically. Off-center left, industrial stack implied below frame edge |
| **Print Hero** | YES — still render at 4x step_size, zero motion blur |
| **Emotional Beat** | Awe. Scale. The plume as geological formation |
| **Ghost Light** | `scattering_anisotropy: 0.8`, volume gradient mask applied — internal forward-scatter creates a faint hot spine visible through the dense column |

**Director's Note**: The viewer's first encounter. The plume must feel monumental — a structure, not a cloud. The vertical boom establishes the scale before any lateral context. The camera never reaches the top; the plume exceeds the frame. This is the Barnett Newman zip: a vertical axis of overwhelming presence.

---

### Shot 02 — "The River"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 00:20 - 00:35 (360 frames) |
| **Duration** | 15 seconds |
| **Camera Move** | `parallel_dolly_path()` — lateral tracking parallel to advection axis |
| **Camera Position** | Mid-height, perpendicular to wind direction. Dolly follows plume drift |
| **Easing** | `ease_in_out_cubic` |
| **Angular Velocity** | 0.02 deg/sec |
| **Dolly Speed** | 1.0% camera-to-subject distance/sec |
| **Breath Hold** | None — continuous motion |
| **VDB Resolution** | 256 base + shader displacement |
| **Composition** | Horizontal river of soot across frame. Plume fills 65% width. Drift direction left-to-right |
| **Print Hero** | No |
| **Emotional Beat** | Recognition. The plume has direction, it goes somewhere. It is not contained |
| **Ghost Light** | Standard `scattering_anisotropy: 0.35` |

**Director's Note**: The shift from vertical monument to horizontal river. The parallel dolly reveals the plume's inexorable advection — this is not a static column but a flowing mass, a river of industrial exhaust with no visible end. The lateral motion should feel like standing on a bridge watching floodwater pass beneath.

---

### Shot 03 — "Internal Suffocation"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 00:35 - 00:50 (360 frames) |
| **Duration** | 15 seconds |
| **Camera Move** | `push_in_path()` with modified parameters — extreme close approach |
| **Camera Position** | Start: outside plume boundary. End: inside volume, surrounded by density |
| **Easing** | `heavy_ease_in` (t^4 — very slow start, accelerating entry) |
| **Angular Velocity** | 0.01 deg/sec (near-zero — the volume moves, not the camera) |
| **Dolly Speed** | Starts at 0.3%, accelerates to 1.0% camera-to-subject distance/sec |
| **Breath Hold** | 2-second hold once fully inside |
| **VDB Resolution** | 512 (macro detail, 0.5-unit voxels, frustum-only upres) |
| **Composition** | Frame fills from edges inward. Final frames: 95% opacity, viewer engulfed |
| **Print Hero** | No |
| **Emotional Beat** | Claustrophobia. Submersion. You are inside the emission |
| **Ghost Light** | Internal smoldering intensifies as camera enters — `ambient: 0.6` override during penetration |

**Director's Note**: The shot the entire sequence builds toward. The heavy_ease_in means the approach is agonizingly slow — the viewer sees the boundary coming, sees the granular dissolution of the edge, and then accelerates into the interior. The internal structure should feel geological: folded layers of density, not uniform fog. The 2-second hold at maximum immersion is the moment of suffocation.

---

### Shot 04 — "The God's Eye"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 00:50 - 01:05 (360 frames) |
| **Duration** | 15 seconds |
| **Camera Move** | `nadir_zoom_path()` — directly overhead, slow zoom out |
| **Camera Position** | Directly above plume centroid, looking straight down. Slow pullback |
| **Easing** | `ease_in_out_cubic` |
| **Angular Velocity** | 0.0 deg/sec (locked nadir, no rotation) |
| **Dolly Speed** | 0.5% camera-to-subject distance/sec (zoom out) |
| **Breath Hold** | 2-second hold at nadir before pullback begins |
| **VDB Resolution** | 256 base + shader displacement |
| **Composition** | Plume viewed from above — radial structure visible. Fills 70% of frame as circular/elliptical mass |
| **Print Hero** | YES — still render at 4x step_size, zero motion blur |
| **Emotional Beat** | Omniscience. The satellite's view. This is what OCO-3 sees |
| **Ghost Light** | Standard `scattering_anisotropy: 0.35`, reduced `ambient: 0.3` for top-down depth |

**Director's Note**: The Steyerl shot — "the politics of verticality." The nadir perspective is the drone's eye, the satellite's column measurement, the God's-eye view that reduces a choking industrial reality to a data point. The radial structure of the plume from above should be beautiful and terrible — a dark mandala of combustion. This shot directly references Steyerl's "In Free Fall" and the replacement of the stable horizon with the vertical gaze of surveillance.

---

### Shot 05 — "Dissolution"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 01:05 - 01:20 (360 frames) |
| **Duration** | 15 seconds |
| **Camera Move** | `glacial_drift_path()` — barely perceptible lateral drift |
| **Camera Position** | Return to mid-distance, three-quarter view. Minimal motion |
| **Easing** | `ease_in_out_cubic` |
| **Angular Velocity** | 0.01 deg/sec |
| **Dolly Speed** | 0.2% camera-to-subject distance/sec |
| **Breath Hold** | None — continuous imperceptible drift |
| **VDB Resolution** | 256 |
| **Composition** | Plume at 60% frame fill. Edges actively dissolving — granular soot particles dispersing outward |
| **Print Hero** | No |
| **Emotional Beat** | Entropy. The plume does not end — it disperses. It becomes atmosphere |
| **Ghost Light** | Standard parameters |

**Director's Note**: The plume's edge treatment is the star. The continuous dense interior breaks into progressively smaller clumps, then individual soot particles that scatter outward like disintegrating ash. The camera is nearly still — the dissolution does the work. This is the thermodynamic truth: CO2 does not disappear, it disperses into everything. The nearly static camera forces the viewer to watch the slow, irreversible contamination of the void.

---

### Shot 06 — "The Fade"

| Parameter | Value |
|-----------|-------|
| **Time Code** | 01:20 - 01:30 (240 frames) |
| **Duration** | 10 seconds |
| **Camera Move** | `glacial_drift_path()` — continued imperceptible drift |
| **Camera Position** | Same as Shot 05, continued drift. Camera does not move away |
| **Easing** | `linear` — no acceleration, pure constant drift into darkness |
| **Angular Velocity** | 0.01 deg/sec |
| **Dolly Speed** | 0.1% camera-to-subject distance/sec |
| **Breath Hold** | Final 3-second hold on near-black |
| **VDB Resolution** | 256 |
| **Composition** | Plume density fades. Frame moves toward pure black. Final frame: black void with trace-level wisps (#1a1a1a) barely visible |
| **Print Hero** | No |
| **Emotional Beat** | Absence. The plume is gone from view but not from atmosphere. The void is not empty |
| **Ghost Light** | Fade `ambient` from 0.4 to 0.05 over duration |

**Director's Note**: No hard cut to black. The plume does not end — it falls below the threshold of visibility. The final frames should be nearly indistinguishable from pure black, but not quite. Trace-level wisps at the very edge of perception. The 3-second hold on near-black forces the viewer to sit with absence. The loop point returns to Shot 01 after a 2-second black gap — the plume re-materializes, 57 megatons per year, every year, without end.

---

## 3. Camera Motion Language: "Cubic Heavy"

All camera motion in "Descent of Carbon" follows the Cubic Heavy protocol.

### Motion Constraints

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Primary Easing** | `ease_in_out_cubic` | Smooth acceleration/deceleration with cubic weight |
| **Secondary Easing** | `heavy_ease_in` (t^4) | For approach shots only — agonizing anticipation |
| **Max Angular Velocity** | 0.05 deg/sec | Human eye should not perceive rotation as movement |
| **Dolly Speed** | 1% camera-to-subject distance/sec (max) | Motion should feel geological, not cinematic |
| **Breath Holds** | 2 seconds minimum at shot transitions | Allow the eye to settle, the volume to breathe |
| **Prohibited** | Fast cuts, snap transitions, rack focus, whip pan | These belong to a different visual language |

### Motion Philosophy

The camera moves like a body in deep water — heavy, slow, deliberate, with momentum. Cubic easing provides the weight: the camera must overcome inertia to begin moving and must decelerate gradually to stop. There are no instant starts or stops.

The "breath hold" is borrowed from large-format photography: the moment of stillness before the shutter fires. In motion, it serves as a caesura — a rhythmic pause that allows the viewer to absorb the volume before the next movement begins.

---

## 4. Camera-Relative Procedural Upres

### Resolution Strategy by Shot Type

| Shot Type | Base Sim | Render Resolution | Strategy |
|-----------|----------|-------------------|----------|
| **Macro** (Shots 01, 03) | 256 base | 0.5-unit voxels in frustum | Frustum-only procedural upres — high detail only where the camera sees |
| **Wide** (Shots 02, 04, 05, 06) | 256 base | Base sim + shader displacement | No volumetric upres — shader-level turbulence adds perceived detail |

### Frustum Upres Protocol

For macro shots (camera-to-subject distance < 50 units):

1. Compute camera frustum at render resolution
2. Identify voxels within frustum + 10% margin
3. Subdivide frustum voxels to 0.5-unit spacing
4. Apply multi-octave turbulence (6 octaves) to subdivided region only
5. Blend at frustum boundary to avoid visible seam

This avoids the computational cost of a full 512 or 1024 simulation while delivering macro-level detail where the camera looks.

---

## 5. Ghost Light Reconciliation

The Soot visual language specifies no external lighting — light is internal and suffocated. However, Shot 01 requires a subtle directional cue to establish the plume's three-dimensional structure against the void.

### Ghost Light Parameters (Shot 01 Only)

| Parameter | Standard Soot | Shot 01 Override | Rationale |
|-----------|--------------|-----------------|-----------|
| `scattering_anisotropy` | 0.35 | 0.80 | Strong forward scatter creates a "hot spine" visible through the column, implying depth without external light |
| Volume gradient mask | None | Applied | Mask restricts the anisotropy override to the densest 30% of the volume, preventing halo artifacts at edges |
| External lights | None | None | No external lights added — the effect is achieved purely through modified scattering behavior |

### Reconciliation Statement

The Ghost Light is not a light source. It is a modification of how the volume's internal emission scatters through density. At `scattering_anisotropy: 0.8`, photons from the internal smoldering preferentially scatter forward, creating a brighter spine visible when viewed from the side. This is physically consistent with dense particulate media (coal dust, volcanic ash) and does not violate the Soot principle of no external illumination.

---

## 6. Print Hero Frames

Two shots are designated for archival print output.

### Hero Frame Specifications

| Parameter | Shot 01 "The Monolith" | Shot 04 "The God's Eye" |
|-----------|----------------------|----------------------|
| **Source Frame** | Frame 360 (at apex hold) | Frame 1230 (at nadir hold) |
| **Render Mode** | Still render — separate pass | Still render — separate pass |
| **Motion Blur** | OFF | OFF |
| **Step Size** | 4x exhibition step_size | 4x exhibition step_size |
| **VDB Resolution** | 1024 (full frustum upres) | 512 + shader displacement |
| **Output Format** | 16-bit EXR, linear | 16-bit EXR, linear |
| **Print Resolution** | 12000 x 15000 px (300 DPI at 40"x50") | 12000 x 15000 px |
| **Target Density** | 30-40% peak — maximum textural detail | 30-40% peak |
| **Noise** | Tuned for paper ink limit (Dmax ~2.3) | Tuned for paper ink limit |

### Print Render Differences from Animation

- No temporal anti-aliasing (single frame, not accumulated)
- 4x step_size increases ray-march samples for smoother gradients
- Histogram re-tuned: animation targets display (Dmax ~0.0 for OLED) while print targets paper (Dmax ~2.3 for Hahnemuhle Photo Rag Baryta)
- Peak density reduced to 30-40% to preserve textural detail in ink — at 80-100% density, the baryta paper saturates and detail collapses

---

## 7. New Camera Presets Required

Three new camera path presets are needed beyond the existing four (`reveal_path`, `orbit_rise_path`, `push_in_path`, `glacial_drift_path`).

### 7.1 `boom_up_path()`

**Used in**: Shot 01 "The Monolith"

**Motion**: Vertical rise along the plume's central axis. Camera starts at plume base looking up at ~60 degrees elevation, rises vertically while gradually leveling to ~30 degrees elevation at apex.

```
Start: base of plume, elevation 60deg, distance 1.0x
End:   mid-height, elevation 30deg, distance 1.0x
Motion: pure vertical translation + elevation rotation
Azimuth: fixed (0 deg change)
```

**Implementation Notes**:
- Derives from `reveal_path()` but inverts direction (bottom-up, not top-down)
- Elevation change: 60 deg to 30 deg (camera levels as it rises)
- Position is computed as vertical offset from focal_point base, not spherical
- Focal point tracks upward with camera to maintain plume in frame

### 7.2 `parallel_dolly_path()`

**Used in**: Shot 02 "The River"

**Motion**: Lateral tracking shot perpendicular to the camera-to-subject axis, parallel to the plume's advection direction. Camera maintains constant distance and elevation while translating laterally.

```
Start: left extent of plume advection corridor
End:   right extent of plume advection corridor
Motion: pure lateral translation
Elevation: fixed at 25deg
Distance: fixed at 1.5x
```

**Implementation Notes**:
- New motion type not derived from existing presets
- Requires `advection_direction` parameter (wind vector) to orient the dolly axis
- Camera-to-subject distance remains constant throughout
- Focal point translates with camera to maintain perpendicular viewing angle
- Drift magnitude = plume advection corridor width (configurable)

### 7.3 `nadir_zoom_path()`

**Used in**: Shot 04 "The God's Eye"

**Motion**: Camera positioned directly above plume centroid (elevation 90 degrees), looking straight down. Slow zoom-out (increasing distance) with zero rotation.

```
Start: directly above centroid, distance 0.5x (close nadir)
End:   directly above centroid, distance 2.0x (wide nadir)
Motion: pure vertical pullback
Elevation: locked at 90deg (true nadir)
Azimuth: locked (0 deg change)
Angular velocity: 0.0 deg/sec
```

**Implementation Notes**:
- `view_up` must be explicitly set to avoid gimbal lock at nadir (elevation = 90 deg)
- Use `view_up = (0, 1, 0)` or align with advection direction for consistent "north"
- The spherical coordinate system in `_spherical_position()` handles nadir correctly when `elevation_rad = pi/2`
- Focal point is fixed at plume centroid; only distance changes

---

## 8. Sequence Timing and Loop Structure

### Timing Breakdown

| Shot | Start | End | Duration | Frames (24fps) |
|------|-------|-----|----------|-----------------|
| 01 The Monolith | 00:00 | 00:20 | 20s | 480 |
| 02 The River | 00:20 | 00:35 | 15s | 360 |
| 03 Internal Suffocation | 00:35 | 00:50 | 15s | 360 |
| 04 The God's Eye | 00:50 | 01:05 | 15s | 360 |
| 05 Dissolution | 01:05 | 01:20 | 15s | 360 |
| 06 The Fade | 01:20 | 01:30 | 10s | 240 |
| **Total** | | | **90s** | **2160** |

### Loop Behavior (Exhibition)

- After Shot 06 final hold, 2-second pure black gap (48 frames)
- Crossfade is prohibited — hard cut from black to Shot 01 frame 1
- Total loop: 92 seconds (90s sequence + 2s black)
- Loop count: infinite (BrightSign XT5 unattended playback)

### Emotional Arc

```
Awe → Recognition → Claustrophobia → Omniscience → Entropy → Absence
 01        02             03              04           05        06
```

The arc descends from grandeur to annihilation. The viewer begins in awe of the plume's scale, recognizes its motion and purpose, is engulfed by it, sees it from the perspective of the measuring satellite, watches it dissolve, and is left with absence. The loop restarts — the emissions never stop.

---

## 9. Relationship to Existing Camera System

### Current Presets (camera_path.py)

| Preset | Motion | Used In |
|--------|--------|---------|
| `reveal_path()` | High above, descend to eye level | Reference for `boom_up_path()` (inverted) |
| `orbit_rise_path()` | Orbit + elevation rise, 5 keyframes | Not used in "Descent of Carbon" |
| `push_in_path()` | Far to close approach | Shot 03 (modified parameters) |
| `glacial_drift_path()` | Barely perceptible lateral drift | Shots 05, 06 |

### Easing Functions (easing.py)

| Function | Formula | Used In |
|----------|---------|---------|
| `linear` | t | Shot 06 (final fade) |
| `smoothstep` | t^2(3-2t) | Not used — too light for Soot |
| `ease_in_cubic` | t^3 | Not used directly |
| `ease_in_out_cubic` | cubic bezier | Shots 01, 02, 04, 05 (primary) |
| `heavy_ease_in` | t^4 | Shot 03 (approach) |

### Design Decision: `smoothstep` Exclusion

The default `smoothstep` easing (used as default in all current presets) is excluded from the "Descent of Carbon" sequence. Its symmetric ease-in/ease-out is too gentle for the Soot aesthetic. All shots use `ease_in_out_cubic` (asymmetric, heavier) or `heavy_ease_in` (t^4, deliberately punishing). The `linear` function is used only for the final fade where mechanical constancy serves the emotional beat of inexorable conclusion.
