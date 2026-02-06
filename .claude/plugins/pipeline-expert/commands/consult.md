---
name: consult
description: Consult a specific pipeline-expert agent directly with a question
user-invocable: true
---

# Consult Command

Direct consultation with a named pipeline-expert agent. The agent loads its
own skills, processes the question through its phase-template, and produces
output conforming to its domain's schema.

## Usage

```
/pipeline-expert:consult <agent-name> "question"
```

## Arguments

- `<agent-name>`: One of `auteur`, `tonalist`, `sculptor`, `choreographer`, `installer`, `spectralist`, `alchemist`
- `"question"`: The question to pose to the agent

## Agent Flow

1. Load the named agent from `.claude/plugins/pipeline-expert/agents/<agent-name>.md`
2. Agent loads its own skills (per its frontmatter `skills:` list)
3. Agent processes the question following phase-template (CONTEXT -> ANALYSIS -> VALIDATION -> VERDICT)
4. Agent produces output matching its domain's schema from output-schemas
5. If the agent needs input from another agent, it requests it explicitly (not automatic cross-consultation)

## Examples

```
/pipeline-expert:consult auteur "What emotional arc for the Australian bushfire sequence?"
/pipeline-expert:consult sculptor "Should the coal dust preset use clumping at this density?"
/pipeline-expert:consult spectralist "What wind field constraints apply to this OCO-3 scene?"
/pipeline-expert:consult tonalist "Is this transfer function achieving sufficient oppression?"
/pipeline-expert:consult choreographer "What camera pacing for a 90-second Secunda flyover?"
/pipeline-expert:consult installer "What projection geometry for a 6m x 3m gallery wall?"
/pipeline-expert:consult alchemist "Can the pipeline handle 4K output at 30fps for this grid?"
```

## Output

The consulted agent returns structured YAML conforming to one of:
- `creative_review` (Auteur, Tonalist)
- `render_review` (Sculptor, Spectralist, Alchemist, Installer, Choreographer)
- `ideation_result` (Auteur, when running the Ideation Protocol)

See `skills/reference/output-schemas/SKILL.md` for full schema definitions.

$ARGUMENTS parsed as `<agent-name>` and `"question"`.
