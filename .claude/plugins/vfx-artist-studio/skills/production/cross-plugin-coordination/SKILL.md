---
name: cross-plugin-coordination
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Cross-Plugin Coordination

Maps the full pipeline handoff chain across all five plugins. Each plugin
owns a distinct domain; handoffs between them flow through structured
collaboration YAML documents. No plugin reaches into another plugin's
domain. No agent acts outside its plugin's boundary without an explicit
cross-plugin request.

```
pipeline-expert (thinks) -> vfx-artist-studio (crafts + codes + plans) -> cinematographer (shoots) -> critical-eye (judges)
wave-runner (orchestrates tickets across all of the above)
```

---

## Principle

The five-plugin architecture exists to enforce separation of concerns at
the creative-technical boundary. Each plugin has a clear domain, a defined
set of agents, and a bounded set of artifacts it produces. Cross-plugin
communication flows through collaboration YAML documents that carry
objective, measurable data -- never subjective opinion. The line-producer
in vfx-artist-studio is the primary coordinator, but wave-runner holds
the master schedule.

When two plugins disagree (e.g., critical-eye rejects what cinematographer
delivered), the resolution flows through the collaboration protocol, not
through informal negotiation. The protocol is the law.

---

## Procedure

### Step 1 -- Understand Plugin Boundaries

Each plugin owns a domain. Work that falls outside a plugin's domain must
be delegated via cross-plugin request.

| Plugin | Domain | Owns | Does NOT Own |
|--------|--------|------|-------------|
| **pipeline-expert** | Governance, architecture, creative direction | Phase plans, coding guide, parameter locks, scope decisions | Implementation, rendering, visual judgment |
| **vfx-artist-studio** | Effects artistry, Houdini/Karma coding, production planning | Shaders, volumes, HDAs, compositing, scheduling, task scoping | Camera work, shot composition, visual verdict |
| **cinematographer** | Shot design, lighting, color science, camera | Lighting rigs, camera paths, color grades, storyboards, visual bible | Effects implementation, production scheduling, governance |
| **critical-eye** | Visual quality judgment | Pass/fail verdicts, visual regression detection, quality metrics | Implementation fixes, parameter tuning, creative direction |
| **wave-runner** | Ticket orchestration, quality gate execution | Ticket status, gate results, wave progress, CI automation | Creative decisions, implementation, visual judgment |

### Step 2 -- Identify Handoff Type

All cross-plugin interactions fall into one of these patterns:

| Pattern | Flow | Example |
|---------|------|---------|
| **Delegation** | Plugin A requests Plugin B to perform work | vfx-artist-studio asks cinematographer to design lighting rig |
| **Delivery** | Plugin A sends completed artifact to Plugin B | cinematographer delivers graded frames to critical-eye for review |
| **Escalation** | Plugin A cannot resolve an issue and escalates up | cinematographer escalates a governance question to pipeline-expert |
| **Verdict** | Plugin A returns a judgment to Plugin B | critical-eye returns pass/fail verdict to cinematographer |
| **Orchestration** | wave-runner triggers work in any plugin | wave-runner fires a ticket that requires vfx-artist-studio agent |

### Step 3 -- Format the Cross-Plugin Request

Cross-plugin requests extend the collaboration YAML protocol with
additional routing fields:

```yaml
collaboration:
  version: "1.0"
  from_agent: string         # agent in source plugin
  from_plugin: string        # source plugin name
  to_agent: string           # agent in target plugin
  to_plugin: string          # target plugin name
  command: string            # action requested
  tier: string               # scout | preview | final
  timestamp: ISO8601
  status: string             # ready | pending_approval | blocked | superseded
  payload: object            # delivery-specific content
  audit_trail: string        # provenance chain
  next_action: string        # directive for target agent
  cross_plugin:              # extension block for cross-plugin routing
    request_type: string     # delegation | delivery | escalation | verdict
    priority: string         # normal | urgent | blocking
    timeout_hours: int       # max hours before escalation
    fallback_agent: string   # agent to notify if timeout expires
```

### Step 4 -- Route Through the Pipeline Chain

The canonical pipeline flow is linear with feedback loops:

