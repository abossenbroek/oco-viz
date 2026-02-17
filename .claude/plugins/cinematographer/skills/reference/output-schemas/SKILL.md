---
name: output-schemas
user-invocable: false
type: reference
primary_owner: shared
---

# Output Schemas

Canonical YAML collaboration payload schemas for all cinematographer agents.
Every agent MUST produce output conforming to the schema matching its delivery type.

---

## storyboard_delivery

Produced by the storyboarder agent. Defines the narrative structure, shot sequence,
emotional arc, and timing for a cinematic sequence.

```yaml
storyboard_delivery:
  version: string              # required — schema version (e.g. "1.0")
  creative_brief: string       # required — director's intent in one paragraph
  shots:                       # required — ordered array of shot objects
    - shot_id: string          # required — unique identifier (e.g. "SH010")
      duration_seconds: float  # required — shot duration in seconds
      camera_move: string      # required — dolly|crane|static|orbit|push-in|pull-out|track
      easing: string           # required — ease-in|ease-out|ease-in-out|linear
      emotional_beat: string   # required — e.g. "revelation", "dread", "awe"
      color_palette: string    # required — reference to color-palette skill preset
      narrative_intent: string # required — what the audience should feel/understand
  emotional_arc: string        # required — overall arc description (e.g. "curiosity -> dread -> sublime")
  timing_map:                  # required — sync points between shots and score
    - shot_id: string          # required — reference to shots[].shot_id
      in_frame: int            # required — first frame of shot
      out_frame: int           # required — last frame of shot
      beat_marker: string      # optional — musical or narrative beat alignment
```

---

## visual_bible_delivery

Produced by the production-designer agent. The definitive visual reference document
for a sequence or project.

```yaml
visual_bible_delivery:
  version: string              # required — schema version
  project_name: string         # required — project or sequence identifier
  keyframe_count: int          # required — min 12 (exhibition), 6 (study), 3 (sketch)
  material_presets:            # required — array of material definitions
    - name: string             # required — preset identifier (e.g. "co2_plume_core")
      physical_reference: string # required — real-world material analog
      shader_params:           # required — key-value shader parameters
        base_color: [float, float, float]  # linear RGB
        density_scale: float
        scattering_anisotropy: float
        emission_intensity: float
        roughness: float
  spatial_config:              # required — spatial layout of scene elements
    - element: string          # required — scene element identifier
      position: [float, float, float]  # required — world-space meters
      narrative_intent: string # required — why this element is placed here
  tier: string                 # required — scout|preview|final
  audit_trail: string          # required — provenance of creative decisions
```

---

## lighting_rig_delivery

Produced by the dp (director of photography) agent. Defines the complete
lighting setup for a shot or sequence.

```yaml
lighting_rig_delivery:
  version: string              # required — schema version
  lights:                      # required — array of light definitions
    - name: string             # required — light identifier (e.g. "key_sunset")
      type: string             # required — distant|dome|rect|sphere|cylinder|mesh
      intensity: float         # required — in nits or relative units
      color_temp: int          # required — Kelvin (2000-10000K)
      motivation: string       # required — practical/narrative reason for this light
      position: [float, float, float]  # optional — world-space position (meters)
      rotation: [float, float, float]  # optional — euler angles (degrees)
      falloff: string          # optional — none|linear|quadratic|cubic
      shadow: bool             # optional — whether light casts shadows
  render_config:               # required — render settings tied to this rig
    resolution: [int, int]     # required — pixel dimensions [width, height]
    samples: int               # required — samples per pixel
    tier: string               # required — scout|preview|final
  ambient_config:              # optional — environment/ambient settings
    hdri_path: string          # optional — path to HDRI environment map
    fog_density: float         # optional — atmospheric fog density
    fog_color: [float, float, float]  # optional — linear RGB
  audit_trail: string          # required — provenance of lighting decisions
```

---

## grading_delivery

Produced by the colorist agent. Defines the color pipeline configuration
for a sequence.

```yaml
grading_delivery:
  version: string              # required — schema version
  show_lut_spec:               # required — show-level LUT configuration
    ocio_config_path: string   # required — path to OCIO config file
    cdl:                       # required — ASC CDL parameters
      slope: [float, float, float]    # required — RGB slope
      offset: [float, float, float]   # required — RGB offset
      power: [float, float, float]    # required — RGB power
      saturation: float               # required — global saturation
    achromatic_compliance: bool # required — neutral gray maps to neutral gray
  film_emulation:              # required — film stock emulation settings
    view_transform: string     # required — ACES view transform name
    enabled: bool              # required — whether film emulation is active
  per_shot_overrides:          # optional — shot-level CDL trims
    - shot_id: string          # required — reference to storyboard shot_id
      cdl_trim:                # required — delta CDL values
        slope: [float, float, float]
        offset: [float, float, float]
        power: [float, float, float]
        saturation: float
  audit_trail: string          # required — provenance of grading decisions
```

