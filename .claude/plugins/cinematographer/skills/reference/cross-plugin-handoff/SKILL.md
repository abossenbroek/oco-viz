---
name: cross-plugin-handoff
user-invocable: false
type: reference
primary_owner: shared
---

# Cross-Plugin Handoff — Cinematographer Adapter

Lightweight adapter mapping the canonical cross-plugin coordination protocol
(defined in `vfx-artist-studio/skills/production/cross-plugin-coordination`)
to the cinematographer plugin's specific inbound and outbound flows.

---

## Receiving Delegation from vfx-artist-studio

When vfx-artist-studio delegates work to cinematographer (e.g., lighting rig
design, camera path, color grade), the request arrives as a collaboration YAML
with `cross_plugin.request_type: delegation` and `to_plugin: cinematographer`.

**Cinematographer responsibilities on receipt:**
1. Validate the collaboration YAML contains all required fields per the
   canonical protocol (`version`, `from_plugin`, `to_plugin`, `cross_plugin`)
2. Route to the correct cinematographer agent based on `to_agent` field
3. The receiving agent executes using its own skills and phase-template
4. Produce a delivery collaboration YAML with `cross_plugin.request_type:
   delivery` when work is complete

---

## Delivering Rendered Frames to critical-eye

When cinematographer completes rendered frames, it delivers them to
critical-eye for visual quality review.

**Delivery format:**
```yaml
collaboration:
  from_plugin: "cinematographer"
  from_agent: "dp"
  to_plugin: "critical-eye"
  to_agent: "critical-eye"
  command: "visual-review"
  cross_plugin:
    request_type: "delivery"
    priority: "normal"
    timeout_hours: 24
    fallback_agent: "line-producer"
  payload:
    artifact_path: "output/frames/<shot_id>/<tier>_v<version>"
    tier: "scout | preview | final"
    storyboard_ref: "<path to storyboard YAML>"
  next_action: "critical-eye: review rendered frames against tier standards"
```

---

## Handling Verdict Feedback from critical-eye

When critical-eye returns a verdict with `cross_plugin.request_type: verdict`:

- **PASS**: Update collaboration YAML status to `ready`. Proceed to next
  pipeline stage or deliver to vfx-artist-studio for compositing.
- **FAIL**: Read the `critique` field for specific failure reasons. The
  cinematographer agent whose domain is cited (dp for lighting/camera,
  colorist for grade) owns the remediation. Resubmission must include a
  `remediation` field mapping each critique point to the corrective action.
- **CONCERN**: Proceed but log concerns for review at next tier promotion.

---

## Canonical Reference

The full cross-plugin coordination protocol, including YAML schema, routing
diagrams, conflict resolution, and anti-patterns, is defined in:

`vfx-artist-studio/skills/production/cross-plugin-coordination/SKILL.md`

This adapter does not redefine the protocol. It maps the protocol's generic
patterns to the cinematographer plugin's specific agent roles and artifacts.
