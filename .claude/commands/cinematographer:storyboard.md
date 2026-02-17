---
description: Generate shot sequence with emotional arc, camera grammar, palettes
argument-hint: "\"creative brief or scene description\""
---

Generate a shot sequence with emotional arc, camera grammar, and palette
assignments from a creative brief using the storyboarder agent.

## Agent

Load storyboarder from `.claude/plugins/cinematographer/agents/storyboarder.md`.

## Skills

Agent loads: `shot-grammar`, `sequence-design`, `color-palette` from
`.claude/plugins/cinematographer/skills/`.

## Output

Collaboration YAML with `storyboard_delivery` payload (shots, emotional arc, timing map).
Next action suggests `/cinematographer:lookdev` or `/cinematographer:shoot`.

$ARGUMENTS parsed as creative brief string.
