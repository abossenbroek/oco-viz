---
description: Show progress across all waves
argument-hint: "[wave-number]"
---

Read-only scan of `plan/tickets/*.yaml` to display progress.

If a wave number is provided, show only that wave's tickets.
Otherwise, show all waves.

Display a progress table:

```
Wave | Total | Done | In Progress | Blocked | Todo
-----|-------|------|-------------|---------|-----
  1  |   5   |  3   |      1      |    1    |  0
  2  |   4   |  0   |      0      |    0    |  4
```

For each blocked ticket, show the `blocked_reason`.

$ARGUMENTS
