---
description: Execute single shot through pipeline with lighting and render config
argument-hint: "<shot-id> [--tier scout|preview|final]"
---

Execute a single shot through the rendering pipeline. The dp agent reads
upstream collaboration YAML and produces lighting, render, and camera configs.

## Agent

Load dp from `.claude/plugins/cinematographer/agents/dp.md`.

## Skills

Agent loads: `deakins-method`, `practical-first`, `review-in-the-cut`, `lighting-setups`
from `.claude/plugins/cinematographer/skills/`.

## Output

Collaboration YAML with `shot_execution_delivery` payload (frames, render stats).
Next action suggests `/critical-eye:review` for visual QA.

$ARGUMENTS parsed as `<shot-id>` and optional `--tier` flag.
