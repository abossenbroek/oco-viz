---
description: Comprehensive cross-stage pipeline audit with conceptual audit trail
argument-hint: "[--stages stage1,stage2,...] [--focus area]"
---

Comprehensive cross-stage pipeline audit orchestrated by the Auteur as creative
director. Reviews each stage with its domain agent, then synthesizes findings
into a unified assessment with a conceptual audit trail.

Load the Auteur agent from `.claude/plugins/pipeline-expert/agents/auteur.md`.

## Agent Routing

Each stage is reviewed by its primary agent:
- Ingestion: `.claude/plugins/pipeline-expert/agents/spectralist.md`
- Reconstruction: `.claude/plugins/pipeline-expert/agents/spectralist.md`
- Conversion: `.claude/plugins/pipeline-expert/agents/alchemist.md`
- Rendering: `.claude/plugins/pipeline-expert/agents/tonalist.md` + `.claude/plugins/pipeline-expert/agents/sculptor.md`
- Exhibition: `.claude/plugins/pipeline-expert/agents/installer.md`

## Standards

Load the relevant quality standards from `.claude/plugins/pipeline-expert/skills/standards/`.

## Arguments

- `--stages`: (optional) Comma-separated stages to audit. Default: all 5.
- `--focus`: (optional) `scientific-integrity`, `artistic-coherence`, `pipeline-health`, or `all`. Default: `all`.

$ARGUMENTS parsed for `--stages` and `--focus` flags.
