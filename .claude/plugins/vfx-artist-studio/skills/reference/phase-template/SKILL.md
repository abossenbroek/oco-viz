---
name: phase-template
user-invocable: false
type: reference
primary_owner: shared
---

# Phase Template

Standard four-phase execution pattern for all vfx-artist-studio agents.
Every agent follows this sequence regardless of its domain specialization.
This template is adapted for pull-based PRODUCTION context where agents
discover work assignments from shot context YAML, load domain knowledge
from the knowledge/ directory, and produce tier-aware artifacts.

---

## CONTEXT

Load relevant skills, knowledge files, schemas, and check shot context
for current assignment.

- **Pull assignment**: Read `output/shots/{shot_id}/shot_context.yaml` and verify
  `active_agent` matches this agent's identity and `status` is `wip`
- Load this agent's exclusive skills (from its `exclusive_skills` list only)
- Load collaboration-protocol schema for incoming/outgoing handoffs
- Load relevant knowledge files from `knowledge/` directory:
  - **effects-td**: `houdini-fx-playbook.yaml`, `asset-naming-conventions.yaml`
  - **houdini-td**: `karma-render-profiles.yaml`, `houdini-fx-playbook.yaml`, `asset-naming-conventions.yaml`
  - **compositor**: `compositing-standards.yaml`, `exhibition-delivery-spec.yaml`, `asset-naming-conventions.yaml`
  - **matte-artist**: `exhibition-delivery-spec.yaml`, `asset-naming-conventions.yaml`
  - **vfx-supe**: `exhibition-delivery-spec.yaml`, `tier-handoff-matrix.yaml`
  - **line-producer**: `tier-handoff-matrix.yaml`, `asset-naming-conventions.yaml`
- If this agent is downstream, read the upstream collaboration YAML delivery
- Identify which output schema applies (from `reference/output-schemas`)
- Identify the tier standard (scout/preview/final) from shot context
- Load any cross-plugin dependencies:
  - **From cinematographer**: storyboard_delivery, lighting_rig_delivery, grading_delivery
  - **From pipeline-expert**: governance approvals, creative direction verdicts
  - **From critical-eye**: exhibition review verdicts
- Read `locked_params` from shot context — these parameters are immutable

**Selective loading only.** Never load skills belonging to another agent's
exclusive set. Never load knowledge files outside this agent's listed set
unless explicitly referenced in an upstream collaboration YAML.

**Assignment verification.** If `shot_context.yaml` does not exist, has
`active_agent` set to a different agent, or has `status` other than `wip`,
STOP. Do not proceed. Produce a blocked collaboration YAML explaining
what is missing.

**Upstream dependency.** If the required upstream collaboration YAML does not
exist or has `status: blocked`, STOP and produce a blocked collaboration YAML
explaining what is missing.

**Locked parameter respect.** Parameters listed in `locked_params` must be
used exactly as specified. An agent MUST NOT override, adjust, or deviate
from a locked parameter. Locked parameters represent human creative
direction decisions.

---

## EXECUTE

Write the artifact using loaded context, knowledge files, and upstream deliverables.

- Write the artifact to its canonical output path per `asset-naming-conventions.yaml`
- Use template-based generation: populate structured templates, do not free-form generate
- Inject provenance metadata into the artifact (creator, timestamp, tier, source data,
  knowledge files consulted)
- Follow the knowledge file specifications for this agent's toolchain:
  - **effects-td**: Recipes from `houdini-fx-playbook.yaml`, batch mode via hython
  - **houdini-td**: Render profiles from `karma-render-profiles.yaml`, HDA versions from playbook
  - **compositor**: AOV names and rules from `compositing-standards.yaml`
  - **matte-artist**: Delivery specs from `exhibition-delivery-spec.yaml`
- Apply tier-specific behavior:

  | Tier | Volume Resolution | Render Resolution | Denoiser | Detail Level |
  |------|-------------------|-------------------|----------|--------------|
  | **scout** | 128^3 | HD (1920x1080) | off | Timing/direction only |
  | **preview** | 512^3 | 2K DCI (2048x1080) | OIDN optional | Lighting/materials validation |
  | **final** | 1024^3 | 4K DCI (4096x2160) | OIDN temporal | Exhibition quality, no surprises |

- Write ONLY to the artifact directory designated for this agent's output
- Do NOT modify files outside the artifact directory
- Do NOT modify `shot_context.yaml` (only line-producer has write authority)
- Do NOT load or reference another agent's exclusive skills
- Do NOT make subjective artistic judgments outside this agent's domain
- Apply locked parameters exactly as specified — no deviation

