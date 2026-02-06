---
name: review-gate
description: Visual QA at a pipeline stage boundary using critical-eye analysis
user-invocable: true
---

# Review Gate Command

Visual quality assessment at a pipeline stage boundary. Uses the critical-eye
agent's image reading and analysis capabilities with stage-specific criteria
to verify that a pipeline stage's output looks correct before proceeding.

## Usage

```
/critical-eye:review-gate <stage> <image-path>
```

## Arguments

- `<stage>`: `1`, `2`, or `3` (stage number -- stage 4 uses `/critical-eye:review` instead)
- `<image-path>`: Path to the stage output visualization image

## Agent Flow

1. Load the **critical-eye** agent from `.claude/plugins/critical-eye/agents/critical-eye.md`
2. Load the **stage-gates** framework skill from
   `.claude/plugins/critical-eye/skills/stage-gates/SKILL.md`
3. Load the specific stage gate skill:
   - Stage 1: `.claude/plugins/critical-eye/skills/stage-gates/stage-1-gate/SKILL.md`
   - Stage 2: `.claude/plugins/critical-eye/skills/stage-gates/stage-2-gate/SKILL.md`
   - Stage 3: `.claude/plugins/critical-eye/skills/stage-gates/stage-3-gate/SKILL.md`
4. Read and analyze the image using the Read tool (vision capability)
5. Run `pixi run image-stats` for quantitative pixel measurements
6. Apply stage-specific visual criteria from the loaded gate skill
7. Output: verdict (PASS / CONCERN / FAIL) with observations per criterion

## Why Not Stage 4?

Stage 4 (rendering) requires the full dual-agent review architecture with
VFX TD evaluation, Art Director consultation, and independence-firewalled
artistic assessment. Use `/critical-eye:review <tier> <image-path>` for
rendered output. Stage gates are lightweight visual sanity checks for
earlier pipeline stages.

## Key Properties

- **Read-only**: No files are created or modified during review
- **Single-agent**: Uses critical-eye only (no art-director delegation)
- **Stage-specific criteria**: Each gate has its own checklist, not the full 7-category review
- **Quick verdict**: PASS / CONCERN / FAIL with specific observations

## Examples

```
/critical-eye:review-gate 1 renders/ingestion_coverage_map.png
/critical-eye:review-gate 2 renders/reconstruction_slice_z30.png
/critical-eye:review-gate 3 renders/vdb_preview_density.png
```

$ARGUMENTS parsed as `<stage>` and `<image-path>`.
