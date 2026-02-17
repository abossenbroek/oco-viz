---
description: "Write/update Houdini pipeline code (Hython, HDA, USD, MaterialX, Karma)"
argument-hint: "<task> [<target>] [--tier scout|preview|final]"
---

Write executable Houdini pipeline code via the houdini-td agent.

## Agent

Load houdini-td from `.claude/plugins/vfx-artist-studio/agents/houdini-td.md`.

## Skills

Agent loads houdini skills from `.claude/plugins/vfx-artist-studio/skills/houdini/`
and pipeline skills from `.claude/plugins/cinematographer/skills/pipeline/`.

## Task Types

- `upres <shot-id>` — Procedural upres
- `shader <name>` — MaterialX shader
- `render <shot-id>` — Karma XPU render config
- `tops <task> <params>` — TOPs wedging network
- `usd <shot-id>` — USD scene assembly
- `hda <name>` — Digital Asset creation

$ARGUMENTS: `<task>` type, optional `<target>`, optional `--tier` flag.
