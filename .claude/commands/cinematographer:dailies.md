---
description: Review in the cut — sequence review with critical-eye delegation
argument-hint: "<shot-ids|sequence-id>"
---

Review in the cut — the dp agent reviews shots in sequence context, applying
Nelson's principle of never evaluating a shot in isolation.

## Agent

Load dp from `.claude/plugins/cinematographer/agents/dp.md`.

## Skills

Agent loads: `review-in-the-cut` (primary) plus standard dp skills
from `.claude/plugins/cinematographer/skills/`.

## Output

Collaboration YAML with `dailies_delivery` payload (sequence review, per-shot notes).
Next action suggests `/critical-eye:review` for independent assessment.

$ARGUMENTS parsed as shot IDs or sequence identifier.
