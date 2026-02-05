---
description: Full two-agent visual quality review (VFX TD + Art Director)
argument-hint: "<tier> <path-or-glob> [--sequence]"
---

Run a full two-agent visual quality review on rendered image(s). Delegates to the critical-eye agent (VFX TD) which conducts its own technical assessment, then delegates to the art-director agent for an independent artistic evaluation, and synthesizes both into a final `review_report`.

## Usage

```
/critical-eye:review exhibition output/examples/wave5/tier_exhibition_soot.png
/critical-eye:review study output/examples/wave5/tier_study_*.png
/critical-eye:review exhibition output/examples/wave5/easing_*.png --sequence
```

## Arguments

- `<tier>`: One of `exhibition`, `study`, `sketch` — determines which standard and persona to use
- `<path-or-glob>`: Image file path or glob pattern matching one or more PNG files
- `--sequence`: (optional) Enable temporal coherence evaluation across multiple frames

## Agent Flow

1. Load the **critical-eye** agent from `.claude/plugins/critical-eye/agents/critical-eye.md`
2. Use the **visual-language** skill from `.claude/plugins/critical-eye/skills/visual-language/SKILL.md`
3. The critical-eye agent selectively loads the tier standard:
   - Exhibition: `.claude/plugins/critical-eye/skills/standards/exhibition.md`
   - Study: `.claude/plugins/critical-eye/skills/standards/study.md`
   - Sketch: `.claude/plugins/critical-eye/skills/standards/sketch.md`
4. If `--sequence`: also loads `.claude/plugins/critical-eye/skills/standards/sequence.md`
5. After VFX evaluation, the critical-eye agent delegates to the **art-director** agent with an independence-firewalled request
6. Final output: `review_report` YAML with VFX findings, artistic review, and synthesis

## Key Properties

- **Read-only**: No files are created or modified during review
- **Independence firewall**: Art director never sees VFX findings
- **Tier isolation**: Only one tier standard is loaded per review
- **Quantitative backing**: Pixel analysis via coordinator-internal recipes

$ARGUMENTS passed through to critical-eye agent.
