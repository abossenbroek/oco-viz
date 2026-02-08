---
description: Visual QA at a pipeline stage boundary using critical-eye analysis
argument-hint: "<stage> <image-path>"
---

Visual quality assessment at a pipeline stage boundary. Uses the critical-eye
agent's image reading and analysis capabilities with stage-specific criteria
to verify that a pipeline stage's output looks correct before proceeding.

Load the **critical-eye** agent from `.claude/plugins/critical-eye/agents/critical-eye.md`.
Load the **stage-gates** framework skill from `.claude/plugins/critical-eye/skills/stage-gates/SKILL.md`.

Load the specific stage gate skill:
- Stage 1: `.claude/plugins/critical-eye/skills/stage-gates/stage-1-gate/SKILL.md`
- Stage 2: `.claude/plugins/critical-eye/skills/stage-gates/stage-2-gate/SKILL.md`
- Stage 3: `.claude/plugins/critical-eye/skills/stage-gates/stage-3-gate/SKILL.md`

Stage 4 (rendering) requires the full dual-agent review -- use `/critical-eye:review` instead.

Key constraints:
- Read-only: no files created or modified
- Single-agent: uses critical-eye only (no art-director delegation)
- Quick verdict: PASS / CONCERN / FAIL with specific observations

$ARGUMENTS parsed as `<stage>` and `<image-path>`.
