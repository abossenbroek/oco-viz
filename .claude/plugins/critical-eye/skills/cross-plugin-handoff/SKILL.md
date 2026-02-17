---
name: cross-plugin-handoff
user-invocable: false
---

# Cross-Plugin Handoff — Critical-Eye Adapter

Lightweight adapter mapping the canonical cross-plugin coordination protocol
(defined in `vfx-artist-studio/skills/production/cross-plugin-coordination`)
to the critical-eye plugin's specific inbound and outbound flows.

---

## Receiving Review Requests

Critical-eye receives review requests from any plugin via collaboration YAML
with `cross_plugin.request_type: delivery` and `to_plugin: critical-eye`.

**Accepted sources:**
| Source Plugin | Typical Artifact | Routing |
|---------------|-----------------|---------|
| cinematographer | Rendered frames, graded sequences | dp or colorist delivers |
| vfx-artist-studio | VDB volumes, composited shots | effects-td or compositor delivers |
| pipeline-expert | Governance artifacts (rare) | auteur delivers for creative review |

**On receipt:**
1. Validate the collaboration YAML has all required fields per the canonical
   protocol (`version`, `from_plugin`, `to_plugin`, `cross_plugin`)
2. Route to the appropriate critical-eye agent (critical-eye for visual review,
   art-director for gallery-context positioning)
3. Evaluate the artifact using tier-appropriate standards and the artistic
   evaluation rubric — independently, without reading the delivering agent's
   subjective commentary (independence firewall)

---

## Issuing Verdicts

Critical-eye returns verdicts in cross-plugin collaboration YAML format:

```yaml
collaboration:
  from_plugin: "critical-eye"
  from_agent: "critical-eye"
  to_plugin: "<source_plugin>"
  to_agent: "<source_agent>"
  command: "visual-verdict"
  cross_plugin:
    request_type: "verdict"
    priority: "normal"
    timeout_hours: 0
    fallback_agent: "line-producer"
  payload:
    verdict: "pass | concern | fail"
    tier: "scout | preview | final"
    critique:
      - "<specific failing aspect with measurable detail>"
    passing_aspects:
      - "<specific passing aspect>"
  next_action: "<agent>: <specific remediation directive>"
```

The `critique` field must contain actionable, specific observations — never
vague sentiment. Each critique point should name the failing aspect and the
measurable threshold it missed.

---

## Routing Feedback to the Correct Plugin

FAIL verdicts route back to the plugin that owns the failing domain:

| Failure Domain | Owning Plugin | Owning Agent |
|---------------|--------------|-------------|
| Lighting, camera, composition | cinematographer | dp |
| Color grade, LUT | cinematographer | colorist |
| Volume quality, shader, effect | vfx-artist-studio | effects-td |
| Compositing, final delivery | vfx-artist-studio | compositor |
| Governance, scope, parameter lock | pipeline-expert | auteur |

If the failure spans two plugins' domains, critical-eye issues separate
verdict YAMLs to each owning plugin with the relevant critique subset.

---

## Canonical Reference

The full cross-plugin coordination protocol, including YAML schema, routing
diagrams, conflict resolution, and anti-patterns, is defined in:

`vfx-artist-studio/skills/production/cross-plugin-coordination/SKILL.md`

This adapter does not redefine the protocol. It maps the protocol's generic
patterns to the critical-eye plugin's specific review and verdict flows.
