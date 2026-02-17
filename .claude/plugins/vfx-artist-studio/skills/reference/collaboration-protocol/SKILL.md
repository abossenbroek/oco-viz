---
name: collaboration-protocol
user-invocable: false
type: reference
primary_owner: shared
---

# Collaboration Protocol

THE central handoff mechanism for all vfx-artist-studio agent interactions.
Every inter-agent delivery, request, and status update flows through
collaboration YAML documents conforming to this protocol. The vfx-artist-studio
extends the cinematographer collaboration protocol with shot-context-driven
coordination and production-tier promotion workflows.

---

## Principle

Agents communicate through structured YAML payloads, never through
unstructured text or implicit assumptions. The collaboration YAML is the
single source of truth for what was delivered, by whom, to whom, and what
happens next. If there is no collaboration YAML, there was no handoff.

The vfx-artist-studio introduces a **pull-based coordination** model via
shot context YAML. Instead of agents pushing work to each other, agents
pull their next assignment by checking `shot_context.yaml` for shots
where `active_agent` matches their identity and `status` is `wip`.
The line-producer is the sole writer of shot context state.

---

## Universal Collaboration YAML Format

Every collaboration YAML document MUST contain these fields:

```yaml
collaboration:
  version: string        # required — protocol version (e.g. "1.0")
  from_agent: string     # required — producing agent identifier
  to_agent: string       # required — consuming agent identifier
  command: string        # required — the command/action that triggered this handoff
  tier: string           # required — scout|preview|final
  timestamp: ISO8601     # required — when this collaboration YAML was produced
  status: string         # required — ready|pending_approval|blocked|superseded
  payload: object        # required — delivery-specific content (per output-schemas)
  audit_trail: string    # required — provenance chain from source to delivery
  next_action: string    # required — directive for the downstream agent
  constraints_checked:   # optional — list of validated constraints
    - name: string       # constraint name
      passed: bool       # whether it passed
      note: string       # measurement or observation
```

---

## Independence Firewall

Collaboration YAML documents carry ONLY objective, measurable information.

**Allowed in payloads:**
- Measured values (density, voxel count, render time, sample count, resolution)
- Schema-conformant structured data
- File paths to artifacts (VDB, USD, MaterialX, EXR, Hython scripts)
- Constraint check results (pass/fail with measurements)
- Locked parameter values and their provenance
- Knowledge file references (paths to knowledge/ YAML files consulted)

**Forbidden in payloads:**
- Subjective artistic assessment ("this looks beautiful")
- Narrative commentary ("I think the emission could be stronger")
- Recommendations beyond the `next_action` field
- Emotional language or persuasive framing
- Opinions on another agent's work quality

Subjective assessment belongs in finaling reports (vfx-supe) or
critical-eye reviews (cross-plugin), not in handoff payloads.
The independence firewall ensures each agent forms its own technical
judgment from the raw artifact, not from another agent's opinion of it.

---

## Schema Validation Rules

### Required Fields

Every collaboration YAML must pass these checks:

| Field | Type | Allowed Values |
|-------|------|----------------|
| `version` | string | Semantic version (e.g. "1.0", "1.1") |
| `from_agent` | string | line-producer, houdini-td, vfx-supe, effects-td, compositor, matte-artist |
| `to_agent` | string | Any vfx-artist-studio, cinematographer, pipeline-expert, or critical-eye agent |
| `command` | string | Non-empty string identifying the triggering command |
| `tier` | string | scout, preview, final |
| `timestamp` | string | ISO 8601 format |
| `status` | string | ready, pending_approval, blocked, superseded |
| `payload` | object | Must conform to one output-schema |
| `audit_trail` | string | Non-empty provenance chain |
| `next_action` | string | Non-empty directive |

### Payload Conformance

The `payload` field must conform to exactly one schema from
`reference/output-schemas`. The schema is determined by the
`from_agent` and `command` combination:

| from_agent | Payload Schema |
|------------|---------------|
| line-producer (status) | shot_context_update |
| line-producer (promote) | tier_promotion_request |
| effects-td (effect) | effects_delivery |
| effects-td (wedge) | wedge_delivery |
| houdini-td (houdini) | houdini_delivery |
| compositor (comp) | comp_delivery |
| matte-artist (void) | void_design_delivery |
| vfx-supe (final) | finaling_report |
| any (cross-plugin) | cross_plugin_request |

---

## Shot Context YAML — Pull-Based Coordination

The shot context YAML is the coordination hub for each shot. It lives at
`output/shots/{shot_id}/shot_context.yaml` and is the SOLE mechanism
through which agents discover their work assignments.

