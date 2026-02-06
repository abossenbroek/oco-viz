---
name: spatial-presence
user-invocable: false
---

# Spatial Presence -- Room Test Gate

Gallery projection quality. The room is the frame. The plume is the only
light source. The viewer's body is in the work, not in front of it.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Resolution sufficiency | >= 4K for standard throw, >= 8K for close viewing (< 1m) | Room calculation: screen_width / pixel_pitch |
| Frame-edge blackness | Imperceptible boundary (projection blends to wall) | Edge luminance measurement + physical mask spec |
| Light source | Plume is ONLY light in room | Ambient light budget < 0.5 lux at screen |
| Close viewing (1m) | Texture detail visible and compelling | Visual inspection at near distance |
| Far viewing (room depth) | Composition commands attention | Visual inspection at full throw distance |
| Multi-angle | Works from all positions in +/-30 deg viewing cone | Multi-viewpoint composition analysis |
| Sound/haptic integration | OSC/MIDI routing functional, non-distracting | System test -- SuperCollider/Max/MSP compatible |
| Duration resilience | Viewer engagement sustained >= 5 minutes | Temporal analysis of narrative arc at projection scale |
| Scale | Piece feels monumental at projection size | Room dimension vs screen width assessment |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | Resolution sufficient for viewing distance. Frame edges imperceptible. Plume is sole light source. Compelling at both 1m and full depth. Composition holds across viewing cone. Multi-sensory integration enhances presence. Viewer sustained 5+ minutes. |
| CONCERN | Resolution adequate but not ideal. Frame edges visible on close inspection. Minor ambient light leakage. Works at one distance but not both. Multi-angle holds from center but weakens at extremes. Sound/haptic needs tuning. |
| FAIL | Resolution insufficient -- visible pixelation. Frame edges visible at viewing distance. Ambient light competes with projection. Composition fails at viewing distance. Multi-angle breaks. Sound/haptic distracts. Viewer disengages quickly. |

---

## Agent Responsibility

Primary: Installer
Secondary: Choreographer (multi-angle composition)
