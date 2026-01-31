---
description: Execute a single ticket from the wave plan
argument-hint: "<ticket-id> | <path.yaml>"
---

Execute a single ticket. Accepts either a ticket ID or a path to a YAML file.

If the argument is a ticket ID (e.g. "1-2"): read `plan/tickets/1-2.yaml`.
If the argument is a file path: read the YAML file directly.

Delegate to the ticket-executor agent with the YAML content.

$ARGUMENTS