```yaml
shot_context:
  shot_id: string          # required — e.g. "sc010"
  tier: string             # required — scout|preview|final
  status: string           # required — wip|pending_review|approved|rejected|blocked
  active_agent: string     # required — which agent currently owns the shot
  assigned_by: string      # required — always "line-producer"
  next_on_approve: string  # required — who receives the shot after approval
  locked_params: object    # required — parameters locked by human (grows per tier)
  artifacts:               # required — array of artifact references
    - path: string         # required — relative path to artifact
      type: string         # required — vdb|usd|mtlx|exr|py|hda
      produced_by: string  # required — agent that created this artifact
      tier: string         # required — tier at which this artifact was produced
      timestamp: ISO8601   # required — when artifact was created
  feedback_log:            # required — array of feedback entries
    - from_agent: string   # required — who provided the feedback
      timestamp: ISO8601   # required — when feedback was given
      verdict: string      # required — approved|rejected|concern
      notes: string        # required — specific, measurable feedback
```

**Write authority**: Only the line-producer agent writes shot context YAML.
All other agents read it to determine their current assignment.

**State transitions**: `wip` -> `pending_review` -> `approved` | `rejected` | `blocked`.
Tier transitions: `scout` -> `preview` -> `final` (non-negotiable order).

---

## Handoff Inventory

The 12 canonical handoff types in the vfx-artist-studio pipeline:

| # | From | To | Payload Schema | Trigger |
|---|------|----|----------------|---------|
| 1 | line-producer | effects-td | shot_context_update | Shot assigned for lookdev |
| 2 | effects-td | vfx-supe | effects_delivery | Effects technique implemented |
| 3 | vfx-supe | line-producer | finaling_report | Scout/preview visual check complete |
| 4 | line-producer | houdini-td | tier_promotion_request | Tier promoted, Houdini setup needed |
| 5 | houdini-td | vfx-supe | houdini_delivery | Render config / MaterialX / USD ready |
| 6 | effects-td | vfx-supe | wedge_delivery | Contact sheet wedge results |
| 7 | matte-artist | vfx-supe | void_design_delivery | Void/environment design complete |
| 8 | compositor | vfx-supe | comp_delivery | Multi-pass comp specification ready |
| 9 | vfx-supe | effects-td | finaling_report | Revision required with specific notes |
| 10 | line-producer | critical-eye | cross_plugin_request | Exit criteria met, exhibition review |
| 11 | any | pipeline-expert | cross_plugin_request | Governance approval needed |
| 12 | any | cinematographer | cross_plugin_request | Upstream creative input needed |

---

## Example Collaboration YAML Documents

### Effects-TD to VFX-Supe handoff (effects delivery)

```yaml
collaboration:
  version: "1.0"
  from_agent: "effects-td"
  to_agent: "vfx-supe"
  command: "effect"
  tier: "scout"
  timestamp: "2026-02-15T14:30:00Z"
  status: "ready"
  payload:
    effects_delivery:
      version: "1.0"
      shot_id: "sc010"
      technique: "soot-crust-shader"
      tier: "scout"
      knowledge_files_consulted:
        - "knowledge/houdini-fx-playbook.yaml"
      artifacts:
        - path: "output/shots/sc010/vdb/sc010.scout.density.vdb"
          type: "vdb"
          grid_names: ["density"]
          voxel_count: 2097152
        - path: "output/shots/sc010/scripts/soot_crust_scout.py"
          type: "hython"
          description: "Hython batch script applying soot-crust technique at scout resolution"
      parameters_used:
        crust_threshold: 0.4
        blend_width: 0.05
        density_scale: 1.0
      validation:
        voxel_spacing_m: 0.078125
        world_size_m: 10.0
        resolution: 128
        sparse_fraction: 0.73
  audit_trail: "effects-td -> soot-crust-shader skill -> houdini-fx-playbook.yaml recipe -> sc010 scout VDB"
  next_action: "vfx-supe: visual check of soot-crust shader at scout resolution"
  constraints_checked:
    - name: "voxel_spacing"
      passed: true
      note: "0.078125 m matches scout tier (10.0 / 128)"
    - name: "sparse_topology"
      passed: true
      note: "73% inactive voxels — sparse design maintained"
    - name: "grid_names"
      passed: true
      note: "density grid uses standard Houdini naming"
```

### Line-producer tier promotion request

```yaml
collaboration:
  version: "1.0"
  from_agent: "line-producer"
  to_agent: "houdini-td"
  command: "promote"
  tier: "preview"
  timestamp: "2026-02-15T16:00:00Z"
  status: "ready"
  payload:
    tier_promotion_request:
      version: "1.0"
      shot_id: "sc010"
      from_tier: "scout"
      to_tier: "preview"
      human_approval: true
      human_approval_timestamp: "2026-02-15T15:45:00Z"
      creative_direction_notes: "Human approved scout lookdev. Proceed to preview resolution."
      locked_params:
        crust_threshold: 0.4
        blend_width: 0.05
      gate_checks:
        - gate: "vfx_supe_approved"
          passed: true
          note: "VFX supe visual check passed at scout tier"
        - gate: "human_creative_direction"
          passed: true
          note: "Human approved creative direction via /promote command"
      source_artifacts:
        - "output/shots/sc010/vdb/sc010.scout.density.vdb"
      target_resolution: 512
      target_voxel_spacing_m: 0.01953125
  audit_trail: "line-producer -> scout approved by vfx-supe -> human creative approval -> promote to preview"
  next_action: "houdini-td: set up preview-tier render config and upres VDB from scout to 512^3"
```

