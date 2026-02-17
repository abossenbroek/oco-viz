---
description: "Plan next sprint/wave with human+agent task allocation"
argument-hint: "<wave|sprint> [--agents <list>]"
---

Sprint/wave planning with human vs agent task allocation.

## Agent

Load line-producer from `.claude/plugins/vfx-artist-studio/agents/line-producer.md`.

## Skills

Agent loads production skills from `.claude/plugins/vfx-artist-studio/skills/production/`.

## Output

Sprint plan with explicit human decisions and agent tasks, each with assignee,
description, exit criteria, and dependencies.

$ARGUMENTS parsed as `wave` or `sprint` scope, with optional `--agents` filter.
