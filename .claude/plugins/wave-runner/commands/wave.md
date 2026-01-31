---
description: Orchestrate a full wave of tickets
argument-hint: "<wave-number> | all"
---

Orchestrate execution of an entire wave. Accepts a wave number or "all" to run all waves in order.

Delegate to the wave-orchestrator agent which will:
1. Load ticket YAMLs for the specified wave
2. Build a dependency DAG
3. Execute tickets in topological order
4. Report wave progress

$ARGUMENTS
