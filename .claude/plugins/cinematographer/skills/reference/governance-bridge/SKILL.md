---
name: governance-bridge
user-invocable: false
type: reference
primary_owner: shared
---

# Governance Bridge

RACI matrix mapping cinematographer agents to pipeline-expert approval
authority. Defines who is Responsible, Accountable, Consulted, and Informed
for each artifact type across the two plugin boundaries.

---

## Principle

No cinematographer artifact ships to production without approval from the
accountable pipeline-expert agent. The cinematographer plugin produces;
the pipeline-expert plugin governs. This separation ensures that creative
execution is validated against the project's artistic standards by agents
with the authority and context to judge.

---

## RACI Matrix

| Artifact | Responsible (Cinematographer) | Accountable (Pipeline-Expert) | Consulted | Informed |
|----------|-------------------------------|-------------------------------|-----------|----------|
| Shot breakdown / storyboard | storyboarder | Auteur | dp | production-designer, colorist |
| Visual bible | production-designer | Auteur + Sculptor | dp, colorist | storyboarder |
| Lighting rigs | dp | Auteur | production-designer | colorist, groundtruth |
| OCIO / LUT config | colorist | Tonalist | dp | production-designer |
| Physical validation | groundtruth | Spectralist | dp | storyboarder |
| Camera paths / temporal | storyboarder + dp | Choreographer | production-designer | colorist |
| Material presets | production-designer | Sculptor | dp | colorist, groundtruth |
| Rendered frames | dp | Auteur + Alchemist | colorist, groundtruth | storyboarder |

---

## Cross-Plugin Request Format

When a cinematographer agent needs pipeline-expert approval, it produces
a `cross_plugin_request` collaboration YAML per the output-schemas skill:

```yaml
cross_plugin_request:
  version: "1.0"
  requesting_agent: "dp"
  target_plugin: "pipeline-expert"
  target_agent: "Auteur"
  request_type: "approve"
  context:
    tier: "preview"
    artifact_path: "output/lighting/preview_rig_v2.yaml"
    brief: "Preview-tier lighting rig for sequence SQ010. Key light motivated
            by late-afternoon sun (5200K). Requesting creative direction approval
            before rendering."
  payload:
    storyboard_ref: "output/storyboard/SQ010_v3.yaml"
    visual_bible_ref: "output/bible/oco_viz_bible_v2.yaml"
  audit_trail: "dp -> lighting_rig_delivery v1.0 -> governance-bridge -> Auteur approval"
```

---

## Approval Flow

1. **Cinematographer agent** completes EXECUTE and VALIDATE phases (per phase-template)
2. **Cinematographer agent** produces collaboration YAML with `status: pending_approval`
3. **Cinematographer agent** produces cross_plugin_request targeting the accountable pipeline-expert agent
4. **Pipeline-expert agent** reviews artifact against its standards and skills
5. **Pipeline-expert agent** returns verdict per its verdict-protocol
6. If **PASS**: cinematographer agent updates collaboration YAML to `status: ready`
7. If **FAIL**: cinematographer agent updates collaboration YAML to `status: blocked` with failure details

---

## Escalation

When the accountable pipeline-expert agent and the responsible cinematographer
agent disagree:

1. The disagreement is documented in both agents' audit trails
2. The pipeline-expert verdict takes precedence (accountable overrides responsible)
3. The cinematographer agent must revise and resubmit
4. After two rejected resubmissions, escalate to the Auteur for creative direction reset

---

## Anti-Patterns

- **Self-governance**: A cinematographer agent approving its own artifact for production. Responsible agents cannot be their own accountable authority.
- **Skipped consultation**: Proceeding to approval without consulting listed agents. The "Consulted" column exists for a reason.
- **Direct delivery**: Sending artifacts directly to production without governance approval. All production artifacts route through the RACI chain.
- **Approval shopping**: Seeking approval from a different pipeline-expert agent after being rejected by the accountable one. The RACI matrix is binding.
- **Missing cross-plugin request**: Producing an artifact and assuming it is approved. No cross_plugin_request means no approval was sought.

---

## Validation Checklist

- [ ] Correct accountable pipeline-expert agent identified from RACI matrix
- [ ] cross_plugin_request produced with all required fields
- [ ] Consulted agents have been included in the review loop
- [ ] Informed agents have received notification of the delivery
- [ ] Approval status reflected in collaboration YAML (pending_approval|ready|blocked)
- [ ] Audit trail documents the complete governance chain
