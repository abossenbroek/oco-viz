---
description: "Promote work from one tier to the next with gate checks"
argument-hint: "<shot-id> <from-tier> <to-tier>"
---

Tier promotion orchestration. The line-producer verifies all gate checks pass for the
current tier, identifies what changes between tiers, delegates upgrade work to
appropriate agents, and coordinates critical-eye review at the new tier.

## Agent

Load line-producer from `.claude/plugins/vfx-artist-studio/agents/line-producer.md`.

## Skills

Agent loads: `production-protocol`, `task-scoping`, `cross-plugin-coordination`,
`human-agent-boundary`
from `.claude/plugins/vfx-artist-studio/skills/`.

Also loads knowledge: `tier-handoff-matrix.yaml`, `karma-render-profiles.yaml`.

## Procedure

1. Read shot context YAML for `<shot-id>`
2. Verify current tier matches `<from-tier>`
3. Run gate checks for current tier:
   - Scout → Preview: human approved creative direction, all scout effects pass visual check
   - Preview → Final: human locked all wedge parameters, VFX supe continuity ledger clean, all preview renders approved
4. Identify what changes between tiers:
   - Resolution (128³ → 512³ → 1024³)
   - Effects stack (reduced → full → exhibition-only)
   - Quality thresholds (spp, step size, denoiser)
5. Delegate upgrade work:
   - effects-td: effects stack upgrade
   - houdini-td: resolution bump, render config upgrade
   - compositor: AOV expansion
6. Coordinate critical-eye review at new tier
7. Block promotion if any gate fails

## Output

Promotion result:
- **Gate Check Results**: pass/fail per gate with details
- **Tier Changes**: specific parameter changes between tiers
- **Delegated Tasks**: tasks assigned to each agent for the new tier
- **Blocked**: if any gate fails, specific blocking reason and required action

$ARGUMENTS: `<shot-id>` (e.g. sc010), `<from-tier>` (scout|preview), `<to-tier>` (preview|final).
