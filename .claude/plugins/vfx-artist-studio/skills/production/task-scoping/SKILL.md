---
name: task-scoping
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Task Scoping

Every task must be small enough for a single agent invocation and precise
enough that the agent knows when it is done. If a task cannot be described
in one sentence with a clear exit condition, it is too large. Split first,
execute second.

> "The art of war is the art of subdivision." -- Napoleon (and every
> production manager who ever shipped on time)

---

## Principle

A well-scoped task is the fundamental unit of predictable delivery. It has
one agent, one deliverable, clear exit criteria, and fits within a single
context window of work. Ambiguity in scoping cascades into ambiguity in
execution, which cascades into missed deadlines and rework. The line-producer
enforces scoping discipline before any agent begins execution. No task
enters `in_progress` status without passing the scoping checklist.

---

## Procedure

### Step 1 -- Evaluate Task Against Scoping Rules

Every proposed task must satisfy ALL of the following rules:

| Rule | Requirement | Violation Signal |
|------|-------------|-----------------|
| Single agent | One agent owns the task end-to-end | Task description names multiple agents |
| Single deliverable | One output artifact (file, config, image) | Task produces multiple unrelated outputs |
| Clear exit criteria | Binary pass/fail condition | "Improve" or "optimize" without a threshold |
| Context-window fit | Total related files fit in one context window | `related_files` list exceeds 8 files |
| Bounded scope | Touches a known, bounded set of files | "Wherever needed" or "across the codebase" |

### Step 2 -- Check Splitting Criteria

If ANY of these conditions are true, the task MUST be split before execution:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| File count | Touches > 3 files | Split by file boundary |
| Skill count | Requires > 2 skills | Split by skill boundary |
| Ambiguous exit | Exit criteria contain "should", "might", "ideally" | Rewrite exit criteria as binary |
| Multi-tier | Spans scout + preview or preview + final | Split by tier |
| Multi-agent | Requires handoff between agents mid-task | Split at handoff point |
| Duration | Estimated > 1 context window of agent work | Split by logical sub-deliverable |

### Step 3 -- Fill Task Template

Every task that passes scoping gets this template filled before execution:

```yaml
task:
  id: string              # ticket ID (e.g., W8-T3)
  agent: string            # single owning agent
  deliverable: string      # one output artifact
  exit_criteria: string    # binary pass/fail condition
  max_files: int           # bounded file count (<= 3)
  skills_required:         # list of skills needed (<= 2)
    - string
  tier: string             # scout | preview | final
  shot_id: string          # shot reference if applicable
  related_files:           # exhaustive list of files to read/modify
    - path: string
  estimated_effort: string # S (< 30 min), M (30-90 min), L (90+ min)
  depends_on:              # tasks that must complete first
    - task_id: string
```

### Step 4 -- Validate Template Completeness

Every field must be filled. Empty fields indicate incomplete scoping.

| Field | Validation Rule |
|-------|----------------|
| `id` | Matches pattern `W\d+-T\d+[a-z]?` |
| `agent` | Must be a recognized agent from any plugin |
| `deliverable` | Must be a concrete noun (file, config, image), not an action verb |
| `exit_criteria` | Must be a complete sentence with a measurable condition |
| `max_files` | Integer, 1-3 (or 4-6 with line-producer approval) |
| `skills_required` | 1-2 entries, each a valid skill name |
| `tier` | One of: scout, preview, final |
| `estimated_effort` | One of: S, M, L |

---

## Splitting Strategies

When a task must be split, use the strategy that produces the most
independent sub-tasks (fewest dependencies between children):

### By File Boundary

Split when the task touches files in different modules. Each sub-task owns
one module's files.

```
W8-T3: "Add bloom to post-processing and update gallery"
  -> W8-T3a: "Add bloom to postprocess/bloom.py" (effects-td)
  -> W8-T3b: "Update gallery script to exercise bloom" (line-producer)
```

### By Skill Boundary

Split when the task requires skills from different domains. Each sub-task
uses one skill.