### VFX-supe finaling report (blocked)

```yaml
collaboration:
  version: "1.0"
  from_agent: "vfx-supe"
  to_agent: "effects-td"
  command: "final"
  tier: "final"
  timestamp: "2026-02-15T18:00:00Z"
  status: "blocked"
  payload:
    finaling_report:
      version: "1.0"
      shot_id: "sc010"
      tier: "final"
      pass_type: "two_percent"
      checks:
        - name: "crust_read"
          passed: true
          measured: "Surface reads matte black, interior translucent grey"
          expected: "Dual-state soot crust per exhibition-delivery-spec.yaml"
        - name: "grain_visibility"
          passed: false
          measured: "Grain visible at density 0.5"
          expected: "Grain invisible above density 0.08"
        - name: "black_level"
          passed: true
          measured: "Background pixels (0,0,0)"
          expected: "Pure black void"
        - name: "temporal_stability"
          passed: true
          measured: "Flicker variance 0.002"
          expected: "< 0.005"
      overall: "fail"
      blocking_issues:
        - check_name: "grain_visibility"
          description: "Paper Grain Manifold amplitude too high — grain reads at density 0.5, should be invisible above 0.08. Reduce grain_amplitude."
      continuity_notes: "Cross-shot continuity verified for sc008-sc012 range."
  audit_trail: "vfx-supe -> sc010 final frames -> two-percent-rule skill -> grain_visibility failed"
  next_action: "effects-td: reduce grain_amplitude to restore invisible-grain above density 0.08, re-render affected frames"
```

---

## Cross-Plugin Handoff Boundaries

The vfx-artist-studio interacts with three other plugins:

| Target Plugin | Typical Request | Requesting Agent | Target Agent |
|---------------|----------------|-----------------|--------------|
| **pipeline-expert** | Governance approval | line-producer | Auteur |
| **cinematographer** | Upstream lighting/storyboard data | houdini-td, effects-td | dp, storyboarder |
| **critical-eye** | Exhibition-level visual review | line-producer | critical-eye agent |

Cross-plugin handoffs use the `cross_plugin_request` schema, identical
to the cinematographer protocol. The vfx-artist-studio line-producer is
the sole agent authorized to initiate cross-plugin requests on behalf
of the studio.

---

## Anti-Patterns

- **Narrative leakage**: Including subjective assessment in payload fields. "The emission looks gorgeous" is narrative leakage. "emission_intensity: 1.5, pulse_amplitude: 0.2" is data.
- **Missing provenance**: Producing a collaboration YAML without audit_trail. Every handoff must be traceable to its source.
- **Schema violation**: Payload that does not conform to the declared output-schema. Malformed payloads are rejected at the protocol level.
- **Implicit handoff**: Relying on file system conventions instead of explicit collaboration YAML. If there is no collaboration YAML, the handoff did not happen.
- **Status forgery**: Setting `status: ready` when validation actually failed. Status must reflect the true state of the artifact.
- **Stale references**: Referencing a superseded collaboration YAML. Always reference the latest version.
- **Bidirectional payload**: Stuffing both request and response data into a single collaboration YAML. Each document represents one directional handoff.
- **Shot context tampering**: Any agent other than line-producer writing to shot_context.yaml. Only line-producer has write authority.
- **Push-based assignment**: An agent assigning work to another agent directly. All assignments flow through shot context updates by the line-producer.
- **Tier skipping**: Promoting directly from scout to final. Tier progression is strictly sequential: scout -> preview -> final.
- **Unlocked parameter promotion**: Promoting to a higher tier without human parameter lock. Human creative direction approval is required at every tier boundary.

---

## Validation Checklist

- [ ] All required fields present and correctly typed
- [ ] `from_agent` is a valid vfx-artist-studio agent (line-producer, houdini-td, vfx-supe, effects-td, compositor, matte-artist)
- [ ] `to_agent` is a valid vfx-artist-studio, cinematographer, pipeline-expert, or critical-eye agent
- [ ] `tier` is one of: scout, preview, final
- [ ] `status` is one of: ready, pending_approval, blocked, superseded
- [ ] `payload` conforms to exactly one output-schema
- [ ] `audit_trail` is non-empty and traces to source
- [ ] `next_action` is non-empty and actionable
- [ ] No subjective language in payload fields (independence firewall)
- [ ] `timestamp` is valid ISO 8601
- [ ] Shot context YAML is updated only by line-producer
- [ ] Cross-plugin requests initiated only by line-producer
- [ ] Tier promotion includes human approval evidence
- [ ] Knowledge file references use paths relative to plugin root
