---
description: "Plan next sprint/wave with human+agent task allocation"
argument-hint: "<wave|sprint> [--agents <list>]"
---

Sprint/wave planning with explicit human vs agent task allocation. The line-producer
reads current wave tickets, agent capabilities, and dependencies to produce a plan.

## Agent

Load line-producer from `.claude/plugins/vfx-artist-studio/agents/line-producer.md`.

## Skills

Agent loads: `production-protocol`, `task-scoping`, `human-agent-boundary`,
`cross-plugin-coordination`
from `.claude/plugins/vfx-artist-studio/skills/`.

## Procedure

1. Read current wave tickets from `plan/tickets/`
2. Identify dependencies and ordering constraints
3. Scope each task: single agent, clear exit criteria, < 1 context window
4. Classify each task as human decision or agent execution
5. Allocate agent tasks to specific agents based on domain boundaries
6. Estimate velocity and identify potential blockers
7. Produce sprint plan with explicit allocation

## Output

Sprint plan with entries like:
- "Human: approve creative direction for Shot 03 void quality"
- "Agent (effects-td): implement Paper Grain Manifold wedge for sc010"
- "Agent (houdini-td): write Karma XPU render config for preview tier"
- "Human: review contact sheet, lock grain_amplitude"
- "Agent (compositor): define AOV specification for sc010 preview"

Each entry includes: assignee, task description, exit criteria, estimated scope, dependencies.

$ARGUMENTS parsed as `wave` or `sprint` scope, with optional `--agents` filter.
