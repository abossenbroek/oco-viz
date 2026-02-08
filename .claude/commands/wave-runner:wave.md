---
description: Orchestrate a full wave of tickets
argument-hint: "<wave-number> | all"
---

Orchestrate execution of an entire wave. Accepts a wave number or "all" to run all waves in order.

Load the wave-orchestrator agent from `.claude/plugins/wave-runner/agents/wave-orchestrator.md`.
The agent uses the ticket-protocol skill from `.claude/plugins/wave-runner/skills/ticket-protocol/SKILL.md`.

The wave-orchestrator will:
1. Load ticket YAMLs for the specified wave
2. Build a dependency DAG
3. Execute tickets in topological order (delegating each to the ticket-executor agent at `.claude/plugins/wave-runner/agents/ticket-executor.md`)
4. Report wave progress

$ARGUMENTS
