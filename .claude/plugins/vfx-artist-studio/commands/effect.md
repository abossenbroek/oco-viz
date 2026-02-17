---
description: "Implement a single Lookdev Bible technique as code"
argument-hint: "<technique-name> [--shot <id>] [--tier scout|preview|final]"
---

Implement a single Lookdev Bible technique as executable Python code against
existing plume/noise.py, plume/turbulent.py, and postprocess/ APIs.

## Agent

Load effects-td from `.claude/plugins/vfx-artist-studio/agents/effects-td.md`.

## Skills

Agent loads the specific technique skill:
- `paper-grain-manifold` (Technique 1)
- `sedimentary-motion` (Technique 2)
- `curvature-driven-emission` (Technique 3)
- `stochastic-ash-culling` (Technique 4)
- `three-chords-of-dread` (Technique 5)
- `soot-crust-shader` (Technique 6)

Plus `reference/collaboration-protocol` and `reference/output-schemas`.

## Procedure

1. Load technique skill for specified technique
2. Read existing API: `src/oco_viz/plume/noise.py`, `src/oco_viz/plume/turbulent.py`
3. Implement technique using existing functions (fbm_3d, curl_noise_3d, apply_turbulence)
4. Apply tier awareness: exhibition effects disabled at scout/study
5. Use fixed seeds per shot for reproducibility
6. Write code following project standards (from __future__ import annotations, ruff ALL)
7. Run quality gates

## Output

- Python implementation using existing API
- Effects delivery collaboration YAML
- Next action: `/vfx-artist-studio:wedge` for parameter discovery

$ARGUMENTS: `<technique-name>` (one of the 6 techniques), optional `--shot` and `--tier`.
