---
name: production-protocol
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Production Protocol

The cadenced heartbeat of the project. Three nested loops -- daily, weekly,
monthly -- keep velocity visible, quality measurable, and scope honest.
Adapted from VFX studio production management practices for a 1-person team
with AI agent collaborators over ~6 months (Waves 7-14).

> "A film is never finished, only abandoned at the right velocity."

---

## Principle

Production health is measured in cadence, not heroics. A team that runs its
daily/weekly/monthly loops reliably ships; a team that skips them drifts.
Every loop produces a concrete artifact (commit, burndown update, decision
log) so progress is never inferred from activity -- it is proven by output.
If a loop is skipped, the next loop must account for the gap before resuming
normal operation.

---

## Procedure

### Daily Protocol (10 minutes)

Execute these five steps in order. Each step gates the next.

| Step | Action | Artifact | Gate |
|------|--------|----------|------|
| 1 | Run `pixi run check` | Terminal output | All four gates green |
| 2 | Update ticket status in `plan/tickets/` YAML | YAML file change | Status reflects reality (`todo` -> `in_progress` -> `done`) |
| 3 | Re-read last commit diff | Mental check | Diff matches ticket `key_behavior` |
| 4 | If rendering code changed: run gallery scripts, inspect output | Gallery PNGs | No visual regression |
| 5 | Clean commit with ticket ID reference | Git commit | Commit message references ticket |

**Exit criteria**: All gates pass, working tree clean, ticket status current.

### Weekly Protocol (30 minutes)

| Step | Action | Artifact |
|------|--------|----------|
| 1 | Update `plan/burndown.md` with completed tickets | Burndown entry |
| 2 | Calculate velocity: `tickets_done / elapsed_weeks` | Velocity number |
| 3 | Compare velocity to target (~3.6 tickets/week) | Velocity delta |
| 4 | Review `output/examples/` for visual regression since last week | Pass/fail per image |
| 5 | Count open items per debt category (gate, visual, pipeline, deferred) | Debt counts |
| 6 | Identify 3-4 tickets for next week's sprint | Sprint plan |

**Velocity formula**:

```
velocity = total_tickets_done / elapsed_weeks
target_velocity = total_remaining_tickets / remaining_weeks
```

If `velocity < target_velocity * 0.8`, trigger the velocity collapse
rescoping protocol (see rescoping-triggers skill).

### Monthly Protocol (2 hours) -- Braintrust Review

Inspired by Pixar's Braintrust: structured self-review where work is
critiqued without ego. The Braintrust does not prescribe solutions; it
identifies problems and trusts the creator to solve them.

| Step | Action | Artifact |
|------|--------|----------|
| 1 | Phase gate check: is current phase on track for exit criteria? | Phase status report |
| 2 | Visual quality review: project latest gallery images at full resolution | Visual assessment |
| 3 | Pipeline integration test: run full pipeline end-to-end (data -> output) | Integration pass/fail |
| 4 | Scope review: are any tickets bloated beyond original intent? | Scope flags |
| 5 | Risk register: what could derail the next month? | Risk list |
| 6 | Decision log: record architectural and creative decisions this month | Decision entries |

**Braintrust rules**:
- Critique the work, not the person (even when the person is yourself)
- Identify problems precisely; do not prescribe solutions
- Every critique must reference a specific artifact (image, metric, code)
- If integration test fails, all feature work pauses until it passes

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `velocity_target` | float | 3.6 | 2.0 - 6.0 | Target tickets completed per week |
| `sprint_duration` | int | 7 | 5 - 14 | Sprint duration in days |
| `debt_threshold` | int | 10 | 5 - 20 | Max open debt items before forced debt sprint |
| `daily_timebox_minutes` | int | 10 | 5 - 15 | Maximum time for daily protocol |
| `weekly_timebox_minutes` | int | 30 | 20 - 45 | Maximum time for weekly protocol |
| `monthly_timebox_hours` | float | 2.0 | 1.5 - 3.0 | Maximum time for monthly Braintrust review |

---

## Technical Debt Classification

Debt items are tracked as comments in ticket YAMLs or as `blocked` tickets
with explicit unblocking conditions.

| Category | Definition | Example |
|----------|-----------|---------|
| **Gate debt** | Code passes CI but has known quality issues | Suppressed linting rule, skipped test |
| **Visual debt** | Rendering meets minimum bar but not ideal | Transfer function needs tuning, composition off |
| **Pipeline debt** | Missing integration between pipeline stages | VDB export exists but Houdini import untested |
| **Deferred scope** | Ticket features intentionally postponed | Exhibition lookdev deferred to Wave 11+ |

When `debt_threshold` is exceeded, the next sprint must be a **debt sprint**:
at least 50% of sprint capacity allocated to retiring debt items. No new
feature tickets until debt count drops below `debt_threshold * 0.7`.

---

## Anti-Patterns

### 1. Velocity Blindness

**Symptom**: Velocity metric is tracked but never compared to the target.
The team ships 2 tickets/week for a month without noticing the 3.6 target
is being missed.

**Cause**: Weekly protocol step 3 (compare velocity to target) is skipped
or treated as informational rather than actionable.

**Fix**: Velocity comparison is a gate, not a metric. If velocity is below
80% of target for 2 consecutive weeks, the rescoping-triggers protocol
fires automatically. No human judgment required -- the threshold is the
threshold.

### 2. Scope Creep

**Symptom**: A ticket that started as "add bloom post-processing" now
includes tonemapping, exposure control, and color grading. The ticket
cannot be completed in a single sprint.

**Cause**: Monthly protocol step 4 (scope review) was not performed, or
bloated tickets were noted but not split.

**Fix**: Any ticket whose implementation touches more than its declared
`related_files` must be split before work continues. The original ticket
retains its ID; child tickets get suffixed IDs (e.g., `W8-T3a`, `W8-T3b`).

### 3. Debt Hiding

**Symptom**: Debt items exist but are not tracked in ticket YAMLs. The
debt count at weekly protocol always reads zero, but the codebase has
suppressed linting rules and skipped tests.

**Cause**: Debt is treated as a personal shame rather than a production
reality. Items are "known" but not written down.

**Fix**: Every suppressed rule, skipped test, or deferred feature gets a
ticket or a `# DEBT:` comment with a category tag. If it is not tracked,
it does not exist for production purposes -- and it will bite later.

### 4. Braintrust Theater

**Symptom**: Monthly review is performed but produces no actionable
output. The decision log is empty. The risk register says "no risks."

**Cause**: The review is treated as a checkbox rather than a genuine
critique session. The Braintrust's power comes from honesty, not process.

**Fix**: Every monthly review must produce at least one critique with a
specific artifact reference and at least one risk entry. If the project
genuinely has no problems, document why -- that itself is a decision worth
recording.

---

## Validation Checklist

- [ ] Daily protocol completed today (all 5 steps)
- [ ] `pixi run check` passes (quality gates green)
- [ ] Ticket status in YAML matches actual progress
- [ ] Last commit diff matches ticket `key_behavior`
- [ ] Gallery images inspected if rendering code changed
- [ ] Weekly velocity calculated and compared to target
- [ ] Burndown updated with completed tickets
- [ ] Debt count current and below threshold
- [ ] Sprint plan identifies 3-4 tickets for next week
- [ ] Monthly Braintrust review produced decision log entries
- [ ] No debt items exist outside the tracking system
