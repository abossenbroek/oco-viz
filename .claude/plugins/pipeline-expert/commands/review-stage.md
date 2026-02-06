---
name: review-stage
description: Review a specific pipeline stage's output with domain-appropriate agents
user-invocable: true
---

# Review Stage Command

Review a pipeline stage's output artifact using the domain-appropriate agent(s).
Each stage routes to agents with the expertise to evaluate that stage's technical
correctness, loading the corresponding quality standard automatically.

## Usage

```
/pipeline-expert:review-stage <stage> <artifact-path>
```

## Arguments

- `<stage>`: One of `ingestion`, `reconstruction`, `conversion`, `rendering`, `exhibition`
- `<artifact-path>`: Path to the artifact to review (config YAML, VDB file, render image, etc.)

## Agent Routing

| Stage | Primary Agent | Secondary Agent | Standard Loaded |
|-------|--------------|-----------------|-----------------|
| ingestion | Spectralist | Auteur | data-quality |
| reconstruction | Spectralist | Auteur | reconstruction-fidelity |
| conversion | Alchemist | Spectralist | asset-integrity |
| rendering | Tonalist + Sculptor | Auteur | rendering-quality |
| exhibition | Installer | Auteur | spatial-presence |

## Agent Flow

1. Load primary agent(s) from `.claude/plugins/pipeline-expert/agents/<agent-name>.md`
2. Agent loads its own skills plus the stage-specific standard from
   `.claude/plugins/pipeline-expert/skills/standards/<standard>/SKILL.md`
3. Agent reads the artifact at `<artifact-path>`
4. Agent follows phase-template: CONTEXT -> ANALYSIS -> VALIDATION -> VERDICT
5. If a secondary agent is specified, both review independently, then findings
   are synthesized using verdict-protocol rules
6. Output: `render_review` YAML per output-schemas

## Separation from Critical-Eye

Pipeline-expert reviews CONFIGURATION and TECHNICAL CORRECTNESS: configs, code,
parameters, data files, VDB assets. For reviewing RENDERED IMAGES (pixel analysis,
artistic evaluation), use `/critical-eye:review` instead. The two plugins are
complementary, not overlapping.

## Examples

```
/pipeline-expert:review-stage ingestion data/oco3_sam_20230815.nc
/pipeline-expert:review-stage reconstruction output/assimilated_field.zarr
/pipeline-expert:review-stage conversion output/scene.vdb
/pipeline-expert:review-stage rendering configs/tiers/exhibition.yaml
/pipeline-expert:review-stage exhibition configs/installation/gallery_6x3m.yaml
```

$ARGUMENTS parsed as `<stage>` and `<artifact-path>`.
