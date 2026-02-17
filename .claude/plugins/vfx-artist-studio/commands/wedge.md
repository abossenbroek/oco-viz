---
description: "Iterative lookdev discovery via parameter wedging (Contact Sheet Bible)"
argument-hint: "<shot-id> [--technique <name>] [--params <list>]"
---

Iterative lookdev discovery using the Contact Sheet Bible workflow (Technique 7).
The effects-td generates parameter wedges, renders contact sheets, and tracks
the wedge→review→lock cycle.

## Agent

Load effects-td from `.claude/plugins/vfx-artist-studio/agents/effects-td.md`.

## Skills

Agent loads all effects skills plus `reference/collaboration-protocol`.
Also loads knowledge: `houdini-fx-playbook.yaml` (for TOPs wedge configuration).

## Procedure

1. Identify shot and technique to wedge
2. Load wedge parameter ranges from the technique's skill (e.g. grain_amplitude 0.02-0.12)
3. Generate TOPs wedge specification (parameter grid, render settings)
4. Define contact sheet layout (10x10 grid for 100 variations)
5. Track the 3-day time box: Day 1 submit+triage, Day 2 full-res+print, Day 3 evaluate+lock
6. Produce parameter lock recommendation for human approval

## Output

Wedge delivery with:
- TOPs wedge specification (parameter ranges, steps, total variations)
- Contact sheet layout definition
- Parameter log mapping index → parameter values
- Lock recommendation with rationale

Next action: human reviews contact sheet, locks parameters.

$ARGUMENTS: `<shot-id>`, optional `--technique` filter, optional `--params` for specific parameters.
