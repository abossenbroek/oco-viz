---
name: output-schemas
user-invocable: false
type: reference
primary_owner: shared
---

# Output Schemas

Canonical YAML collaboration payload schemas for all vfx-artist-studio agents.
Every agent MUST produce output conforming to the schema matching its delivery type.

---

## shot_context_update

Produced by the line-producer agent. Represents a state change to the
shot context YAML that coordinates all agent work on a shot.

```yaml
shot_context_update:
  version: string              # required — schema version (e.g. "1.0")
  shot_id: string              # required — shot identifier (e.g. "sc010")
  update_type: string          # required — assign|reassign|status_change|tier_change|param_lock|feedback
  previous_state:              # required — snapshot of changed fields before update
    tier: string               # required — tier before update
    status: string             # required — status before update
    active_agent: string       # required — agent before update
  new_state:                   # required — snapshot of changed fields after update
    tier: string               # required — tier after update
    status: string             # required — status after update
    active_agent: string       # required — agent after update
    next_on_approve: string    # required — downstream agent after approval
  reason: string               # required — why this update was made
  human_involved: bool         # required — whether a human triggered or approved this change
  locked_params_delta: object  # optional — newly locked parameters (key-value)
  audit_trail: string          # required — provenance of the state change
```

---

## tier_promotion_request

Produced by the line-producer agent. Formalizes the promotion of a shot
from one tier to the next, including all gate checks and human approvals.

```yaml
tier_promotion_request:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  from_tier: string            # required — scout|preview (tier being left)
  to_tier: string              # required — preview|final (tier being entered)
  human_approval: bool         # required — must be true for promotion
  human_approval_timestamp: ISO8601  # required — when human approved
  creative_direction_notes: string   # required — human's creative direction summary
  locked_params: object        # required — all parameters locked at this promotion point
  gate_checks:                 # required — array of gate check results
    - gate: string             # required — gate identifier
      passed: bool             # required — whether gate passed
      note: string             # required — measurement or observation
  source_artifacts:            # required — array of artifact paths from the departing tier
    - string                   # absolute or project-relative path
  target_resolution: int       # required — VDB resolution for the new tier (128|512|1024)
  target_voxel_spacing_m: float  # required — voxel spacing in meters for the new tier
  audit_trail: string          # required — full promotion provenance chain
```

---

## effects_delivery

Produced by the effects-td agent. Delivers the result of applying a
lookdev technique (soot-crust, paper-grain, ash-culling, emission,
sedimentary-motion, or three-chords-of-dread) to a shot.

```yaml
effects_delivery:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  technique: string            # required — skill name (e.g. "soot-crust-shader", "paper-grain-manifold")
  tier: string                 # required — scout|preview|final
  knowledge_files_consulted:   # required — array of knowledge file paths read
    - string                   # relative path from plugin root (e.g. "knowledge/houdini-fx-playbook.yaml")
  artifacts:                   # required — array of produced artifacts
    - path: string             # required — path to artifact file
      type: string             # required — vdb|hython|mtlx|usd|exr
      grid_names: [string]     # optional — VDB grid names (for VDB type)
      voxel_count: int         # optional — total voxel count (for VDB type)
      description: string      # optional — what this artifact contains
  parameters_used: object      # required — key-value map of technique parameters applied
  validation:                  # required — self-validation measurements
    voxel_spacing_m: float     # required — actual voxel spacing in meters
    world_size_m: float        # required — world size in meters
    resolution: int            # required — grid resolution (128|512|1024)
    sparse_fraction: float     # required — fraction of inactive voxels (0.0-1.0)
  upstream_refs:               # optional — references to upstream deliverables consumed
    - path: string             # path to upstream artifact
      from_agent: string       # agent that produced it
  audit_trail: string          # required — provenance from knowledge file to artifact
```

---

## houdini_delivery

Produced by the houdini-td agent. Delivers Hython scripts, HDA definitions,
USD scene assemblies, MaterialX shaders, or Karma XPU render configurations.

