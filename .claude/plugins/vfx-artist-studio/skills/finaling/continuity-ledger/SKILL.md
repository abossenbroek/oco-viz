---
name: continuity-ledger
user-invocable: false
type: instruction
primary_owner: vfx-supe
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Continuity Ledger --- Cross-Shot Parameter Tracking

In live-action VFX the script supervisor tracks every physical detail across shots ---
the actor's collar is up in take 3, down in take 5; the glass is half-full at 00:42:15
and empty at 00:42:18 without anyone drinking from it. These continuity errors destroy
the illusion of a unified reality. In volumetric rendering the equivalent danger is
parameter drift: grain amplitude creeps from 0.05 to 0.08 across a sequence, crust
threshold shifts from 0.4 to 0.45 between shots, shadow density wanders from 0.92 to
0.88 without anyone noticing --- until the sequence plays back and the viewer senses
something is wrong without being able to articulate what.

The continuity ledger is the authoritative record of every cross-shot parameter. It is
not a configuration file --- it is a contract. Once a parameter is locked in the ledger,
it does not change without explicit VFX supe approval, documentation of the reason, and
re-verification across every shot that references it.

> "Continuity is invisible when it works. When it fails, it is all you see."

---

## Principle

Every cross-shot parameter is tracked in the continuity ledger. Parameter drift between
shots is the most common source of visual discontinuity in sequences. The ledger
provides a single source of truth for every value that must be consistent across shots,
distinguishing between creative parameters (exact match required) and technical
parameters (configurable tolerance allowed). The VFX supe owns the ledger. No agent,
no automated process, and no artist may modify a locked value without the supe's
documented approval.

The ledger solves three problems simultaneously:
1. **Drift detection** --- small incremental changes that are invisible per-shot but
   visible in sequence
2. **Provenance tracking** --- who locked this value, when, and why
3. **Verification automation** --- machine-readable format enables automated checks
   during finaling

---

## Procedure

### Step 1 --- Identify Tracked Parameters

Every parameter that affects the visual appearance of the rendered output and must be
consistent across multiple shots is a tracked parameter. The ledger tracks all wedge
parameters from the creative pipeline plus lighting and render settings:

**Creative Parameters (variance_tolerance: 0.0)**

| Category | Parameters |
|----------|-----------|
| Transfer function | opacity_curve, color_map, density_scale, emission_intensity |
| Grain / texture | grain_amplitude, grain_frequency, grain_temporal_stability, grain_shadow_mult, grain_highlight_mult |
| Crust shader | crust_threshold, crust_transition_width, crust_inner_material, crust_outer_material |
| Emission | emission_base_intensity, emission_pulse_amplitude, emission_color_temp |
| Post-processing | bloom_radius, bloom_intensity, tonemap_curve, exposure_bias |

**Technical Parameters (variance_tolerance: configurable)**

| Category | Parameters | Typical Tolerance |
|----------|-----------|-------------------|
| Lighting | key_intensity, key_color_temp, key_azimuth, key_elevation | 0.02, 50K, 2 deg, 2 deg |
| Render settings | sample_count, volume_step_size, denoiser_strength | 0, 0.001, 0.02 |
| Camera | focal_length, aperture, focus_distance | 0.5mm, 0.1 stop, 0.1m |

### Step 2 --- Create the Ledger

The ledger is a YAML file stored alongside the sequence configuration. One ledger per
sequence. The format is machine-readable for automated verification during finaling:

