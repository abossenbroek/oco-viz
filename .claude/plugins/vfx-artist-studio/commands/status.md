---
description: "Production status: velocity, debt, tier progression, blockers, next actions"
argument-hint: "[--wave <n>] [--shot <id>]"
---

Production status report. The line-producer reads all ticket YAMLs, wave progress,
git log velocity, and gallery state to produce a structured report.

## Agent

Load line-producer from `.claude/plugins/vfx-artist-studio/agents/line-producer.md`.

## Skills

Agent loads: `production-protocol`, `task-scoping`, `rescoping-triggers`,
`cross-plugin-coordination`, `human-agent-boundary`
from `.claude/plugins/vfx-artist-studio/skills/`.

## Procedure

1. Read ticket YAMLs from `plan/tickets/` — count done/total per wave
2. Check git log for recent velocity (commits/week, tickets closed/week)
3. Check re-scoping trigger thresholds (velocity collapse, phase overrun, regression loop, CI red streak)
4. Inventory debt: gate debt, visual debt, pipeline debt, deferred scope
5. Read shot context YAMLs from `output/shots/*/shot_context.yaml` for tier progression state
6. Identify cross-plugin blockers
7. Suggest next human decisions needed

## Output

Structured status report with sections:
- **Velocity**: tickets done/total, velocity trend, on-track assessment
- **Debt Inventory**: counts per category with top items
- **Tier Progression**: per-shot tier status (scout/preview/final), active agent, blockers
- **Re-Scoping Triggers**: which triggers are approaching or exceeded
- **Cross-Plugin Blockers**: dependencies on other plugins' outputs
- **Next Actions**: prioritized list of human decisions and agent tasks needed

$ARGUMENTS parsed as optional `--wave` and `--shot` filters.
