# wave-runner

A Claude Code plugin that automates wave-based project execution with parallel quality gates, auto-fix loops, and YAML ticket handover.

## Installation

```bash
claude --plugin-dir ./wave-runner
```

## Commands

| Command | Description |
|---------|-------------|
| `/wave-runner:gate` | Run quality gates (ruff, mypy, pyright, pytest) with auto-fix |
| `/wave-runner:ticket <id>` | Execute a single ticket from the wave plan |
| `/wave-runner:wave <n>` | Orchestrate a full wave of tickets |
| `/wave-runner:wave-status` | Show progress across all waves |

## Ticket Schema

Tickets live at `plan/tickets/{wave}-{seq}.yaml`:

```yaml
id: "1-2"
title: "Gaussian plume generator"
wave: 1
status: todo              # todo | in_progress | done | blocked
depends: ["1-1"]
produces:
  - src/oco_viz/plume/gaussian.py
  - tests/test_plume.py
gates:
  - cmd: "pixi run pytest tests/test_plume.py -x"
    expect: exit_0
  - cmd: "pixi run ruff check src/ tests/"
    expect: exit_0
  - cmd: "pixi run mypy src/"
    expect: exit_0
  - cmd: "pixi run pyright src/"
    expect: exit_0
context:
  key_behavior: "Wind-rotated coords, ground reflection, mixing height cap"
  patterns: ["xr.Dataset output", "float32 arrays"]
  related_files:
    - src/oco_viz/plume/protocol.py
    - src/oco_viz/config/schema.py
```

## Agent Coordination Flow

```
/wave-runner:wave 1
       |
       v
wave-orchestrator (MINIMAL context: ticket YAMLs only)
       |
       v  delegates with ticket YAML
ticket-executor (FULL context: related_files + schema + test + config)
       |
       v  runs gates internally
gate-runner (SELECTIVE context: error output + specific files)
       |
       v  outputs gate_results YAML
```

## Context Fidelity Tiers

| Agent | Context Level | Reads |
|-------|--------------|-------|
| wave-orchestrator | MINIMAL | Ticket YAMLs only |
| ticket-executor | FULL | related_files + schema + test + config |
| gate-runner | SELECTIVE | Error output + specific error files |