```yaml
continuity_ledger:
  sequence_id: "descent_of_carbon"
  version: 3
  last_modified: "2026-02-15T14:30:00Z"
  last_modified_by: "human"
  approval_required_for_changes: true

  entries:
    - parameter: "grain_amplitude"
      category: creative
      locked_value: 0.05
      locked_by: "human"
      locked_date: "2026-02-15"
      lock_reason: "Approved in dailies session 2026-02-14, matches reference photography grain level"
      shots_applied: ["sc010", "sc020", "sc030", "sc040", "sc050"]
      variance_tolerance: 0.0  # exact match required
      verification_method: "sample grain amplitude at density 0.5, compare to locked value"

    - parameter: "crust_threshold"
      category: creative
      locked_value: 0.4
      locked_by: "human"
      locked_date: "2026-02-15"
      lock_reason: "Crust transition zone approved in lookdev review, shot sc010 reference"
      shots_applied: ["sc010", "sc020", "sc030", "sc040", "sc050"]
      variance_tolerance: 0.0
      verification_method: "check config value against locked value"

    - parameter: "key_intensity"
      category: technical
      locked_value: 0.65
      locked_by: "human"
      locked_date: "2026-02-14"
      lock_reason: "Key intensity set to match furnace motivation, approved in lighting review"
      shots_applied: ["sc010", "sc020", "sc030"]
      variance_tolerance: 0.02  # small technical adjustment allowed
      verification_method: "check config value, verify within tolerance"

    - parameter: "shadow_density"
      category: creative
      locked_value: 0.92
      locked_by: "human"
      locked_date: "2026-02-14"
      lock_reason: "Shadow depth approved in Deakins-method lighting review"
      shots_applied: ["sc010", "sc020", "sc030", "sc040", "sc050"]
      variance_tolerance: 0.0
      verification_method: "measure shadow region luminance, convert to density"
```

### Step 3 --- Lock Parameters

A parameter is locked when a human creative decision is made and documented. The lock
process:

```
LOCK PROCESS:
1. Parameter value finalized in lookdev or dailies review
2. Human confirms the value (not an agent suggestion, not an auto-tune result)
3. Lock entry created in ledger with:
   - locked_value: the exact value
   - locked_by: "human" (mandatory for creative params)
   - locked_date: ISO date
   - lock_reason: why this value, referencing the review session
   - shots_applied: which shots this value applies to
   - variance_tolerance: 0.0 for creative, configurable for technical
4. Ledger version incremented
5. All shots in shots_applied verified against locked value
```

An agent may propose a value, but only a human may lock it. The `locked_by` field
enforces this distinction. During finaling, any parameter with `locked_by != "human"`
is flagged as unlocked and blocks the finaling checklist.

### Step 4 --- Verify Against Ledger

Verification runs during finaling (two-percent-rule Step 8) and can be run at any time
during production:

```python
def verify_continuity(ledger_path: str, shot_configs: dict[str, dict]) -> list[str]:
    """Verify all shot configs against the continuity ledger.

    Returns list of failure messages. Empty list = all checks pass.
    """
    failures = []
    ledger = load_ledger(ledger_path)

    for entry in ledger["entries"]:
        param = entry["parameter"]
        locked = entry["locked_value"]
        tolerance = entry["variance_tolerance"]

        for shot_id in entry["shots_applied"]:
            if shot_id not in shot_configs:
                failures.append(f"{shot_id}: missing config for tracked parameter {param}")
                continue

            actual = shot_configs[shot_id].get(param)
            if actual is None:
                failures.append(f"{shot_id}: parameter {param} not found in config")
                continue

            if abs(actual - locked) > tolerance:
                failures.append(
                    f"{shot_id}: {param} = {actual}, locked = {locked}, "
                    f"delta = {abs(actual - locked):.6f}, tolerance = {tolerance}"
                )

    return failures
```

### Step 5 --- Modify a Locked Parameter

When a locked parameter must be changed (creative revision, technical discovery), the
modification follows a strict protocol:

```
MODIFICATION PROTOCOL:
1. VFX supe approves the change (documented in dailies notes)
2. Old entry is NOT deleted --- it is marked as superseded:
   superseded_by: "entry_v4"
   superseded_date: "2026-02-16"
   superseded_reason: "Grain too coarse at exhibition projection scale"
3. New entry created with updated locked_value and new lock metadata
4. Ledger version incremented
5. ALL shots in shots_applied are re-rendered and re-verified
6. Full sequence re-reviewed in dailies (not just the changed shots)
```

The ledger maintains history. No value is ever deleted --- only superseded. This
provides an audit trail for creative decisions and enables rollback if the new value
proves worse in sequence context.

