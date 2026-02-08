---
description: Launch a dual-model creative ideation session with Claude analysis + Gemini provocation
argument-hint: "\"creative intent description\""
---

Launch a dual-model creative ideation session. Claude establishes ground truth
from data and project state; Gemini generates radical artistic provocations;
the Auteur synthesizes both into an actionable Director's Brief.

Load the Auteur agent from `.claude/plugins/pipeline-expert/agents/auteur.md`.
Use the ideation skill from `.claude/plugins/pipeline-expert/skills/ideation/SKILL.md`.

## Ideation Protocol

### Phase 1 -- Analysis (Claude)
Establish Ground Truth from current data and project state.

### Phase 2 -- Provocation (Gemini)
Use `mcp__pal__chat` with `model: gemini-2.5-pro` to generate 3-5 radical artistic
theses that intentionally diverge from literal interpretation.

### Phase 3 -- Synthesis (Auteur)
The Auteur creates a Director's Brief with per-agent directives:
- `sculptor_directive`, `tonalist_directive`, `choreographer_directive`

### Phase 4 -- Execution
Translate the Director's Brief into actionable parameters.

## Output
`ideation_result` YAML per `.claude/plugins/pipeline-expert/skills/reference/output-schemas/SKILL.md`.

$ARGUMENTS parsed as the creative intent string.