**Template rule.** Every artifact must be reproducible from its inputs. If the
same inputs are provided twice, the same artifact must result. No hidden state.

**Batch mode rule.** All Houdini/Hython work runs in batch mode, never
interactive GUI. Scripts must be executable via `hython script.py`.

---

## VALIDATE

Self-check the artifact against quality gates, knowledge file specifications,
and tier-specific constraints.

- Run self-validation checks appropriate to this agent's domain:

  | Agent | Validation Focus |
  |-------|-----------------|
  | **effects-td** | Voxel spacing matches tier, sparse topology preserved, grid names standard |
  | **houdini-td** | Render config matches karma-render-profiles.yaml tier, batch mode, USD stage opens |
  | **compositor** | AOV names match compositing-standards.yaml, color management chain correct |
  | **matte-artist** | Background is (0,0,0), no ambient contribution, black point absolute |
  | **vfx-supe** | All finaling checks per exhibition-delivery-spec.yaml quality thresholds |
  | **line-producer** | Gate checks all passed, human approval obtained, locked params recorded |

- Self-check against golden rules:
  - Physical accuracy (meters, Kelvin, m/s)
  - Schema conformance (output-schemas)
  - Tier compliance (scout/preview/final thresholds from knowledge files)
  - Provenance completeness (audit_trail traces to source, knowledge files listed)
  - Locked parameter compliance (no deviation from locked_params)
  - Asset naming compliance (paths match asset-naming-conventions.yaml templates)
- Populate `constraints_checked` in the output collaboration YAML
- Compare artifact measurements against tier-specific thresholds:

  | Check | Scout | Preview | Final |
  |-------|-------|---------|-------|
  | Voxel spacing (m) | 0.078125 | 0.01953125 | 0.009765625 |
  | VDB resolution | 128^3 | 512^3 | 1024^3 |
  | Render resolution | 1920x1080 | 2048x1080 | 4096x2160 |
  | SPP | 64 | 256 | 512 |
  | Sparse fraction | > 0.5 | > 0.5 | > 0.5 |

- If any gate fails, prepare an error collaboration YAML with `status: blocked`
- Cross-reference tier-handoff-matrix.yaml for routing after completion
- Verify knowledge file references are valid (files exist and were actually read)

**No self-approval.** An agent cannot approve its own artifact for
production delivery. Validation confirms technical correctness; artistic
approval requires the vfx-supe (within-plugin) or critical-eye (cross-plugin)
governance chain.

**Knowledge file traceability.** Every validation check must be traceable
to a specific knowledge file entry. "I checked the render resolution" is
insufficient. "Render resolution 4096x2160 matches karma-render-profiles.yaml
final.resolution" is traceable.

---

## DELIVER

Produce the collaboration YAML delivery per the output-schemas skill.

- Select the correct schema from `reference/output-schemas`
- Populate all required fields (no empty required fields)
- Include complete `audit_trail` tracing from knowledge files and source data to artifact
- Include `knowledge_files_consulted` listing all knowledge files read during CONTEXT
- Include `next_action` directive for the downstream agent, determined by
  consulting `tier-handoff-matrix.yaml` for the current (tier, action) pair
- If validation failed, set `status: blocked` and populate `blocking_issues`
- If validation passed, set `status: ready` and specify the downstream consumer
- Write the collaboration YAML to the canonical handoff path:
  `output/shots/{shot_id}/collab/{from_agent}_to_{to_agent}_{timestamp}.yaml`
- Notify the line-producer that this agent's work is complete (the line-producer
  will update shot context YAML accordingly)

**Delivery contract.** The collaboration YAML IS the deliverable. The artifact
file is an attachment. If the collaboration YAML is malformed, the delivery
did not happen.

**Routing contract.** The `next_action` field must align with the routing
specified in `tier-handoff-matrix.yaml`. An effects-td completing at scout
tier routes to vfx-supe for visual_check, not directly to line-producer
for promotion.

**Cross-plugin delivery.** When the tier-handoff-matrix specifies a
cross-plugin destination (e.g., final tier exit routes to critical-eye),
the line-producer produces the `cross_plugin_request`. Individual agents
do not initiate cross-plugin handoffs.

---

## Tier-Specific Phase Variations

### Scout Tier

Focus: **creative direction discovery**. Speed over fidelity.

- CONTEXT: Minimal knowledge file loading. Focus on technique selection.
- EXECUTE: Low-resolution artifacts (128^3). Hython scripts for rapid iteration.
- VALIDATE: Verify timing, composition, and creative intent — not render quality.
- DELIVER: Route to vfx-supe for visual_check. Expect human creative direction feedback.

