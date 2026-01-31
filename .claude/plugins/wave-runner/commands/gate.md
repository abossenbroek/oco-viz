---
description: Run quality gates with auto-fix
argument-hint: "[--fix] [--only ruff|mypy|pyright|pytest]"
---

Run quality gates on the project. Delegates to the gate-runner agent.

Options:
- `--fix`: Enable auto-fix loop (default behavior)
- `--only <gate>`: Run only the specified gate (ruff, mypy, pyright, pytest)

$ARGUMENTS passed through to gate-runner.