```
W9-T1: "Create Karma material and render preview"
  -> W9-T1a: "Author MaterialX shader" (houdini-td, materialx-shading)
  -> W9-T1b: "Render preview tier" (houdini-td, karma-xpu-rendering)
```

### By Tier Boundary

Split when the task spans tiers. Each sub-task targets one tier.

```
W10-T2: "Implement camera path for scout and preview"
  -> W10-T2a: "Implement camera path at scout tier" (dp)
  -> W10-T2b: "Promote camera path to preview tier" (dp)
```

### By Handoff Point

Split when the task requires inter-agent collaboration. Each sub-task is
one side of the handoff, connected by a collaboration YAML.

```
W11-T4: "Grade and composite final shot"
  -> W11-T4a: "Deliver grading for SH010" (colorist -> compositor)
  -> W11-T4b: "Composite graded SH010" (compositor)
```

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `max_files_per_task` | int | 3 | 1 - 6 | Maximum files a single task may touch |
| `max_skills_per_task` | int | 2 | 1 - 3 | Maximum skills a single task may require |
| `max_context_files` | int | 8 | 4 - 12 | Maximum related_files before mandatory split |
| `effort_threshold_split` | string | L | M, L | Effort level that triggers split review |

---

## Anti-Patterns

### 1. The Mega-Task

**Symptom**: A single ticket says "Implement the full Karma rendering
pipeline." It has 12 related files, requires 5 skills, and no one can
explain when it is done.

**Cause**: Task was conceived at the feature level rather than the
deliverable level. Features are made of tasks; tasks are not features.

**Fix**: Split by deliverable. A feature like "Karma rendering pipeline"
becomes 4-6 tasks: "Author base material", "Configure render settings",
"Build USD scene assembly", "Render scout tier", "Validate against
groundtruth." Each has one agent, one deliverable, one exit condition.

### 2. Vague Exit Criteria

**Symptom**: Exit criteria say "the rendering looks good" or "performance
is acceptable." The agent cannot determine when it is done, so it either
stops too early or iterates indefinitely.

**Cause**: Exit criteria written as subjective quality judgments instead of
measurable conditions.

**Fix**: Replace every subjective word with a number or a binary check.
"Looks good" becomes "passes critical-eye review with no FAIL verdicts."
"Performance is acceptable" becomes "renders 128-cubed volume in < 30
seconds on M1 Mac."

### 3. The Multi-Agent Task

**Symptom**: A task says "the effects-td builds the shader and the
compositor integrates it." Two agents share ownership, and neither knows
whether they or the other agent is responsible for the final deliverable.

**Cause**: The handoff between agents was embedded inside a task instead of
being a task boundary.

**Fix**: Split at the handoff. Task A produces an artifact. Task B
consumes it. The collaboration YAML is the contract between them. Each
task has exactly one owning agent.

### 4. The Tier-Spanning Task

**Symptom**: A task says "implement and validate across scout, preview, and
final tiers." The agent must switch context between resolution levels,
quality requirements, and validation criteria multiple times.

**Cause**: Tier progression was treated as a single activity rather than a
promotion pipeline. Each tier has different parameters, different quality
bars, and often different agents.

**Fix**: One task per tier. Scout first, validate, then promote to preview
as a separate task. Tier promotion is never implicit -- it is always an
explicit task with its own exit criteria.

---

## Validation Checklist

- [ ] Task has exactly one owning agent
- [ ] Task produces exactly one deliverable artifact
- [ ] Exit criteria are binary (pass/fail), not subjective
- [ ] Task touches <= `max_files_per_task` files
- [ ] Task requires <= `max_skills_per_task` skills
- [ ] `related_files` list fits in one context window (<= `max_context_files`)
- [ ] Task template is fully filled (no empty fields)
- [ ] Task ID matches `W\d+-T\d+[a-z]?` pattern
- [ ] No splitting criteria are violated
- [ ] Dependencies (`depends_on`) are explicit and resolvable
- [ ] Estimated effort is S or M (L triggers split review)
