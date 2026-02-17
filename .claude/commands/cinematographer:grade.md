---
description: Color grading session — show LUT creation, OCIO config, achromatic validation
argument-hint: "<shot-id|sequence-id> [--mode create-lut|apply|verify]"
---

Color grading session. The colorist agent produces OCIO configuration,
show LUT, CDL values, and achromatic compliance data.

## Agent

Load colorist from `.claude/plugins/cinematographer/agents/colorist.md`.

## Skills

Agent loads: `fraser-shift`, `aces-ocio`, `show-lut`, `skip-bleach`
from `.claude/plugins/cinematographer/skills/`.

## Output

Collaboration YAML with `grading_delivery` payload (OCIO config, CDL, achromatic compliance).
Next action suggests `/pipeline-expert:consult tonalist` for achromatic review.

$ARGUMENTS parsed as `<shot-id|sequence-id>` and optional `--mode` flag.
