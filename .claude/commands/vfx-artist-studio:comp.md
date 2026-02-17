---
description: "Define multi-pass compositing specification for a shot/sequence"
argument-hint: "<shot-id> [--tier scout|preview|final]"
---

Multi-pass compositing specification via the compositor agent.

## Agent

Load compositor from `.claude/plugins/vfx-artist-studio/agents/compositor.md`.

## Skills

Agent loads compositing skills from `.claude/plugins/vfx-artist-studio/skills/compositing/`.

## Output

AOV manifest, merge order, grain restoration parameters, and delivery format specs.

$ARGUMENTS: `<shot-id>`, optional `--tier` flag.
