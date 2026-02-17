---
description: "Promote work from one tier to the next with gate checks"
argument-hint: "<shot-id> <from-tier> <to-tier>"
---

Tier promotion orchestration with gate verification and agent delegation.

## Agent

Load line-producer from `.claude/plugins/vfx-artist-studio/agents/line-producer.md`.

## Skills

Agent loads production skills from `.claude/plugins/vfx-artist-studio/skills/production/`.

## Output

Gate check results, tier changes, delegated tasks, or blocking reasons.

$ARGUMENTS: `<shot-id>`, `<from-tier>` (scout|preview), `<to-tier>` (preview|final).
