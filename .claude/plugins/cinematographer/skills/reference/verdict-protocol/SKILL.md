---
name: verdict-protocol
user-invocable: false
type: reference
primary_owner: shared
---

# Verdict Protocol

Standard verdict structure for all cinematographer agents. Governs how
technical and artistic assessments combine into final production verdicts.
Adapted from pipeline-expert's verdict-protocol for production (not review)
context.

---

## Technical Verdict

Three-tier blocking protocol applied to every artifact validation.

| Verdict | Meaning | Blocking? |
|---------|---------|-----------|
| **PASS** | Artifact meets all criteria for the requested tier. No issues. | No |
| **CONCERN** | Meets minimum criteria but has issues that should be addressed before final delivery. | No |
| **FAIL** | Does not meet minimum criteria. Must fix before proceeding to downstream agents. | **Yes** |

A single FAIL in any category makes the overall technical verdict FAIL.

---

## Artistic Verdict Scale

Five-level quality assessment for creative output.

| Verdict | Score Range | Meaning |
|---------|-------------|---------|
| **exceptional** | 9-10 | Exhibition-ready. Anchors a major gallery show. No notes. |
| **strong** | 7-8 | Achieves creative intent with genuine conviction. Minor refinements possible. |
| **developing** | 5-6 | Direction correct, execution needs deepening or polish. |
| **weak** | 3-4 | Conceptual or execution problems undermine the intent. |
| **failed** | 1-2 | Does not serve the artistic vision. Fundamental rethink required. |

---

## Constraint Verification

All golden rules MUST pass before any verdict is issued. These are
non-negotiable physical and technical constraints.

| Constraint | Rule | Verification |
|------------|------|-------------|
| Length units | Meters (real-world scale) | Grid extent matches expected physical size |
| Temperature | Kelvin (293-3000K) | Temperature grid values in valid range |
| Voxel spacing | world_size / resolution | Spacing matches declared resolution |
| Grid names | "density", "vel", "temperature" | OpenVDB grid name inspection |
| Sparse design | Exact 0.0 where empty | Non-zero voxel count vs total volume |
| ACES pipeline | ACEScg working space | OCIO config verification |
| Achromatic compliance | Neutral gray maps to neutral gray | CDL neutral test |

A constraint violation is an automatic FAIL regardless of artistic quality.

---

## Verdict Synthesis Rules

How technical and artistic verdicts combine:

1. **Constraint violation** -> overall **FAIL** regardless of everything else
2. **Technical FAIL** -> overall **FAIL** regardless of artistic score
3. **Technical PASS + artistic "weak" or "failed"** -> overall **CONCERN** with mandatory revision
4. **Technical PASS + artistic "developing" or better** -> overall **PASS**
5. **Technical CONCERN + artistic "strong" or better** -> overall **PASS** with noted concerns
6. **Disagreement between agents** -> take the most conservative verdict and document the disagreement explicitly

When multiple agents evaluate the same artifact, the most conservative
individual verdict determines the combined result.

---

## Confidence Levels

Quantified certainty attached to every verdict.

| Range | Level | When to use |
|-------|-------|-------------|
| 0.0 - 0.3 | Low | Preliminary assessment, limited evidence, incomplete artifact |
| 0.3 - 0.6 | Medium | Reasonable evidence, some uncertainty remains |
| 0.6 - 0.8 | High | Strong evidence from multiple checks, minor gaps acknowledged |
| 0.8 - 1.0 | Very High | Comprehensive assessment, all checks passed, high certainty |

A confidence below 0.3 on any finding MUST be flagged as provisional.
Verdicts with overall confidence below 0.5 SHOULD request a second review
or additional evidence before blocking downstream work.

---

## Audit Trail

Every verdict MUST include a traceable path from source to conclusion:

```
source artifact -> measurement -> interpretation -> verdict
```

Example:
```
lighting_rig_delivery v1.0 (dp, 2026-02-15)
  -> key light color_temp 5600K, intensity 850 nits
  -> matches daylight reference, sufficient for preview tier
  -> PASS: lighting meets preview-tier motivated-light requirement
```

Example (failure):
```
grading_delivery v1.0 (colorist, 2026-02-15)
  -> CDL slope [1.2, 0.9, 0.8] applied to neutral gray patch
  -> output measured [0.48, 0.36, 0.32] — NOT neutral
  -> FAIL: achromatic compliance violated, CDL introduces color cast on neutrals
```

---

## Anti-Patterns

- **Verdict inflation**: Marking "strong" when execution is clearly "developing". Precision over diplomacy.
- **Hedged fails**: Writing "this might be a concern" when measurement clearly shows a FAIL. If it fails, say it fails.
- **Missing constraint check**: Issuing a PASS verdict without verifying all golden rule constraints. Constraints are non-negotiable.
- **Orphaned verdicts**: Producing a verdict without an audit trail. Every verdict must trace to evidence.
- **Cross-domain overreach**: A colorist issuing lighting verdicts, or a storyboarder judging physical accuracy. Each agent judges within its domain only.

---

## Validation Checklist

- [ ] All golden rule constraints verified before verdict issued
- [ ] Technical verdict is one of: PASS, CONCERN, FAIL
- [ ] Artistic verdict is one of: exceptional, strong, developing, weak, failed
- [ ] Synthesis rules correctly applied to produce overall verdict
- [ ] Confidence level assigned and justified
- [ ] Audit trail traces from source artifact to conclusion
- [ ] Provisional findings (confidence < 0.3) explicitly flagged
- [ ] Disagreements between agents documented if applicable