```yaml
houdini_delivery:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  delivery_type: string        # required — hython_script|hda|usd_assembly|materialx|render_config|upres
  tier: string                 # required — scout|preview|final
  knowledge_files_consulted:   # required — array of knowledge file paths read
    - string                   # e.g. "knowledge/karma-render-profiles.yaml"
  artifacts:                   # required — array of produced artifacts
    - path: string             # required — path to artifact file
      type: string             # required — py|hda|usda|mtlx|yaml
      description: string      # required — what this artifact contains
      version: string          # optional — HDA version or script version
  render_config:               # optional — present when delivery_type is render_config
    renderer: string           # required — "karma_xpu"
    resolution: [int, int]     # required — pixel dimensions
    samples_per_pixel: int     # required — SPP
    volume_step_size_multiplier: float  # required
    max_volume_bounces: int    # required
    denoiser_enabled: bool     # required
    denoiser_type: string      # optional — "oidn"
    denoiser_temporal: bool    # optional
    aov_list: [string]         # required — list of AOV names
    profile_source: string     # required — reference to karma-render-profiles.yaml tier
  upres_config:                # optional — present when delivery_type is upres
    source_resolution: int     # required — source tier resolution
    target_resolution: int     # required — target tier resolution
    detail_octaves: int        # required — Volume Noise octave count
    detail_amplitude: float    # required — Volume Noise amplitude
    interpolation: string      # required — "quadratic" per playbook
  materialx_config:            # optional — present when delivery_type is materialx
    shader_name: string        # required — shader identifier
    hda_version: string        # required — reference to approved HDA version
    inputs: object             # required — shader input parameter values
  usd_config:                  # optional — present when delivery_type is usd_assembly
    layers:                    # required — USD composition layers
      - path: string           # required — layer file path
        purpose: string        # required — base|override|assembly
    stage_metrics:             # required
      up_axis: string          # required — "Y"
      meters_per_unit: float   # required — 1.0
  batch_mode: bool             # required — must be true (all Houdini work is batch-mode)
  audit_trail: string          # required — provenance of Houdini artifact
```

---

## comp_delivery

Produced by the compositor agent. Delivers the multi-pass compositing
specification, AOV routing, grain restoration config, and delivery format spec.

```yaml
comp_delivery:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  tier: string                 # required — scout|preview|final
  knowledge_files_consulted:   # required — array of knowledge file paths read
    - string                   # e.g. "knowledge/compositing-standards.yaml"
  color_management:            # required — color pipeline specification
    working_space: string      # required — "ACEScg"
    rendering_space: string    # required — "ACEScg (AP1 primaries, linear)"
    display_transform: string  # required — ACES view transform name
    ocio_config: string        # required — OCIO config identifier
  aov_routing:                 # required — how each AOV contributes to final
    - aov_name: string         # required — AOV identifier (per compositing-standards.yaml)
      operation: string        # required — add|over|multiply|screen|deep_resolve
      layer_order: int         # required — compositing order (lower = earlier)
      purpose: string          # required — what this AOV provides to the final image
  grain_restoration:           # required — NoisyBeauty grain blend config
    enabled: bool              # required
    blend_factor: float        # required — range [0.10, 0.15]
    source_aov: string         # required — "NoisyBeauty"
    target_aov: string         # required — "Beauty"
    method: string             # required — "motion_tracked_blend"
  deep_compositing:            # optional — present for preview and final tiers
    enabled: bool              # required
    deep_aov: string           # required — "deep"
    resolve_before_flat: bool  # required — must be true per compositing rules
  delivery_formats:            # required — output format specifications
    - format_name: string      # required — exhibition_projection|review_proxy|archive_master|exhibition_print
      format: string           # required — file format (EXR|ProRes|TIFF|DPX)
      resolution: [int, int]   # required — pixel dimensions
      color_space: string      # required — output color space
      bit_depth: string        # required — e.g. "16-bit half-float"
  comp_script_path: string     # required — path to comp script artifact
  audit_trail: string          # required — provenance of compositing decisions
```

---

## void_design_delivery

Produced by the matte-artist agent. Delivers the void/environment design
specification including atmospheric context, boundary dissolution, and
derived format parameters.

```yaml
void_design_delivery:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  tier: string                 # required — scout|preview|final
  knowledge_files_consulted:   # required — array of knowledge file paths read
    - string                   # e.g. "knowledge/exhibition-delivery-spec.yaml"
  void_specification:          # required — core void design
    background_color: [float, float, float]  # required — must be [0.0, 0.0, 0.0]
    background_emission: float # required — must be 0.0
    environment_map: string    # required — null or path to HDRI
    ambient_occlusion: bool    # required — must be false for pure void
    black_point: string        # required — "absolute" (no compensation)
  atmospheric_context:         # required — atmosphere/fog design
    fog_enabled: bool          # required
    fog_density: float         # optional — atmospheric fog density
    fog_color: [float, float, float]  # optional — linear RGB
    fog_narrative_intent: string  # optional — what the fog communicates
  boundary_dissolution:        # required — how the plume meets the void
    method: string             # required — e.g. "exponential_falloff", "noise_erosion"
    falloff_start_density: float  # required — density at which dissolution begins
    falloff_end_density: float # required — density at which plume is fully dissolved
    noise_frequency: float     # optional — dissolution noise frequency
    noise_amplitude: float     # optional — dissolution noise amplitude
  derived_formats:             # optional — format-specific void adaptations
    - format_name: string      # required — exhibition_projection|exhibition_print
      adaptation: string       # required — how void is adapted for this format
      black_point_compensation: bool  # required — must be false for print
  artifacts:                   # required — array of produced artifacts
    - path: string             # required — path to artifact file
      type: string             # required — usda|yaml|py
      description: string      # required — what this artifact contains
  audit_trail: string          # required — provenance of void design decisions
```

---

## finaling_report

Produced by the vfx-supe agent. The result of a finaling pass
(visual check at scout/preview, or two-percent rule at final tier).

