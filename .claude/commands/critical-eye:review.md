---
description: Full two-agent visual quality review (VFX TD + Art Director)
argument-hint: "<tier> <path-or-glob> [--sequence]"
---

Run a full two-agent visual quality review on rendered image(s). Delegates to the critical-eye agent (VFX TD) which conducts its own technical assessment, then delegates to the art-director agent for an independent artistic evaluation, and synthesizes both into a final `review_report`.

Load the critical-eye agent from `.claude/plugins/critical-eye/agents/critical-eye.md`.
Use the visual-language skill from `.claude/plugins/critical-eye/skills/visual-language/SKILL.md`.

The critical-eye agent selectively loads the tier standard:
- Exhibition: `.claude/plugins/critical-eye/skills/standards/exhibition.md`
- Study: `.claude/plugins/critical-eye/skills/standards/study.md`
- Sketch: `.claude/plugins/critical-eye/skills/standards/sketch.md`

If `--sequence` is present, also load `.claude/plugins/critical-eye/skills/standards/sequence.md`.

After VFX evaluation, the critical-eye agent delegates to the art-director agent (`.claude/plugins/critical-eye/agents/art-director.md`) with an independence-firewalled request containing only images, tier, and config snapshot — no VFX findings.

The art-director agent loads its own skills:
- `.claude/plugins/critical-eye/skills/tier-personas/SKILL.md`
- `.claude/plugins/critical-eye/skills/artistic-evaluation/SKILL.md`
- `.claude/plugins/critical-eye/skills/gallery-context/SKILL.md`

Key constraints:
- Read-only: no files created or modified during review
- Independence firewall: art director never sees VFX findings
- Tier isolation: only one tier standard loaded per review

$ARGUMENTS passed through to critical-eye agent.
