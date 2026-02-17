---
description: "Implement a single Lookdev Bible technique as code"
argument-hint: "<technique-name> [--shot <id>] [--tier scout|preview|final]"
---

Implement a Lookdev Bible technique as executable Python code.

## Agent

Load effects-td from `.claude/plugins/vfx-artist-studio/agents/effects-td.md`.

## Skills

Agent loads the specific technique skill from `.claude/plugins/vfx-artist-studio/skills/effects/`.

## Techniques

paper-grain-manifold, sedimentary-motion, curvature-driven-emission,
stochastic-ash-culling, three-chords-of-dread, soot-crust-shader

$ARGUMENTS: `<technique-name>`, optional `--shot` and `--tier`.