```yaml
finaling_report:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  tier: string                 # required — scout|preview|final
  pass_type: string            # required — visual_check|composition_check|render_quality|shader_quality|comp_integrity|two_percent|delivery_check
  checks:                      # required — array of check results
    - name: string             # required — check identifier
      passed: bool             # required — whether check passed
      measured: string         # required — what was observed/measured
      expected: string         # required — what was expected
  overall: string              # required — pass|concern|fail
  blocking_issues:             # optional — issues that block approval
    - check_name: string       # required — reference to checks[].name
      description: string      # required — specific, measurable description of failure
  continuity_notes: string     # optional — cross-shot continuity observations
  revision_targets:            # optional — specific agents/parameters to address
    - target_agent: string     # required — which agent should fix this
      parameter: string        # required — which parameter or artifact needs change
      current_value: string    # required — current measured value
      required_value: string   # required — what it should be
  knowledge_files_consulted:   # optional — finaling reference files
    - string
  audit_trail: string          # required — finaling methodology and data sources
```

---

## wedge_delivery

Produced by the effects-td agent. Delivers the results of a parameter
wedge exploration via TOPs/PDG, including the contact sheet and
top candidate selections.

```yaml
wedge_delivery:
  version: string              # required — schema version
  shot_id: string              # required — shot identifier
  tier: string                 # required — final (wedges are final-tier only)
  knowledge_files_consulted:   # required — array of knowledge file paths read
    - string                   # e.g. "knowledge/houdini-fx-playbook.yaml"
  wedge_config:                # required — wedge parameter space definition
    parameters:                # required — array of wedged parameters
      - name: string           # required — parameter name
        range: [float, float]  # required — min and max values
        steps: int             # required — number of steps
    total_variations: int      # required — product of all parameter steps
    render_tier: string        # required — "final"
  artifacts:                   # required — produced contact sheet and frames
    - path: string             # required — path to artifact
      type: string             # required — exr|png
      description: string      # required — e.g. "contact sheet", "wedge frame 0042"
  contact_sheet:               # required — contact sheet specification
    path: string               # required — path to contact sheet image
    grid_dimensions: [int, int]  # required — rows x columns
    total_frames: int          # required — number of wedge frames
  top_candidates:              # required — ranked candidate selections
    - rank: int                # required — 1-based rank
      wedge_index: int         # required — index into wedge parameter space
      parameters: object       # required — parameter values for this candidate
      frame_path: string       # required — path to this candidate's frame
      selection_rationale: string  # required — measurable reason for ranking
  audit_trail: string          # required — provenance of wedge configuration and selection
```

---

## cross_plugin_request

Used to request action from an agent in another plugin. Bridges the
vfx-artist-studio boundary to pipeline-expert, cinematographer, or
critical-eye plugins.

```yaml
cross_plugin_request:
  version: string              # required — schema version
  requesting_agent: string     # required — vfx-artist-studio agent making request
  target_plugin: string        # required — "pipeline-expert"|"cinematographer"|"critical-eye"
  target_agent: string         # required — specific agent in the target plugin
  request_type: string         # required — review|validate|approve|ideate|exhibition_review
  context:                     # required — request context
    tier: string               # required — scout|preview|final
    artifact_path: string      # required — path to artifact under review
    brief: string              # required — what is being requested and why
    shot_id: string            # optional — shot identifier
  payload: object              # optional — additional structured data
  audit_trail: string          # required — provenance of request
```

---

## Anti-Patterns

- **Schema drift**: Adding fields without updating this document. All schema changes MUST be reflected here first.
- **Optional-by-default**: Fields are required unless explicitly marked optional. Do not treat required fields as optional.
- **Untyped payloads**: Every field must have a declared type. `object` is acceptable only for `payload` in cross_plugin_request, `locked_params`, and `parameters_used`.
- **Missing audit_trail**: Every delivery schema includes audit_trail. Omitting it is a schema violation.
- **Version omission**: Every delivery must include a version field for forward compatibility.
- **Missing knowledge_files_consulted**: Effects-td, houdini-td, compositor, and matte-artist deliveries must declare which knowledge files were read. Omission means the agent operated without reference material.
- **Unlocked promotion**: A tier_promotion_request with `human_approval: false` is invalid. Human approval is mandatory at every tier boundary.
- **Unvalidated effects**: An effects_delivery without the `validation` block is a schema violation. Self-validation is required.

---

## Validation Checklist

- [ ] Output conforms to exactly one schema defined above
- [ ] All required fields are present and non-empty
- [ ] Field types match declared types (string, int, float, bool, array, object)
- [ ] `audit_trail` traces from data source to creative/technical decision
- [ ] `version` field is present and matches current schema version
- [ ] Array fields contain at least one entry (empty arrays are schema violations)
- [ ] `knowledge_files_consulted` references actual files in the knowledge/ directory
- [ ] Physical units are correct (meters for spacing, Kelvin for temperature)
- [ ] Tier value matches the current shot context tier
- [ ] VDB validation measurements match tier-specific expected values from knowledge files
