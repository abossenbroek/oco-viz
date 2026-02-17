---
name: wrap
description: Print full pipeline sequence with expected inputs/outputs per stage
user-invocable: true
---

# Wrap Command

Documentation command. Prints the recommended execution sequence with
collaboration YAML flow diagram and expected payload fields per handoff.
Does NOT execute all stages (context exhaustion risk).

## Usage

```
/cinematographer:wrap [--tier scout|preview|final]
```

## Arguments

- `--tier`: Quality tier to show pipeline for (default: preview)

## Agent Flow

1. Load the dp agent from `.claude/plugins/cinematographer/agents/dp.md`
2. dp prints the full pipeline sequence (documentation only, no execution)

## Pipeline Sequence

```
Stage 1: /cinematographer:storyboard
  Agent: storyboarder
  Output: storyboard_delivery YAML
  Payload: creative_brief, shots[], emotional_arc, timing_map

Stage 2: /cinematographer:lookdev
  Agents: production-designer → dp → colorist
  Output chain:
    visual_bible_delivery → lighting_rig_delivery → grading_delivery
  Payload: keyframes, materials, lighting, OCIO, LUT

Stage 3: /cinematographer:shoot
  Agent: dp
  Input: storyboard_delivery + lookdev outputs
  Output: shot_execution_delivery YAML
  Payload: shot_id, frames[], render_stats

Stage 4: /cinematographer:grade
  Agent: colorist
  Input: lighting_rig_delivery or shot_execution_delivery
  Output: grading_delivery YAML
  Payload: show_lut_spec, film_emulation

Stage 5: /cinematographer:dailies
  Agent: dp
  Input: shot_execution_delivery (multiple)
  Output: dailies_delivery YAML
  Payload: sequence review, per-shot notes

Cross-plugin handoffs:
  → /pipeline-expert:consult — governance approval
  → /critical-eye:review — visual QA
  → /wave-runner:gate — quality gates
```

## Collaboration YAML Flow

Each stage produces collaboration YAML that the next stage consumes.
The `next_action` field in each YAML suggests the recommended next command.
No stage loads another stage's full context — only the structured YAML.

## Examples

```
/cinematographer:wrap
/cinematographer:wrap --tier scout
/cinematographer:wrap --tier final
```

$ARGUMENTS parsed as optional `--tier` flag.
