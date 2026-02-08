# Production Tracking Protocol

Adapted from VFX studio production management practices for a 1-person team over ~6 months (Waves 7-14).

---

## Daily Protocol (10 minutes)

1. **Quality gates**: Run `pixi run check` — all four gates must pass before any commit
2. **Wave progress**: Update current ticket status in `plan/tickets/` YAML (`todo` -> `in_progress` -> `done`)
3. **Self-review**: Re-read the last commit diff — does it match the ticket's `key_behavior`?
4. **Visual review**: If any rendering code changed, run gallery scripts and inspect output
5. **Commit**: Clean commit with ticket ID reference

## Weekly Protocol (30 minutes)

1. **Burndown update**: Update `plan/burndown.md` with completed tickets
2. **Velocity calculation**: tickets_done / elapsed_weeks (target: ~3.6 tickets/week for 18-week schedule)
3. **Gallery audit**: Review `output/examples/` for any visual regression since last week
4. **Debt count**: Count open items in each debt category (see below)
5. **Next week plan**: Identify the 3-4 tickets for next week's sprint

## Monthly Protocol (2 hours) — Braintrust Review

Inspired by Pixar's Braintrust: a structured self-review where the work is critiqued without ego.

1. **Phase gate check**: Is the current phase on track to meet its exit criteria?
2. **Visual quality review**: Print or project the latest gallery images at full resolution
3. **Pipeline integration test**: Run the full pipeline end-to-end from data to output
4. **Scope review**: Are any tickets bloated beyond their original intent?
5. **Risk register**: What could derail the next month? (dependency, tooling, creative block)
6. **Decision log**: Record any architectural or creative decisions made this month

---

## Re-Scoping Triggers

These conditions trigger a mandatory scope review:

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Velocity collapse | < 2.0 tickets/week for 2 consecutive weeks | Re-scope current wave, defer non-critical tickets |
| Phase overrun | Phase exceeds estimated duration by > 50% | Split phase, defer aspirational features |
| Visual regression loop | Same image fails critical-eye review 3+ times | Pause feature work, fix root cause |
| CI red streak | `pixi run ci` fails for > 2 consecutive days | Stop all feature work, fix CI |

---

## Technical Debt Classification

| Category | Definition | Example |
|----------|-----------|---------|
| **Gate debt** | Code that passes CI but has known quality issues | Suppressed linting rule, skipped test |
| **Visual debt** | Rendering output that meets minimum bar but not ideal | Transfer function needs tuning, composition off |
| **Pipeline debt** | Missing integration between pipeline stages | VDB export exists but Houdini import untested |
| **Deferred scope** | Ticket features intentionally postponed | Exhibition lookdev deferred to Wave 11+ |

Debt items are tracked as comments in ticket YAMLs or as `blocked` tickets with explicit unblocking conditions.
