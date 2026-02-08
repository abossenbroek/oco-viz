---
description: Run quality gates with auto-fix
argument-hint: "[--fix] [--only ruff|mypy|pyright|pytest]"
---

Run quality gates on the project. Delegates to the gate-runner agent.

Load the gate-runner agent from `.claude/plugins/wave-runner/agents/gate-runner.md`.
The agent uses the gate-conventions skill from `.claude/plugins/wave-runner/skills/gate-conventions/SKILL.md`.

Options:
- `--fix`: Enable auto-fix loop (default behavior)
- `--only <gate>`: Run only the specified gate (ruff, mypy, pyright, pytest)

$ARGUMENTS passed through to gate-runner.
