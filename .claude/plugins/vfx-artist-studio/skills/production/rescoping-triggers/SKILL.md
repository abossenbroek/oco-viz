---
name: rescoping-triggers
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Rescoping Triggers

Conditions that fire mandatory scope review. These are not suggestions --
they are circuit breakers. When a trigger fires, normal feature work stops
and the line-producer executes the prescribed action before any new work
begins. Ignoring a fired trigger is a production violation.

> "The schedule is your friend until you lie to it. Then it becomes your
> enemy." -- every VFX producer who has shipped a show

---

## Principle

Rescoping is not failure. Rescoping is the production system working as
designed. A project that never rescopes is either trivially simple or
dangerously unaware of its own velocity. The triggers defined here encode
objective thresholds that remove human judgment from the "should we
rescope?" question. When the threshold is crossed, the action fires. No
debate, no deferral, no "let's see how next week goes."

The line-producer monitors these triggers at every weekly protocol
execution. If a trigger fires between weekly checkpoints (e.g., CI breaks
on a Tuesday), it activates immediately -- it does not wait for the weekly
cadence.

---

## Procedure

### Step 1 -- Evaluate All Triggers

At every weekly protocol (and on any day when an obvious trigger event
occurs), evaluate each trigger condition:

| # | Trigger | Metric | Threshold | Measurement Method |
|---|---------|--------|-----------|-------------------|
| T1 | Velocity collapse | tickets/week | < 2.0 for 2 consecutive weeks | `tickets_done / elapsed_weeks` from burndown |
| T2 | Phase overrun | phase duration | Exceeds estimate by > 50% | Calendar days vs. phase plan |
| T3 | Visual regression loop | critical-eye retries | Same image fails 3+ times | Count FAIL verdicts per image ID |
| T4 | CI red streak | consecutive CI failures | > 2 consecutive days | `pixi run ci` pass/fail log |

### Step 2 -- If Trigger Fires, Execute Prescribed Action

Each trigger has exactly one prescribed action. The action is not
negotiable -- it is the minimum response. Additional actions may be taken
at the line-producer's discretion, but the prescribed action is mandatory.

---

## Trigger T1: Velocity Collapse

**Condition**: Velocity drops below 2.0 tickets/week for 2 consecutive
weeks.

**Why this threshold**: The project targets ~3.6 tickets/week over 18
weeks. At 2.0 tickets/week, the project is operating at 56% of target
velocity. A single bad week is noise; two consecutive bad weeks is a
trend that requires intervention.

**Prescribed action**:

1. **Freeze**: No new tickets enter `in_progress`
2. **Audit**: Review all `in_progress` tickets for scope bloat
3. **Split or defer**: Each `in_progress` ticket is either:
   - Split into smaller sub-tasks (if scope bloated)
   - Deferred to a later wave (if non-critical)
   - Completed as-is (if nearly done)
4. **Re-plan**: Recalculate remaining velocity required and adjust
   wave assignments if `required_velocity > velocity_target * 1.2`
5. **Resume**: Only after re-plan is complete and documented in burndown

**Recovery criteria**: Velocity returns to >= 3.0 tickets/week for 1 week.

---

## Trigger T2: Phase Overrun

**Condition**: A phase exceeds its estimated duration by more than 50%.

**Why this threshold**: Phases are estimated with buffer. Exceeding by 50%
means both the estimate and the buffer are consumed. The remaining phases
will be compressed unless scope is cut.

**Prescribed action**:

1. **Assess**: List all incomplete tickets in the overrunning phase
2. **Classify**: Each ticket is either:
   - **Critical path**: Must complete for the phase to be meaningful
   - **Aspirational**: Nice to have but not blocking downstream phases
3. **Split the phase**:
   - Critical-path tickets remain in current phase
   - Aspirational tickets move to a new "Phase X.5" or defer to a later wave
4. **Adjust downstream**: Recalculate start dates for all subsequent phases
5. **Document**: Record the phase split in `plan/burndown.md` with rationale

**Recovery criteria**: The reduced phase completes within 2 weeks of the
revised estimate.

---

## Trigger T3: Visual Regression Loop

**Condition**: The same image (identified by shot ID or gallery filename)
fails the critical-eye review 3 or more times.

**Why this threshold**: One failure is a normal iteration. Two failures
suggest a parameter tuning problem. Three failures indicate a systemic
issue -- the root cause is not in the parameters being adjusted but in
something upstream (density field, transfer function architecture,
lighting topology).

**Prescribed action**:

1. **Pause**: All feature work stops for the failing shot
2. **Root cause**: Investigate upstream of the failing parameter:
   - If lighting fails: check density field distribution
   - If transfer function fails: check normalization pipeline
   - If composition fails: check camera path and volume bounds
3. **Fix upstream**: Apply the fix to the root cause, not the symptom
4. **Re-render**: Generate fresh gallery images from the fixed upstream
5. **Re-review**: Submit to critical-eye review as a new submission (not
   a retry of the old one)