---

## Parameters

### Ledger Structure Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `ledger_path` | path | `continuity_ledger.yaml` | --- | Path to the ledger file relative to sequence root |
| `ledger_version_tracking` | bool | true | --- | Whether the ledger maintains version history |
| `approval_required` | bool | true | --- | Whether modifications require explicit VFX supe approval |
| `history_retention` | enum | full | full, last_3, none | How many superseded entries to retain |

### Tolerance Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `variance_tolerance_creative` | float | 0.0 | 0.0 | Tolerance for creative parameters (must be exact) |
| `variance_tolerance_technical` | float | 0.02 | 0.005 - 0.05 | Default tolerance for technical parameters |
| `tolerance_override_allowed` | bool | false | --- | Whether per-parameter tolerance overrides are allowed |
| `tolerance_override_max` | float | 0.05 | 0.02 - 0.10 | Maximum tolerance for any override |

### Verification Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `verify_on_render` | bool | true | --- | Automatically verify against ledger before each render |
| `verify_on_final` | bool | true | --- | Mandatory verification during finaling |
| `fail_on_missing_entry` | bool | true | --- | Fail if a render parameter has no ledger entry |
| `fail_on_missing_shot` | bool | true | --- | Fail if a shot listed in shots_applied has no config |

---

## Presets

### Exhibition Ledger

Maximum rigor. All parameters tracked with full history. Creative parameters at zero
tolerance. Technical parameters at tight tolerance. Modification requires documented
VFX supe approval.

```yaml
ledger_path: "continuity_ledger.yaml"
ledger_version_tracking: true
approval_required: true
history_retention: full
variance_tolerance_creative: 0.0
variance_tolerance_technical: 0.01
tolerance_override_allowed: false
verify_on_render: true
verify_on_final: true
fail_on_missing_entry: true
fail_on_missing_shot: true
```

### Production Ledger

Standard production rigor. All parameters tracked. Creative parameters at zero
tolerance. Technical parameters at moderate tolerance. History retained for last 3
versions.

```yaml
ledger_path: "continuity_ledger.yaml"
ledger_version_tracking: true
approval_required: true
history_retention: last_3
variance_tolerance_creative: 0.0
variance_tolerance_technical: 0.02
tolerance_override_allowed: true
tolerance_override_max: 0.05
verify_on_render: true
verify_on_final: true
fail_on_missing_entry: true
fail_on_missing_shot: true
```

### Scout Ledger

Lightweight tracking for early creative exploration. Creative parameters tracked but
tolerance is relaxed for rapid iteration. History not retained. Verification is
advisory, not blocking.

```yaml
ledger_path: "continuity_ledger.yaml"
ledger_version_tracking: false
approval_required: false
history_retention: none
variance_tolerance_creative: 0.02
variance_tolerance_technical: 0.05
tolerance_override_allowed: true
tolerance_override_max: 0.10
verify_on_render: false
verify_on_final: true
fail_on_missing_entry: false
fail_on_missing_shot: false
```

---

## Anti-Patterns

### 1. Unlocked Parameters in Final Tier

**Symptom:** Finaling begins with parameters that have no ledger entry, or entries with
`locked_by: "agent"` or `locked_by: "auto"`. The finaling checklist passes because the
values happen to be correct at this moment, but there is no guarantee they were
intentionally chosen and no contract that they will remain consistent.

**Cause:** Rushing from lookdev to finaling without the parameter lock ceremony. The
values "look right" so the lock step is skipped. This works until shot 4 is rendered
with a slightly different auto-tuned value and the sequence has a discontinuity.

**Fix:** The finaling checklist (two-percent-rule Step 1) blocks on unlocked parameters.
There is no workaround. Return to lookdev, lock the parameters with human approval,
then restart finaling. The 5 minutes spent locking saves the hours spent debugging
drift.

### 2. Missing Ledger Entries

**Symptom:** A render parameter exists in the shot configuration but has no
corresponding entry in the continuity ledger. The parameter is effectively invisible
to the verification system. It could drift, change, or be removed without detection.

