---
name: phase-template
user-invocable: false
---

# Phase Template

Standard four-phase execution pattern for all pipeline-expert agents.
Every agent follows this sequence regardless of its domain specialization.

---

## CONTEXT

Load relevant skills, standards, and source material.

- Read tier-specific and stage-specific standards
- Load the visual language reference
- Read the source config or artifact under review
- Identify which output schema applies (render_review, creative_review, etc.)
- Load the verdict-protocol for synthesis rules

**Selective loading only.** Never load standards for tiers or stages outside
the current review scope.

---

## ANALYSIS

Independent assessment against loaded criteria.

- Evaluate each category from the relevant standard
- Record observations with specific, measurable evidence
- Score artistic categories on the 0-10 scale where applicable
- Note strengths AND concerns with equal rigor
- Cross-reference measurements against tier thresholds
- Document raw data before interpretation

**No hedging.** If something fails, say it fails. If something excels,
say it excels. Precision over diplomacy.

---

## VALIDATION

Cross-reference findings against constraints and other agents.

- Check findings against physical constraints (Spectralist domain)
- Verify artistic direction alignment (Auteur domain)
- Confirm technical feasibility (Alchemist domain)
- Flag any conflicts between agents' assessments
- Apply the verdict-protocol synthesis rules
- Ensure audit trail is traceable from data source to conclusion

**Independence firewall.** During initial analysis, agents do not see each
other's findings. Cross-referencing happens only in this phase after
independent assessments are complete.

---

## VERDICT

Produce structured output per the output-schemas skill.

- Apply verdict-protocol rules to determine technical and artistic verdicts
- Generate actionable suggestions for each concern or fail
- Document the full audit trail (data source -> interpretation -> verdict)
- Route results to the requesting command
- Flag any confidence levels below 0.3 as provisional

**Output contract.** The verdict MUST conform to exactly one of the
schemas defined in `skills/reference/output-schemas/SKILL.md`.