**Recovery criteria**: The image passes critical-eye review on the first
submission after the root-cause fix.

**Escalation**: If the image fails a 5th time after root-cause
investigation, escalate to the monthly Braintrust review regardless of
calendar timing.

---

## Trigger T4: CI Red Streak

**Condition**: `pixi run ci` fails for more than 2 consecutive days.

**Why this threshold**: CI is the immune system of the project. A 1-day
failure is a cold; 2+ consecutive days is an infection. Feature work on a
red CI is building on quicksand -- every commit is unvalidated and
potentially compounding the problem.

**Prescribed action**:

1. **Stop**: All feature work halts immediately. No new commits except
   CI fixes.
2. **Diagnose**: Identify the failing gate(s):
   - ruff: likely a new lint rule or import issue
   - mypy/pyright: likely a type annotation regression
   - pytest: likely a broken test or missing fixture
   - spell: likely a new technical term not in the dictionary
3. **Fix**: Address the root cause, not the symptom. If a lint rule is
   being suppressed to pass CI, that is debt, not a fix.
4. **Verify**: `pixi run ci` must pass 2 consecutive runs before feature
   work resumes.
5. **Post-mortem**: Add a 1-line entry to the weekly protocol notes
   explaining what broke CI and how it was prevented from recurring.

**Recovery criteria**: `pixi run ci` passes 2 consecutive runs.

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `velocity_threshold` | float | 2.0 | 1.0 - 3.0 | Minimum tickets/week before T1 fires |
| `velocity_consecutive_weeks` | int | 2 | 2 - 4 | Consecutive weeks below threshold before T1 fires |
| `overrun_threshold` | float | 0.5 | 0.3 - 1.0 | Phase duration overrun fraction before T2 fires (0.5 = 50%) |
| `regression_max_retries` | int | 3 | 2 - 5 | Critical-eye failures on same image before T3 fires |
| `regression_escalation` | int | 5 | 4 - 7 | Failures before mandatory Braintrust escalation |
| `ci_fail_max_days` | int | 2 | 1 - 3 | Consecutive CI failure days before T4 fires |
| `ci_recovery_runs` | int | 2 | 2 - 3 | Consecutive CI passes required to resume feature work |

---

## Anti-Patterns

### 1. Ignoring Triggers

**Symptom**: Velocity has been below 2.0 for three weeks, but the
line-producer notes it in the weekly report and continues planning feature
work. "We'll catch up next week."

**Cause**: The trigger is treated as advisory rather than mandatory. The
prescribed action feels disruptive, so it is deferred.

**Fix**: Triggers are circuit breakers, not suggestions. When the threshold
is crossed, the action fires. If the action feels too disruptive, adjust
the threshold parameter -- do not ignore the trigger at its current setting.

### 2. Premature Rescoping

**Symptom**: After a single slow week (velocity 2.5), the line-producer
panics and rescopes the entire wave. Tickets are deferred that were on
track. Morale drops.

**Cause**: Confusing a single data point with a trend. The velocity
threshold requires 2 consecutive weeks precisely to filter noise from
signal.

**Fix**: Trust the threshold. A single bad week is within normal variance.
Record it, note the cause if known, and continue. Only act when the
consecutive-week condition is met.

### 3. Scope-Only-Once

**Symptom**: The project rescoped in month 2 and never rescoped again,
despite velocity fluctuations and phase overruns in months 3-5. "We
already rescoped."

**Cause**: Treating rescoping as a one-time event rather than a recurring
production mechanism. Scope is not set in stone after the first
adjustment.

**Fix**: Triggers are evaluated at every weekly checkpoint for the entire
project duration. A trigger that fired in month 2 can fire again in month
4. Each firing produces its own prescribed action independently.

### 4. Symptom Fixing

**Symptom**: Visual regression trigger fires, and the response is to
tweak the transfer function parameters until the image passes. Two weeks
later, a different image starts failing with similar symptoms.

**Cause**: The prescribed action (investigate upstream root cause) was
replaced with the faster action (tweak parameters). The root cause --
perhaps a normalization bug or density field artifact -- remains.

**Fix**: Follow the prescribed action literally. Step 2 of T3 says
"investigate upstream." If the failure is in lighting, look at density.
If the failure is in transfer function, look at normalization. The fix
must be at a different pipeline stage than the symptom.

---

## Validation Checklist

- [ ] All four triggers evaluated at weekly protocol
- [ ] No trigger has been in fired state for > 1 week without prescribed action
- [ ] Velocity is calculated from burndown data, not estimated
- [ ] Phase duration is measured in calendar days, not "working days"
- [ ] Visual regression count tracks per-image, not aggregate
- [ ] CI failure count resets only after `ci_recovery_runs` consecutive passes
- [ ] Prescribed actions are executed in order (no step skipping)
- [ ] Recovery criteria are verified before resuming feature work
- [ ] Parameter overrides (if any) are documented in sprint plan
- [ ] Post-mortems are recorded for T4 (CI red streak) incidents
