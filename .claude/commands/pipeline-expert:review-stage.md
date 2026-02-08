---
description: Review a specific pipeline stage's output with domain-appropriate agents
argument-hint: "<stage> <artifact-path>"
---

Review a pipeline stage's output artifact using the domain-appropriate agent(s).
Each stage routes to agents with the expertise to evaluate that stage's technical
correctness, loading the corresponding quality standard automatically.

## Agent Routing

| Stage | Primary Agent | Standard |
|-------|--------------|----------|
| ingestion | `.claude/plugins/pipeline-expert/agents/spectralist.md` | data-quality |
| reconstruction | `.claude/plugins/pipeline-expert/agents/spectralist.md` | reconstruction-fidelity |
| conversion | `.claude/plugins/pipeline-expert/agents/alchemist.md` | asset-integrity |
| rendering | `.claude/plugins/pipeline-expert/agents/tonalist.md` + `sculptor.md` | rendering-quality |
| exhibition | `.claude/plugins/pipeline-expert/agents/installer.md` | spatial-presence |

## Standards

Quality standards loaded from `.claude/plugins/pipeline-expert/skills/standards/<standard>/SKILL.md`.
Output schemas at `.claude/plugins/pipeline-expert/skills/reference/output-schemas/SKILL.md`.

## Separation from Critical-Eye

Pipeline-expert reviews CONFIGURATION and TECHNICAL CORRECTNESS. For reviewing
RENDERED IMAGES (pixel analysis, artistic evaluation), use `/critical-eye:review`.

$ARGUMENTS parsed as `<stage>` and `<artifact-path>`.