### Preview Tier

Focus: **technical validation**. Confirm lighting, materials, and effects stack.

- CONTEXT: Full knowledge file loading. Load all upstream scout-tier artifacts.
  Load locked parameters from scout tier promotion.
- EXECUTE: Mid-resolution artifacts (512^3). Full effects stack applied.
  MaterialX shaders authored. Render config per karma-render-profiles.yaml preview.
- VALIDATE: Render quality, shader quality, comp integrity checks.
  Verify all scout-locked parameters honored.
- DELIVER: Route to vfx-supe for quality assessment. Preview approval
  requires human parameter lock before final tier promotion.

### Final Tier

Focus: **exhibition delivery**. No creative surprises. Execution only.

- CONTEXT: All parameters locked. No creative decisions remain.
  Load full knowledge file set. Verify all parameters are locked in shot context.
- EXECUTE: Procedural upres to 1024^3. Exhibition-only effects
  (e.g., temporal denoising, deep compositing). All paths from
  asset-naming-conventions.yaml.
- VALIDATE: Two-percent rule finaling (vfx-supe). Exhibition-delivery-spec.yaml
  quality thresholds. Pure black void test. Temporal stability check.
- DELIVER: Route through vfx-supe finaling -> line-producer exit criteria ->
  critical-eye exhibition review. Exit only after all gates pass.

---

## Anti-Patterns

- **Skill trespassing**: Loading another agent's exclusive skills during CONTEXT phase. Each agent operates within its own skill boundary.
- **Free-form generation**: Writing artifacts without template structure. All artifacts must be template-based and reproducible.
- **Self-approval**: Marking own output as approved. Validation confirms correctness; approval is a governance function owned by vfx-supe.
- **Orphaned artifacts**: Writing an artifact file without producing the corresponding collaboration YAML delivery. The YAML is the handoff mechanism.
- **Tier mismatch**: Producing a final-tier artifact when scout-tier was requested. Always match the requested tier from shot context.
- **Silent failure**: Encountering a validation failure and proceeding anyway. Failures MUST produce blocked collaboration YAML.
- **Shot context tampering**: Any agent other than line-producer writing to shot_context.yaml. Read-only access for all other agents.
- **Knowledge file ignorance**: Producing artifacts without consulting the relevant knowledge files. Every technique has a playbook entry; use it.
- **Locked parameter override**: Changing a parameter that appears in `locked_params`. Locked parameters represent human creative decisions and are immutable.
- **Push-based routing**: An agent deciding where to send its output based on its own judgment instead of consulting tier-handoff-matrix.yaml.
- **Cross-plugin bypass**: An agent other than line-producer initiating a cross-plugin request. All cross-plugin communication flows through line-producer.
- **GUI dependency**: Writing Houdini artifacts that require interactive GUI. All work must be batch-mode hython.

---

## Validation Checklist

- [ ] CONTEXT verified `active_agent` matches this agent in shot_context.yaml
- [ ] CONTEXT verified `status` is `wip` in shot_context.yaml
- [ ] CONTEXT loaded only this agent's exclusive skills
- [ ] CONTEXT loaded relevant knowledge files from the knowledge/ directory
- [ ] CONTEXT identified the correct output schema
- [ ] CONTEXT verified upstream collaboration YAML exists and is not blocked
- [ ] CONTEXT read and recorded all locked parameters
- [ ] EXECUTE wrote artifact to canonical path per asset-naming-conventions.yaml
- [ ] EXECUTE injected provenance metadata including knowledge file references
- [ ] EXECUTE applied tier-specific settings from knowledge files
- [ ] EXECUTE honored all locked parameters without deviation
- [ ] EXECUTE used batch mode for all Houdini operations
- [ ] VALIDATE ran all applicable domain-specific checks
- [ ] VALIDATE populated constraints_checked with traceable measurements
- [ ] VALIDATE compared measurements against tier thresholds from knowledge files
- [ ] VALIDATE verified asset naming compliance
- [ ] DELIVER produced conformant collaboration YAML per output-schemas
- [ ] DELIVER included complete audit_trail with knowledge file provenance
- [ ] DELIVER included knowledge_files_consulted array
- [ ] DELIVER set correct status (ready|blocked)
- [ ] DELIVER set next_action aligned with tier-handoff-matrix.yaml routing
- [ ] DELIVER wrote collaboration YAML to canonical handoff path
