---
name: installation-architecture
user-invocable: false
---

# Installation Architecture — Room-as-Frame Craft

The gallery space is not a container for the work — it IS part of the work. The void of the room and the void of the frame are continuous. The plume is the only light source. The viewer's body is in the piece, not in front of it.

---

## Room Configuration Calculator

Given room dimensions (W x H x D meters), calculate:

1. **Throw distance** = D x 0.6 (projector positioned 60% back from screen wall)
2. **Screen width** = W x 0.85 (15% margin for frame-edge bleed-to-black)
3. **Screen height** = screen_width / aspect_ratio (2.39 for anamorphic, 1.78 for 16:9)
4. **Required resolution** = screen_width_m / 0.0005 (0.5mm pixel pitch for close viewing at 1m)
5. **Minimum resolution** = screen_width_m / 0.001 (1mm pixel pitch for 2m+ viewing)
6. **Aspect ratio** = screen_width / screen_height (prefer 2.39:1 anamorphic or 16:9)
7. **Viewing cone** = +-30 degrees from center (content must compose from any position in cone)
8. **Ambient light budget** = < 0.5 lux at screen surface (gallery blackout required)

Example: 8m x 4m x 12m room -> throw 7.2m, screen 6.8m wide, 4K minimum (13,600px ideal at 0.5mm pitch, 6,800px at 1mm pitch).

---

## Projection Types

| Type | Resolution | Lumens | When | Notes |
|------|-----------|--------|------|-------|
| **4K DLP** | 3840x2160 | 20,000+ | Standard gallery (screen < 5m) | Adequate for most installations. Ensure native 4K, not pixel-shifted. |
| **Laser 4K** | 3840x2160 | 30,000+ | Large installation (screen 5-8m) | Superior black level (critical for void quality). Long-throw lens essential. |
| **8K** | 7680x4320 | 25,000+ | Museum permanent (close viewing < 1m) | Texture detail visible at intimate distance. Justifies the rendering cost. |
| **Multi-projector blend** | Variable | Cumulative | Wall-sized (screen > 8m) | Edge-blending with geometric correction. Overlap zones must be invisible. Black level matching critical. |

**Critical: black level.** The projector's black must match the room's black. Any grey in the "black" areas breaks the void. Laser projectors excel here. DLP projectors need careful calibration and may require physical masking at frame edges.

---

## Multi-Sensory Integration

### Sound Routing (OSC)

Simulation metrics are routed as OSC messages to the sound designer's system (SuperCollider, Max/MSP, Ableton Live).

| Simulation Metric | OSC Address | Value Range | Sound Mapping |
|-------------------|-------------|-------------|---------------|
| Mean density | `/soot/density/mean` | 0.0-1.0 | Base frequency and volume. Dense = low, rumbling. Sparse = silence. |
| Turbulence intensity | `/soot/turbulence/intensity` | 0.0-1.0 | Harmonic complexity. Laminar = pure tone. Turbulent = rich harmonics, noise. |
| Emission rate | `/soot/emission/rate` | 0.0-1.0 | Onset transients. New emission = percussive attack. Steady = sustained. |
| Wind velocity (vec3) | `/soot/wind/velocity` | -50.0 to 50.0 m/s | Directional panning (ambisonics or stereo). Speed = broadband noise level. |
| Phase (enum) | `/soot/phase/current` | 0-3 | Global state for sound scene transitions. |
| Breath cycle | `/soot/breath/phase` | 0.0-1.0 | Periodic modulation of all sound parameters. The sound breathes with the volume. |

**Protocol:** OSC over UDP, port 57120 (SuperCollider default). Messages sent at render framerate (30-60 Hz for exhibition).

### Haptic Routing (MIDI)

Simulation metrics are mapped to MIDI CC messages for vibration actuators (bass shakers, tactile transducers in floor or seating).

| Simulation Metric | MIDI CC | Channel | Haptic Mapping |
|-------------------|---------|---------|----------------|
| Density pulses | CC 1 | 1 | Floor vibration intensity. The viewer feels the weight through their body. |
| Phase transitions | CC 2 | 1 | Intensity shift envelope. Building -> Chaotic triggers crescendo. |
| Turbulence bursts | CC 3 | 1 | Irregular vibration pattern. Chaotic phase = unpredictable tactile events. |
| Breath cycle | CC 4 | 1 | Slow periodic vibration. The floor breathes. |

**Protocol:** MIDI over USB or 5-pin DIN. Standard MIDI CC range 0-127.

---

## Frame-Edge Treatment

The boundary between projected content and room wall is the most critical spatial detail:

- **Software mask**: Render with 5% black border on all edges (content never reaches frame edge)
- **Physical mask**: Matte black velvet or flocked material at projection boundary for diffuse absorption
- **Projector calibration**: Geometric correction to ensure projected rectangle aligns precisely with physical mask
- **Light spill**: Projector housing must not emit stray light. Baffles on lens if necessary.
- **Scrim option**: For immersive installations, project onto black scrim with viewer behind — the substance floats in space

---

## The Room Test Checklist

1. **Frame edges**: Are they imperceptible? (projection blends to room wall blackness)
2. **Light source**: Is the plume the ONLY light source in the room?
3. **Scale**: Does the piece feel monumental at viewing distance?
4. **Multiple angles**: Does composition hold from left, center, right of viewing cone (+-30 degrees)?
5. **Close viewing**: Is texture detail visible and compelling at 1m?
6. **Far viewing**: Does the overall composition command attention at full room depth?
7. **Duration**: Can a viewer remain for 5+ minutes without losing engagement?
8. **Sound/haptic**: Does multi-sensory layer enhance without distracting?

---

## Installation Validation Checklist

1. Are room calculations physically correct? (throw ratio, pixel pitch, resolution)
2. Does the projector's native black level match the room's ambient black?
3. Is ambient light budget < 0.5 lux at screen surface?
4. Are OSC addresses using standard format? (SuperCollider/Max/MSP compatible)
5. Are MIDI CC mappings in valid range? (0-127, standard channels)
6. Is frame-edge treatment specified? (software mask + physical mask)
7. Does the viewing cone span +-30 degrees with valid composition throughout?
8. Is loop duration 8-15 minutes for continuous exhibition?