```
                    +-----------+
                    | wave-     |
                    | runner    |  (orchestrates)
                    +-----+-----+
                          |
                          v
              +-----------+-----------+
              |                       |
     +--------v--------+   +---------v--------+
     | pipeline-expert  |   | vfx-artist-      |
     | (governance)     |   | studio (craft)   |
     +--------+---------+   +---------+--------+
              |                       |
              | param locks,          | volumes, shaders,
              | phase plans           | HDAs, comps
              |                       |
              v                       v
         +----+-----------------------+----+
         |       cinematographer            |
         |  (lighting, camera, color)       |
         +----+----------------------------+
              |
              | rendered frames
              v
         +----+----------------------------+
         |       critical-eye               |
         |  (visual judgment)               |
         +----+----------------------------+
              |
              | verdict (pass/fail)
              v
         feedback loop -> cinematographer or vfx-artist-studio
```

**Feedback loops**: When critical-eye returns a FAIL verdict, the feedback
routes to the plugin that owns the failing aspect:
- Lighting/camera fail -> cinematographer
- Volume/shader/effect fail -> vfx-artist-studio
- Governance/scope fail -> pipeline-expert (via escalation)

### Step 5 -- Resolve Conflicts

When two plugins produce contradictory outputs (e.g., cinematographer's
lighting rig conflicts with vfx-artist-studio's shader assumptions):

1. **Identify conflict**: Document both positions in collaboration YAML
2. **Determine domain owner**: The plugin whose domain the conflict falls
   in has authority (lighting conflicts -> cinematographer owns)
3. **If domain is ambiguous**: Escalate to pipeline-expert for governance
   ruling
4. **Apply resolution**: The losing side adapts its output to match the
   ruling
5. **Document**: Record the resolution in the collaboration YAML
   `audit_trail`

---

## Coordination Patterns

### Delegation

Plugin A needs work done that falls in Plugin B's domain.

```yaml
# vfx-artist-studio -> cinematographer
collaboration:
  from_plugin: "vfx-artist-studio"
  from_agent: "effects-td"
  to_plugin: "cinematographer"
  to_agent: "dp"
  command: "design-lighting-rig"
  cross_plugin:
    request_type: "delegation"
    priority: "normal"
    timeout_hours: 48
    fallback_agent: "line-producer"
  payload:
    context: "New soot-crust shader requires specific rim lighting angle"
    constraints:
      - "Key light must come from below (furnace motivation)"
      - "No fill light (Soot tier)"
  next_action: "dp: design lighting rig for soot-crust shader"
```

### Escalation

An agent encounters a decision that exceeds its authority.

```yaml
# cinematographer -> pipeline-expert
collaboration:
  from_plugin: "cinematographer"
  from_agent: "dp"
  to_plugin: "pipeline-expert"
  to_agent: "auteur"
  command: "governance-ruling"
  cross_plugin:
    request_type: "escalation"
    priority: "urgent"
    timeout_hours: 24
    fallback_agent: "line-producer"
  payload:
    issue: "Color temperature locked at 3200K by parameter lock, but
            storyboard calls for 5600K twilight palette"
    options:
      - "Override parameter lock (requires auteur approval)"
      - "Revise storyboard palette to match lock"
    recommendation: "Override — creative intent should drive parameter"
  next_action: "auteur: rule on parameter lock vs. creative intent conflict"
```

### Verdict

critical-eye returns judgment on rendered output.

```yaml
# critical-eye -> cinematographer
collaboration:
  from_plugin: "critical-eye"
  from_agent: "critical-eye"
  to_plugin: "cinematographer"
  to_agent: "dp"
  command: "visual-verdict"
  cross_plugin:
    request_type: "verdict"
    priority: "normal"
    timeout_hours: 0  # verdicts are immediate
    fallback_agent: "line-producer"
  payload:
    verdict: "fail"
    shot_id: "SH010"
    tier: "preview"
    critique:
      - "Plume edges clip to hard boundary — no wispy halo"
      - "Lighting is flat — no directional depth"
    passing_aspects:
      - "Color temperature is within specification"
      - "Background is pure black"
  next_action: "dp: address edge clipping and lighting directionality"
```

---

## Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `handoff_timeout_hours` | int | 48 | 12 - 168 | Hours before unacknowledged request escalates |
| `urgent_timeout_hours` | int | 24 | 4 - 48 | Hours before urgent request escalates |
| `blocking_timeout_hours` | int | 4 | 1 - 12 | Hours before blocking request escalates |
| `conflict_escalation_threshold` | int | 2 | 1 - 3 | Failed resolution attempts before pipeline-expert escalation |
| `max_delegation_depth` | int | 2 | 1 - 3 | Max plugin hops for a single request (prevents circular routing) |

---

## Anti-Patterns

### 1. Plugin Boundary Violation

**Symptom**: An effects-td agent in vfx-artist-studio directly modifies a
lighting rig YAML that belongs to the cinematographer plugin. The change
works, but it bypasses the DP agent's authority over lighting decisions.

**Cause**: The agent optimized for speed over protocol. Modifying the file
directly is faster than sending a cross-plugin delegation request.

**Fix**: Enforce the boundary. If an agent needs an artifact changed in
another plugin's domain, it sends a delegation request. The owning plugin
makes the change. The collaboration YAML is the proof that the change was
authorized.

### 2. Implicit Handoff

**Symptom**: An agent places a file in a shared directory and expects
another plugin's agent to notice it. No collaboration YAML is produced.
The receiving agent may or may not pick it up, depending on when it next
scans the directory.

**Cause**: File-system convention substituted for explicit protocol. This
works in small teams but fails at scale and is invisible to production
tracking.

**Fix**: Every handoff produces a collaboration YAML. If there is no YAML,
there was no handoff. The file in the shared directory is an artifact; the
YAML is the contract that says "this artifact is ready for you."

### 3. Circular Delegation

**Symptom**: Plugin A delegates to Plugin B, which delegates back to
Plugin A with slightly different framing. The request bounces indefinitely,
consuming context windows without producing output.

**Cause**: Ambiguous domain ownership. Neither plugin is sure the work
belongs to the other, so they pass it back and forth.

**Fix**: The `max_delegation_depth` parameter limits hops. If a request
reaches the depth limit, it automatically escalates to pipeline-expert
for a domain-ownership ruling. The ruling is recorded and applies to all
future requests of the same type.

### 4. Verdict Shopping

**Symptom**: After critical-eye returns a FAIL verdict, the owning agent
tweaks the output minimally and resubmits, hoping for a different verdict.
No root-cause investigation is performed between submissions.

**Cause**: The agent treats the verdict as an obstacle rather than
diagnostic information. The critique section of the verdict YAML tells the
agent exactly what failed, but the agent does not read it.

**Fix**: Resubmission after a FAIL verdict requires evidence that the
critique was addressed. The resubmission collaboration YAML must include a
`remediation` field listing what changed and why, mapped to each critique
point from the original verdict.

### 5. Wave-Runner Bypass

**Symptom**: Agents coordinate directly between plugins without routing
through the ticket system. Work gets done but is invisible to wave-runner,
so burndown and velocity metrics are wrong.

**Cause**: The ticket overhead feels unnecessary for "small" coordination
tasks. But production tracking depends on all work being ticket-visible.

**Fix**: Every cross-plugin interaction that produces or modifies an
artifact must be associated with a ticket. If no ticket exists, the
line-producer creates one before the interaction begins. Ad-hoc
coordination without tickets is a production violation.

---

## Validation Checklist

- [ ] Every cross-plugin request has a collaboration YAML with `cross_plugin` block
- [ ] `from_plugin` and `to_plugin` are different (same-plugin requests use standard collaboration)
- [ ] `request_type` is one of: delegation, delivery, escalation, verdict
- [ ] `timeout_hours` is set and appropriate for `priority` level
- [ ] `fallback_agent` is specified for timeout escalation
- [ ] No agent modifies artifacts outside its plugin's domain
- [ ] Delegation depth does not exceed `max_delegation_depth`
- [ ] FAIL verdicts include critique details and trigger root-cause investigation
- [ ] Resubmissions after FAIL include `remediation` field
- [ ] All cross-plugin work is associated with a ticket in wave-runner
- [ ] Conflict resolutions are documented in `audit_trail`
