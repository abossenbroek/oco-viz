---
description: Vermette-method visual bible session with material presets and color keys
argument-hint: "\"subject\" [--tier scout|preview|final]"
---

Multi-agent look development session. Three agents execute sequentially
via collaboration YAML: production-designer → dp → colorist.

## Agents

1. production-designer → `visual_bible_delivery` YAML
2. dp → `lighting_rig_delivery` YAML
3. colorist → `grading_delivery` YAML

Load agents from `.claude/plugins/cinematographer/agents/`.

## Skills

Each agent loads ONLY its exclusive skills from
`.claude/plugins/cinematographer/skills/`. No cross-loading.

## Output

Final `grading_delivery` collaboration YAML with full audit trail chain.
Next action suggests `/cinematographer:shoot` or `/pipeline-expert:consult auteur`.

$ARGUMENTS parsed as `"subject"` and optional `--tier` flag.
