---
description: "Write/update Houdini pipeline code (Hython, HDA, USD, MaterialX, Karma)"
argument-hint: "<task> [<target>] [--tier scout|preview|final]"
---

Write executable Houdini pipeline code. The houdini-td writes Hython batch scripts,
HDA definitions, USD scene assembly, MaterialX shaders, and Karma XPU render configs.

## Agent

Load houdini-td from `.claude/plugins/vfx-artist-studio/agents/houdini-td.md`.

## Skills

Agent loads: `hython-coding`, `hda-authoring`, `usd-scene-assembly`,
`materialx-shading`, `karma-xpu-rendering`, `tops-wedging`
from `.claude/plugins/vfx-artist-studio/skills/`.

Also loads from cinematographer: `pipeline/hython-standards`, `pipeline/usd-patterns`,
`pipeline/openvdb-production`.

Also loads knowledge: `karma-render-profiles.yaml`, `houdini-fx-playbook.yaml`,
`asset-naming-conventions.yaml`.

## Task Types

- `upres <shot-id>` — Procedural upres via VDB Activate + Volume Noise SOPs
- `shader <name>` — MaterialX shader for Karma XPU (e.g. `shader soot-crust`)
- `render <shot-id>` — Karma XPU render config and submission script
- `tops <task> <params>` — TOPs network for parallel parameter wedging
- `usd <shot-id>` — USD scene assembly for shot
- `hda <name>` — Create/update Houdini Digital Asset

## Output

Executable artifacts written to canonical paths:
- `.py` — Hython batch scripts (run with `hython script.py`)
- `.hda` — Houdini Digital Assets (versioned)
- `.usda` — USD scene descriptions (base + override layers)
- `.mtlx` — MaterialX shader definitions

Plus collaboration YAML with `houdini_delivery` payload.

$ARGUMENTS: `<task>` type, optional `<target>`, optional `--tier` flag.
