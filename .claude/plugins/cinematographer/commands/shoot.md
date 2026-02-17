---
name: shoot
description: Execute single shot through pipeline with lighting and render config
user-invocable: true
---

# Shoot Command

Execute a single shot through the rendering pipeline. The dp agent reads
upstream collaboration YAML and produces lighting configuration, render
scripts, and camera setup for the specified shot.

## Usage

```
/cinematographer:shoot <shot-id> [--tier scout|preview|final]
```

## Arguments

- `<shot-id>`: Identifier for the shot to execute (from storyboard or lookdev)
- `--tier`: Quality tier (default: preview). Controls resolution, samples, and validation.

## Agent Flow

1. Load the dp agent from `.claude/plugins/cinematographer/agents/dp.md`
2. dp loads exclusive skills: `deakins-method`, `practical-first`, `review-in-the-cut`, `lighting-setups`
3. dp reads upstream collaboration YAML:
   - `storyboard_delivery` — for shot specs, timing, emotional beat
   - `visual_bible_delivery` — for material presets, spatial config
   - `lighting_rig_delivery` — if lookdev was already run
4. dp analyzes VDB data, creates lighting rig, writes render config
5. dp produces `shot_execution_delivery` collaboration YAML

## Output

Collaboration YAML with `shot_execution_delivery` payload:
- `shot_id` — the executed shot identifier
- `frames` — rendered frame paths with render times
- `render_stats` — total time, peak memory, samples per pixel

## Next Action

The collaboration YAML suggests:
- `/critical-eye:review` — for independent visual QA
- `/cinematographer:grade` — for color grading

## Examples

```
/cinematographer:shoot shot_001 --tier scout
/cinematographer:shoot opening_sequence_01 --tier preview
/cinematographer:shoot hero_frame --tier final
```

$ARGUMENTS parsed as `<shot-id>` and optional `--tier` flag.
