---
name: collaboration-protocol
user-invocable: false
type: reference
primary_owner: shared
---

# Collaboration Protocol

THE central handoff mechanism for all cinematographer agent interactions.
Every inter-agent delivery, request, and status update flows through
collaboration YAML documents conforming to this protocol.

---

## Principle

Agents communicate through structured YAML payloads, never through
unstructured text or implicit assumptions. The collaboration YAML is the
single source of truth for what was delivered, by whom, to whom, and what
happens next. If there is no collaboration YAML, there was no handoff.

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
- Measured values (color temperature, density, resolution, frame count)
- Schema-conformant structured data
- File paths to artifacts
- Constraint check results (pass/fail with measurements)

**Forbidden in payloads:**
- Subjective artistic assessment ("this looks beautiful")
- Narrative commentary ("I think the lighting could be warmer")
- Recommendations beyond the `next_action` field
- Emotional language or persuasive framing

Subjective assessment belongs in verdict-protocol outputs, not in
handoff payloads. The independence firewall ensures each agent forms
its own artistic judgment from the raw artifact, not from another
agent's opinion of it.

---

## Schema Validation Rules

### Required Fields

Every collaboration YAML must pass these checks:

| Field | Type | Allowed Values |
|-------|------|----------------|
| `version` | string | Semantic version (e.g. "1.0", "1.1") |
| `from_agent` | string | dp, production-designer, colorist, storyboarder, groundtruth |
| `to_agent` | string | Any cinematographer or pipeline-expert agent |
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
| storyboarder | storyboard_delivery |
| production-designer | visual_bible_delivery |
| dp (lighting) | lighting_rig_delivery |
| dp (execution) | shot_execution_delivery |
| dp (dailies) | dailies_delivery |
| colorist | grading_delivery |
| groundtruth | validation_report |
| any (cross-plugin) | cross_plugin_request |

---

## Handoff Inventory

The 8 canonical handoff types in the cinematographer pipeline:

| # | From | To | Payload Schema | Trigger |
|---|------|----|----------------|---------|
| 1 | storyboarder | dp | storyboard_delivery | Sequence planning complete |
| 2 | storyboarder | production-designer | storyboard_delivery | Visual bible needed |
| 3 | production-designer | dp | visual_bible_delivery | Bible approved by governance |
| 4 | dp | colorist | lighting_rig_delivery | Lighting rig ready for grading |
| 5 | colorist | dp | grading_delivery | Grade ready for render |
| 6 | dp | groundtruth | shot_execution_delivery | Frames ready for validation |
| 7 | groundtruth | dp | validation_report | Validation complete |
| 8 | any | pipeline-expert | cross_plugin_request | Governance approval needed |

---

## Example Collaboration YAML Documents

### Storyboard to DP handoff

```yaml
collaboration:
  version: "1.0"
  from_agent: "storyboarder"
  to_agent: "dp"
  command: "sequence-plan"
  tier: "preview"
  timestamp: "2026-02-15T14:30:00Z"
  status: "ready"
  payload:
    storyboard_delivery:
      version: "1.0"
      creative_brief: "Industrial plume rising against twilight sky. Arc from
                       quiet observation to dawning dread as scale becomes apparent."
      shots:
        - shot_id: "SH010"
          duration_seconds: 8.0
          camera_move: "push-in"
          easing: "ease-in-out"
          emotional_beat: "curiosity"
          color_palette: "twilight_industrial"
          narrative_intent: "Establish scale — viewer realizes this is not cloud but emission"
      emotional_arc: "curiosity -> recognition -> dread -> sublime"
      timing_map:
        - shot_id: "SH010"
          in_frame: 1
          out_frame: 192
          beat_marker: "score_entry"
  audit_trail: "storyboarder -> creative_brief from Auteur directive 2026-02-14 -> SH010 derived from sequence-design skill"
  next_action: "dp: build lighting rig for SH010 using twilight_industrial palette"
```

### Groundtruth validation report

```yaml
collaboration:
  version: "1.0"
  from_agent: "groundtruth"
  to_agent: "dp"
  command: "validate-render"
  tier: "preview"
  timestamp: "2026-02-15T16:00:00Z"
  status: "blocked"
  payload:
    validation_report:
      version: "1.0"
      target: "output/frames/SH010/preview_v1"
      tier: "preview"
      checks:
        - name: "density_range"
          passed: true
          measured: "0.0 - 847.3 kg/m3"
          expected: "0.0 - 1000.0 kg/m3"
          physical_reference: "OCO-3 XCO2 retrieval bounds"
        - name: "color_temp_key"
          passed: false
          measured: "3200K"
          expected: "5000-5600K (twilight)"
          physical_reference: "CIE D55 illuminant"
      overall: "fail"
      blocking_issues:
        - check_name: "color_temp_key"
          description: "Key light 3200K reads as tungsten, not twilight. Contradicts storyboard palette."
  audit_trail: "groundtruth -> SH010 preview_v1 frames -> density from VDB grid -> color_temp from lighting_rig_delivery"
  next_action: "dp: correct key light color_temp to 5000-5600K range and re-render"
```

---

## Anti-Patterns

- **Narrative leakage**: Including subjective assessment in payload fields. "The lighting feels warm and inviting" is narrative leakage. "Key light color_temp: 3200K" is data.
- **Missing provenance**: Producing a collaboration YAML without audit_trail. Every handoff must be traceable to its source.
- **Schema violation**: Payload that does not conform to the declared output-schema. Malformed payloads are rejected at the protocol level.
- **Implicit handoff**: Relying on file system conventions instead of explicit collaboration YAML. If there is no collaboration YAML, the handoff did not happen.
- **Status forgery**: Setting `status: ready` when validation actually failed. Status must reflect the true state of the artifact.
- **Stale references**: Referencing a superseded collaboration YAML. Always reference the latest version.
- **Bidirectional payload**: Stuffing both request and response data into a single collaboration YAML. Each document represents one directional handoff.

---

## Validation Checklist

- [ ] All required fields present and correctly typed
- [ ] `from_agent` is a valid cinematographer agent
- [ ] `to_agent` is a valid cinematographer or pipeline-expert agent
- [ ] `tier` is one of: scout, preview, final
- [ ] `status` is one of: ready, pending_approval, blocked, superseded
- [ ] `payload` conforms to exactly one output-schema
- [ ] `audit_trail` is non-empty and traces to source
- [ ] `next_action` is non-empty and actionable
- [ ] No subjective language in payload fields (independence firewall)
- [ ] `timestamp` is valid ISO 8601
