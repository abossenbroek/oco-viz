---
description: Consult a specific pipeline-expert agent directly with a question
argument-hint: "<agent-name> \"question\""
---

Direct consultation with a named pipeline-expert agent. The agent loads its
own skills, processes the question through its phase-template, and produces
output conforming to its domain's schema.

## Available Agents

Load the named agent from `.claude/plugins/pipeline-expert/agents/<agent-name>.md`:
- `auteur` - Creative direction and artistic vision
- `tonalist` - Transfer functions and color discipline
- `sculptor` - Volume structure and material parameters
- `choreographer` - Camera language and temporal arc
- `installer` - Projection geometry and exhibition design
- `spectralist` - Atmospheric physics and data integrity
- `alchemist` - Pipeline optimization and format conversions

## Skills

Each agent loads skills per its frontmatter `skills:` list from `.claude/plugins/pipeline-expert/skills/`.
Output schemas are at `.claude/plugins/pipeline-expert/skills/reference/output-schemas/SKILL.md`.

$ARGUMENTS parsed as `<agent-name>` and `"question"`.
