---
name: ticket-protocol
user-invocable: false
---

# Ticket Protocol

Defines the YAML ticket contract, execution phases, and output schemas for wave-based orchestration.

---

## Ticket Input Schema

Every ticket lives at `plan/tickets/{wave}-{seq}.yaml`:

```yaml
# Required fields
id: "1-2"                          # "{wave}-{seq}" identifier
title: "Human-readable title"       # Short description
wave: 1                            # Wave number (integer)
status: todo                       # todo | in_progress | done | blocked

# Dependency tracking
depends: ["1-1"]                   # List of ticket IDs that must complete first

# File outputs
produces:                          # Files this ticket will create or modify
  - src/oco_viz/plume/gaussian.py
  - tests/test_plume.py

# Quality gates
gates:                             # Gates to run after implementation
  - cmd: "pixi run pytest tests/test_plume.py -x"
    expect: exit_0                 # exit_0 | output_contains:<string>
  - cmd: "pixi run ruff check src/ tests/"
    expect: exit_0
  - cmd: "pixi run mypy src/"
    expect: exit_0
  - cmd: "pixi run pyright src/"
    expect: exit_0

# Implementation context
context:
  key_behavior: "Description of core behavior"
  patterns: ["xr.Dataset output", "float32 arrays"]
  related_files:                   # Files to read for context
    - src/oco_viz/plume/protocol.py
    - src/oco_viz/config/schema.py
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | `"{wave}-{seq}"` format |
| `title` | string | yes | Human-readable ticket title |
| `wave` | integer | yes | Wave number |
| `status` | enum | yes | `todo`, `in_progress`, `done`, `blocked` |
| `depends` | list[string] | no | Ticket IDs that must complete first |
| `produces` | list[string] | yes | Files created or modified |
| `gates` | list[gate] | yes | Quality gates to run |
| `gates[].cmd` | string | yes | Shell command to run |
| `gates[].expect` | string | yes | Expected result (`exit_0`) |
| `context` | object | no | Implementation context |
| `context.key_behavior` | string | no | Core behavior description |
| `context.patterns` | list[string] | no | Code patterns to follow |
| `context.related_files` | list[string] | no | Files to read for context |

---

## Ticket Result Output Schema (`ticket_result`)

Produced by ticket-executor after completing a ticket:

```yaml
ticket_result:
  id: "1-2"
  status: done                     # done | blocked
  files_created:
    - src/oco_viz/plume/gaussian.py
    - tests/test_plume.py
  files_modified: []
  gate_summary:
    passed: 4
    failed: 0
    auto_fixed: 2                  # Number of auto-fix cycles applied
  notes: "Optional notes about implementation decisions"
  blocked_reason: null             # Set if status is blocked
```

---

## Gate Results Output Schema (`gate_results`)

Produced by gate-runner after running quality gates:

```yaml
gate_results:
  overall: pass                    # pass | fail
  cycle_count: 2                   # Number of auto-fix cycles run
  gates:
    ruff:
      status: pass                 # pass | fail
      errors_initial: 3
      errors_final: 0
      auto_fixed: 3
      config_fix: 0
      manual: 0
      details: []
    mypy:
      status: pass
      errors_initial: 1
      errors_final: 0
      auto_fixed: 1
      config_fix: 0
      manual: 0
      details: []
    pyright:
      status: pass
      errors_initial: 0
      errors_final: 0
      auto_fixed: 0
      config_fix: 0
      manual: 0
      details: []
    pytest:
      status: pass
      errors_initial: 0
      errors_final: 0
      auto_fixed: 0
      config_fix: 0
      manual: 0
      details: []
  remaining_issues:                # Only if overall: fail
    - gate: mypy
      classification: MANUAL
      message: "Incompatible return type"
      file: "src/oco_viz/plume/gaussian.py"
      line: 42
```

---

## Wave Progress Output Schema (`wave_progress`)

Produced by wave-orchestrator after completing a wave:

```yaml
wave_progress:
  wave: 1
  status: done                     # done | partial | blocked
  tickets:
    - id: "1-1"
      status: done
      gate_summary: { passed: 4, failed: 0 }
    - id: "1-2"
      status: done
      gate_summary: { passed: 4, failed: 0 }
    - id: "1-3"
      status: blocked
      blocked_reason: "mypy MANUAL error in protocol.py:15"
  summary:
    total: 3
    done: 2
    blocked: 1
    todo: 0
```

---

## Implementation Phases

Ticket-executor follows 5 phases:

### Phase 1: Context Gathering (SELECTIVE)

Read ONLY these files to build implementation context:
- `context.related_files` from the ticket YAML
- `src/oco_viz/config/schema.py` (always — central schema)
- One existing test file matching the module pattern (for test conventions)
- `pyproject.toml` tool config sections (ruff, mypy, pyright)

Do NOT read the entire codebase. Selective context prevents hallucination.

### Phase 2: Implementation

Create all files listed in `produces`:
- Follow `context.patterns` for code style
- Apply standard module header (`from __future__ import annotations`)
- Use import strategy from gate-conventions skill

### Phase 3: Test Creation

For each test file in `produces`:
- Follow test patterns from the file read in Phase 1
- Use pytest function style (no classes)
- Include edge cases from `context.key_behavior`
- For tickets producing VTK/VDB output, include volumetric data assertions from
  the test-scaffolder (grid spacing, grid names, sparsity, temperature range).
  See `plan/coding_guide_2026.md` for the full cinematic pipeline context.

### Phase 4: Gate Execution

Run all gates from the ticket's `gates` list:
- Execute in parallel
- Apply auto-fix loop (max 4 cycles) per gate-conventions skill
- Classify remaining failures

### Phase 5: Status Output

Produce `ticket_result` YAML with:
- Final status (`done` or `blocked`)
- List of files created/modified
- Gate summary with counts
- Any blocking issues

---

## File Creation Conventions

- Source files go under `src/oco_viz/`
- Test files go under `tests/`
- Config files go under `configs/`
- Script files go under `scripts/`
- Every Python file starts with `from __future__ import annotations`
- Test files are named `test_{module}.py`
