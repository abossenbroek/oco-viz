---
name: verdict-protocol
user-invocable: false
---

# Verdict Protocol

Standard verdict structure for all pipeline-expert agents. Governs how
technical and artistic assessments combine into final verdicts.

---

## Technical Verdict

Three-tier blocking protocol applied to every stage review.

| Verdict | Meaning | Blocking? |
|---------|---------|-----------|
| **PASS** | Meets all criteria for the current stage and tier. No issues. | No |
| **CONCERN** | Meets minimum criteria but has issues that should be addressed. | No |
| **FAIL** | Does not meet minimum criteria. Must fix before proceeding. | **Yes** |

A single FAIL in any category makes the overall technical verdict FAIL.

---

## Artistic Verdict Scale

Five-level quality assessment extending critical-eye's 0-10 scoring.

| Verdict | Score Range | Meaning |
|---------|-----------|---------|
| **exceptional** | 9-10 | Gallery-ready. Anchors a major exhibition. |
| **strong** | 7-8 | Achieves intent with genuine artistic conviction. |
| **developing** | 5-6 | Direction right, execution needs deepening. |
| **weak** | 3-4 | Conceptual problems undermine intent. |
| **failed** | 1-2 | Does not serve the artistic vision. |

---

## Verdict Synthesis Rules

How technical and artistic verdicts combine into a final verdict:

1. **Technical FAIL** -> overall **FAIL** regardless of artistic score
2. **Technical PASS + artistic "weak" or "failed"** -> overall **CONCERN**
3. **Technical PASS + artistic "developing" or better** -> overall **PASS**
4. **Disagreement between agents** -> take the most conservative verdict and document the disagreement explicitly

When multiple agents review the same artifact, the most conservative
individual verdict determines the combined result.

---

## Confidence Levels

Quantified certainty attached to every verdict.

| Range | Level | When to use |
|-------|-------|-------------|
| 0.0 - 0.3 | Low | Preliminary assessment, limited evidence |
| 0.3 - 0.6 | Medium | Reasonable evidence, some uncertainty remains |
| 0.6 - 0.8 | High | Strong evidence, minor gaps acknowledged |
| 0.8 - 1.0 | Very High | Comprehensive assessment, high certainty |

A confidence below 0.3 on any finding MUST be flagged as provisional.
Verdicts with overall confidence below 0.5 SHOULD request a second review.

---

## Audit Trail

Every verdict MUST include a traceable path from data source to conclusion:

```
data source -> observation -> interpretation -> verdict
```

Example:
```
ERA5 wind field (10m, 2024-03-15T14:00Z)
  -> peak velocity 12.3 m/s at grid (45, 62)
  -> exceeds plume coherence threshold for exhibition tier
  -> CONCERN: wind shear may compromise volume stability
```