**Cause:** New parameters added to the render pipeline without updating the ledger.
The ledger was created at the start of production and not maintained as the pipeline
evolved.

**Fix:** The ledger must evolve with the pipeline. When a new parameter is added to the
render configuration, a ledger entry is created immediately --- even before the value
is finalized. The entry starts with `locked_by: "pending"` and is updated to
`locked_by: "human"` after the value is approved in review. `fail_on_missing_entry:
true` ensures the verification system catches untracked parameters.

### 3. Tolerance Greater Than Zero for Creative Parameters

**Symptom:** A creative parameter (grain amplitude, transfer function curve, crust
threshold) has a non-zero variance tolerance in the ledger. The verification system
allows shot 3 to have grain amplitude 0.05 and shot 4 to have 0.07 because both are
within the 0.03 tolerance. But the difference is visible in the sequence.

**Cause:** Misunderstanding the distinction between creative and technical parameters.
Creative parameters define the look --- they must be identical across shots because any
difference is a continuity error. Technical parameters support the look --- small
variations are acceptable if they are visually imperceptible.

**Fix:** Creative parameters have `variance_tolerance: 0.0`, always. This is not
negotiable. If a creative parameter needs to vary across shots (e.g., grain amplitude
increases as the plume grows), that variation must be explicitly specified in the ledger
as a per-shot locked value, not as a tolerance range.

### 4. Modifying the Ledger Without VFX Supe Approval

**Symptom:** An artist or agent modifies a locked value in the ledger to make a shot
"look better." The modification is not documented, not approved, and not verified
across the sequence. Three shots later, the old value and new value coexist in the
sequence, creating a discontinuity that will not be caught until the full sequence
review.

**Cause:** The ledger is treated as a configuration file that anyone can edit, rather
than as a controlled document that requires approval for changes. Write access to the
ledger is not restricted.

**Fix:** The ledger modification protocol (Step 5) is mandatory. Old values are
superseded, not deleted. New values are documented with approval reference. All
affected shots are re-rendered and the full sequence is re-reviewed. The ledger is
version-controlled and diffs are reviewed as part of the commit process. If `git diff`
shows a ledger change without a corresponding dailies note, the commit is rejected.

### 5. Stale Shot Lists

**Symptom:** A ledger entry lists `shots_applied: ["sc010", "sc020", "sc030"]` but
the sequence now contains shots sc010 through sc060. The new shots (sc040-sc060) are
not tracked by the ledger entry. Their parameters are unverified.

**Cause:** Shots added to the sequence without updating the ledger's `shots_applied`
lists. The ledger was accurate at creation but became stale as the sequence grew.

**Fix:** When a shot is added to the sequence, every relevant ledger entry's
`shots_applied` list must be updated. The `fail_on_missing_shot` flag catches the
inverse problem (shot in ledger but no config), but stale lists require proactive
maintenance. A periodic audit compares the sequence shot list against all
`shots_applied` fields to identify gaps.

---

## Validation Checklist

- [ ] Continuity ledger exists for every active sequence
- [ ] Ledger version is current (matches latest approved revision)
- [ ] All creative parameters have `variance_tolerance: 0.0`
- [ ] All creative parameters have `locked_by: "human"`
- [ ] All entries have `lock_reason` documenting the creative decision
- [ ] All entries have `shots_applied` listing every shot in the sequence
- [ ] No shots exist in the sequence without corresponding ledger coverage
- [ ] No parameters exist in render configs without corresponding ledger entries
- [ ] Verification passes: all actual values within tolerance of locked values
- [ ] No superseded entries exist without documented `superseded_reason`
- [ ] Ledger modifications follow the modification protocol (Step 5)
- [ ] Ledger is version-controlled and diffs are reviewed in commits
- [ ] No `locked_by` values of "agent", "auto", or "default" in final-tier entries
- [ ] Technical parameter tolerances do not exceed `tolerance_override_max`
- [ ] Ledger `shots_applied` lists match the current sequence shot list
