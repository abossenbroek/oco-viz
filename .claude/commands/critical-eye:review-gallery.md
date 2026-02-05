---
description: Batch visual quality review with auto-detected tier
argument-hint: "<dir>"
---

Batch review all gallery images in a directory. Auto-detects tier from filenames and runs the full two-agent review pipeline for each tier group.

Load the critical-eye agent from `.claude/plugins/critical-eye/agents/critical-eye.md`.
Use the visual-language skill from `.claude/plugins/critical-eye/skills/visual-language/SKILL.md`.

Tier detection from filename patterns:
- `*exhibition*` or `*exhibit*` -> exhibition
- `*study*` -> study
- `*sketch*` -> sketch
- No tier keyword -> study (default)

Images are grouped by detected tier. Each group is reviewed using the corresponding tier standard and persona.

Sequence detection: multiple images sharing a base name with frame numbers (e.g., `easing_heavy_t02.png`, `easing_heavy_t04.png`) are treated as a sequence with temporal coherence evaluation.

Key constraints:
- Read-only: no files created or modified
- Auto-tier: no need to specify tier manually
- Batch efficient: groups images to minimize agent context loading

$ARGUMENTS passed through to critical-eye agent.
