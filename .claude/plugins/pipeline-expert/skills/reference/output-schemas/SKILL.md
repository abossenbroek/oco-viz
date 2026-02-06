---
name: output-schemas
user-invocable: false
---

# Output Schemas

Canonical YAML output contracts used by all pipeline-expert agents. Every agent
MUST produce output conforming to the schema matching its review type.

---

## render_review

Produced by any agent performing a stage-level technical review.

```yaml
render_review:
  stage: string          # ingestion|reconstruction|conversion|rendering|exhibition
  agent: string          # primary reviewing agent
  timestamp: ISO8601
  findings:
    - category: string
      status: pass|concern|fail
      observation: string
      evidence: string   # specific measurement or reference
      suggestion: string # actionable fix (optional)
  verdict: pass|concern|fail
  artistic_verdict: exceptional|strong|developing|weak|failed
  confidence: float      # 0.0-1.0
  audit_trail: string    # traces decision back to data source
```

---

## creative_review

Produced by the Auteur or any agent evaluating artistic merit.

```yaml
creative_review:
  intent: string         # original creative direction
  agent: string
  timestamp: ISO8601
  assessment:
    emotional_register: {score: int, note: string}
    material_presence: {score: int, note: string}
    compositional_authority: {score: int, note: string}
    chromatic_discipline: {score: int, note: string}
    void_quality: {score: int, note: string}
    narrative_potency: {score: int, note: string}
    sublime_register: {score: int, note: string}
  verdict: exceptional|strong|developing|weak|failed
  direction_notes: [string]
  gallery_positioning: string
```

**Differences from critical-eye's artistic evaluation:**
- Adds `narrative_potency` — does the image tell the story of industrial emission?
- Adds `sublime_register` — does the image achieve the Kantian sublime (awe + dread)?

---

## ideation_result

Produced by the Ideation Protocol (multi-model creative generation).

```yaml
ideation_result:
  intent: string
  ground_truth:          # Phase 1 (Claude)
    data_analysis: string
    technical_canvas: string
  provocations:          # Phase 2 (Gemini)
    - thesis: string
      rationale: string
      risk: string
  synthesis:             # Phase 3 (Auteur)
    directors_brief: string
    sculptor_directive: string
    tonalist_directive: string
    choreographer_directive: string
  execution_plan:        # Phase 4
    parameters: {key: value}
    code_snippets: [string]
```

---

## audit_report

Produced by cross-stage pipeline audits.

```yaml
audit_report:
  timestamp: ISO8601
  stages_reviewed: [string]
  per_stage:
    - stage: string
      primary_agent: string
      findings: [finding]
      verdict: pass|concern|fail
  cross_stage_issues: [string]
  conceptual_audit_trail: string
  overall_verdict: pass|concern|fail
  recommendations: [string]
```

---

## Usage

Agents select the schema matching their output type:
- Stage review (Spectralist, Alchemist, etc.) -> `render_review`
- Creative evaluation (Auteur, Tonalist) -> `creative_review`
- Ideation sessions -> `ideation_result`
- Full pipeline audits -> `audit_report`
