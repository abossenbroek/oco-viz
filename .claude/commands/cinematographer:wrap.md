---
description: Print full pipeline sequence with expected inputs/outputs per stage
argument-hint: "[--tier scout|preview|final]"
---

Documentation command. Prints the recommended cinematographer execution
sequence with collaboration YAML flow and expected payload fields per handoff.
Does NOT execute all stages.

## Agent

Load dp from `.claude/plugins/cinematographer/agents/dp.md`.

## Pipeline

1. `/cinematographer:storyboard` → `storyboard_delivery`
2. `/cinematographer:lookdev` → `visual_bible_delivery` → `lighting_rig_delivery` → `grading_delivery`
3. `/cinematographer:shoot` → `shot_execution_delivery`
4. `/cinematographer:grade` → `grading_delivery`
5. `/cinematographer:dailies` → `dailies_delivery`

Cross-plugin: `→ /pipeline-expert:consult` | `→ /critical-eye:review` | `→ /wave-runner:gate`

$ARGUMENTS parsed as optional `--tier` flag.
