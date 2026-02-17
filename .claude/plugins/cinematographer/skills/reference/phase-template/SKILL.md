---
name: phase-template
user-invocable: false
type: reference
primary_owner: shared
---

# Phase Template

Standard four-phase execution pattern for all cinematographer agents.
Every agent follows this sequence regardless of its domain specialization.
This template is adapted for PRODUCTION context (artifact creation),
not review context.

---

## CONTEXT

Load relevant skills, schemas, and upstream deliverables.

- Load this agent's exclusive skills (from its `exclusive_skills` list only)
- Load collaboration-protocol schema for incoming/outgoing handoffs
- If this agent is downstream, read the upstream collaboration YAML delivery
- Identify which output schema applies (from `reference/output-schemas`)
- Load governance-bridge to identify approval authority
- Identify the tier standard (scout/preview/final) for quality thresholds
- Load any cross-plugin dependencies via cross_plugin_request format

**Selective loading only.** Never load skills belonging to another agent's
exclusive set. Never load standards for tiers outside the current scope.

**Upstream dependency.** If the required upstream collaboration YAML does not
exist or has `status: blocked`, STOP and produce a blocked collaboration YAML
explaining what is missing.

---

## EXECUTE

Write the artifact using loaded context and upstream deliverables.

- Write the artifact to its canonical output path
- Use template-based generation: populate structured templates, do not free-form generate
- Inject provenance metadata into the artifact (creator, timestamp, tier, source data)
- Follow the tech-stack specification for this agent's toolchain
- Write ONLY to the artifact directory designated for this agent's output
- Do NOT modify files outside the artifact directory
- Do NOT load or reference another agent's exclusive skills
- Do NOT make subjective artistic judgments outside this agent's domain

**Template rule.** Every artifact must be reproducible from its inputs. If the
same inputs are provided twice, the same artifact must result. No hidden state.

---

## VALIDATE

Self-check the artifact against quality gates and constraints.

- Run quality gates (reference/quality-gates) applicable to this artifact type
- Self-check against golden rules:
  - Physical accuracy (meters, Kelvin, m/s)
  - Schema conformance (output-schemas)
  - Tier compliance (scout/preview/final thresholds)
  - Provenance completeness (audit_trail traces to source)
- Populate `constraints_checked` in the output collaboration YAML
- Compare artifact measurements against tier standard thresholds
- If any gate fails, prepare an error collaboration YAML with `status: blocked`
- Cross-reference governance-bridge for required approvals

**No self-approval.** An agent cannot approve its own artifact for
production delivery. Validation confirms technical correctness; artistic
approval requires the governance chain.

---

## DELIVER

Produce the collaboration YAML delivery per the output-schemas skill.

- Select the correct schema from `reference/output-schemas`
- Populate all required fields (no empty required fields)
- Include complete `audit_trail` tracing from source data to artifact
- Include `next_action` directive for the downstream agent
- If validation failed, set `status: blocked` and populate `blocking_issues`
- If validation passed, set `status: ready` and specify the downstream consumer
- Write the collaboration YAML to the canonical handoff path

**Delivery contract.** The collaboration YAML IS the deliverable. The artifact
file is an attachment. If the collaboration YAML is malformed, the delivery
did not happen.

---

## Anti-Patterns

- **Skill trespassing**: Loading another agent's exclusive skills during CONTEXT phase. Each agent operates within its own skill boundary.
- **Free-form generation**: Writing artifacts without template structure. All artifacts must be template-based and reproducible.
- **Self-approval**: Marking own output as approved. Validation confirms correctness; approval is a governance function.
- **Orphaned artifacts**: Writing an artifact file without producing the corresponding collaboration YAML delivery. The YAML is the handoff mechanism.
- **Tier mismatch**: Producing a final-tier artifact when scout-tier was requested. Always match the requested tier.
- **Silent failure**: Encountering a validation failure and proceeding anyway. Failures MUST produce blocked collaboration YAML.

---

## Validation Checklist

- [ ] CONTEXT loaded only this agent's exclusive skills
- [ ] CONTEXT identified the correct output schema
- [ ] CONTEXT verified upstream collaboration YAML exists and is not blocked
- [ ] EXECUTE wrote artifact to canonical path only
- [ ] EXECUTE injected provenance metadata
- [ ] VALIDATE ran all applicable quality gates
- [ ] VALIDATE populated constraints_checked
- [ ] DELIVER produced conformant collaboration YAML
- [ ] DELIVER included complete audit_trail
- [ ] DELIVER set correct status (ready|blocked)