---

## shot_execution_delivery

Produced by the dp agent after rendering a shot. Contains frame paths
and render statistics.

```yaml
shot_execution_delivery:
  version: string              # required — schema version
  shot_id: string              # required — reference to storyboard shot_id
  tier: string                 # required — scout|preview|final
  frames:                      # required — array of rendered frames
    - path: string             # required — absolute path to rendered frame
      frame_number: int        # required — frame index
      render_time_seconds: float # required — wall-clock render time
  render_stats:                # required — aggregate render statistics
    total_frames: int          # required — number of frames rendered
    total_render_time_seconds: float # required — sum of all frame render times
    peak_memory_gb: float      # required — peak memory usage in GB
    resolution: [int, int]     # required — pixel dimensions
    samples: int               # required — samples per pixel
  audit_trail: string          # required — provenance and render environment
```

---

## dailies_delivery

Produced by the dp or storyboarder after reviewing rendered frames.
Frame-by-frame critique and next-action directives.

```yaml
dailies_delivery:
  version: string              # required — schema version
  sequence_id: string          # required — sequence or project identifier
  reviewed_shots:              # required — array of reviewed shot entries
    - shot_id: string          # required — reference to storyboard shot_id
      frame_notes:             # required — per-frame notes
        - frame_number: int    # required — frame index
          note: string         # required — observation or critique
          severity: string     # required — info|concern|fail
      overall_impression: string # required — shot-level summary
  next_action: string          # required — what happens next (relight|regrade|approve|reshoot)
  blocking_issues:             # optional — issues that prevent approval
    - shot_id: string          # required — which shot is blocked
      issue: string            # required — description of blocking issue
  audit_trail: string          # required — who reviewed, when, context
```

---

## validation_report

Produced by the groundtruth agent. Physical and technical validation
of artifacts against measured references.

```yaml
validation_report:
  version: string              # required — schema version
  target: string               # required — artifact being validated
  tier: string                 # required — scout|preview|final
  checks:                      # required — array of validation checks
    - name: string             # required — check identifier (e.g. "density_range")
      passed: bool             # required — whether check passed
      measured: string         # required — measured value
      expected: string         # required — expected value or range
      physical_reference: string # required — source of expected value
      tolerance: string        # optional — acceptable deviation
  overall: string              # required — pass|concern|fail
  blocking_issues:             # optional — issues that block delivery
    - check_name: string       # required — reference to checks[].name
      description: string      # required — explanation of failure
  audit_trail: string          # required — measurement methodology, data sources
```

---

## cross_plugin_request

Used to request action from a pipeline-expert agent. Bridges the
cinematographer and pipeline-expert plugin boundaries.

```yaml
cross_plugin_request:
  version: string              # required — schema version
  requesting_agent: string     # required — cinematographer agent making request
  target_plugin: string        # required — "pipeline-expert"
  target_agent: string         # required — specific pipeline-expert agent
  request_type: string         # required — review|validate|ideate|approve
  context:                     # required — request context
    tier: string               # required — scout|preview|final
    artifact_path: string      # required — path to artifact under review
    brief: string              # required — what is being requested and why
  payload: object              # optional — additional structured data
  audit_trail: string          # required — provenance of request
```

---

## Anti-Patterns

- **Schema drift**: Adding fields without updating this document. All schema changes MUST be reflected here first.
- **Optional-by-default**: Fields are required unless explicitly marked optional. Do not treat required fields as optional.
- **Untyped payloads**: Every field must have a declared type. `object` is acceptable only for `payload` in cross_plugin_request.
- **Missing audit_trail**: Every delivery schema includes audit_trail. Omitting it is a schema violation.
- **Version omission**: Every delivery must include a version field for forward compatibility.

---

## Validation Checklist

- [ ] Output conforms to exactly one schema defined above
- [ ] All required fields are present and non-empty
- [ ] Field types match declared types (string, int, float, bool, array)
- [ ] `audit_trail` traces from data source to creative decision
- [ ] `version` field is present and matches current schema version
- [ ] Array fields contain at least one entry (empty arrays are schema violations)
