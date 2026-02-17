---
name: human-agent-boundary
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Human-Agent Boundary

Defines what the human decides versus what agents execute. This boundary
is explicit, non-negotiable, and applies to every interaction in the
pipeline. When in doubt, the answer is always: surface options to the
human, never decide.

> "The director decides what the film is about. Everyone else decides how
> to make it." -- every film crew handbook ever written

---

## Principle

The human is the creative director. Agents are the crew. The director
chooses the destination; the crew builds the road. This division is not a
matter of convenience or capability -- it is a governance principle that
ensures creative accountability rests with a human being, not with a
stochastic process.

Agents excel at execution: they can generate thousands of parameter
variations, run quality gates in seconds, and maintain perfect consistency
across a 200-shot pipeline. But they cannot decide whether the plume
should evoke dread or wonder. They cannot decide whether to cut a feature
to meet a deadline. They cannot decide whether the exhibition should
prioritize scientific accuracy or emotional impact. These are human
decisions, and no amount of agent sophistication changes that.

The boundary is a firewall, not a gradient. There is no gray zone where
agents "mostly decide but check with the human." Either the human decides,
or the agent executes. When the boundary is ambiguous, the agent escalates.

---

## Procedure

### Step 1 -- Classify the Decision

Every decision or action in the pipeline falls into exactly one of two
categories. There is no third category.

#### Human Decisions

The human decides. Agents surface options, generate wedges, and present
data -- but the human makes the call.

| Decision Domain | Examples | Why Human |
|----------------|---------|-----------|
| **Creative direction approval** | "The plume should feel ominous, not beautiful" | Artistic intent cannot be computed |
| **Scope cuts** | "Defer exhibition lookdev to Wave 13" | Business trade-off with timeline implications |
| **Timeline trade-offs** | "Ship scout quality by March, not preview quality" | Risk tolerance is a human judgment |
| **Parameter locks** | "Lock color temperature at 3200K for this show" | Creative commitment from contact sheet review |
| **Exhibition space decisions** | "Gallery wall 3, printed at 60x40 inches" | Physical space is outside the digital pipeline |
| **Emotional arc approval** | "The sequence arc is curiosity -> dread -> sublime" | Emotional design is a directorial choice |
| **Conflict resolution (creative)** | "Lighting warmth wins over color science accuracy" | When two valid approaches conflict, the director chooses |
| **Risk acceptance** | "Accept visual debt on this shot to meet deadline" | Conscious quality trade-off |
| **Phase gate approval** | "Phase 2 is complete, proceed to Phase 3" | Milestone sign-off requires human authority |
| **Partner/stakeholder commitments** | "We will deliver 12 shots, not 20" | External commitments bind the project |

#### Agent Execution

Agents execute. They do not seek approval for these actions unless they
encounter an ambiguity that prevents execution.

| Execution Domain | Examples | Why Agent |
|-----------------|---------|-----------|
| **Code implementation** | Write Python, author HDAs, build shaders | Mechanical translation of spec to code |
| **Quality gate execution** | Run `pixi run check`, `pixi run ci` | Deterministic pass/fail evaluation |
| **Wedge generation** | Produce 50 parameter variations for contact sheet | Mechanical parameter sweep |
| **Format conversion** | VDB export, USD assembly, EXR rendering | Pipeline plumbing with no creative decision |
| **Status tracking** | Update ticket YAML, burndown, velocity | Bookkeeping |
| **Gate checking** | Validate collaboration YAML, schema conformance | Protocol enforcement |
| **Artifact generation** | Gallery images, preview renders, scout passes | Execution of locked creative parameters |
| **Dependency resolution** | Install packages, configure environments | Infrastructure maintenance |
| **Test execution** | Run pytest, validate results | Deterministic verification |
| **Debt tracking** | Count and classify technical debt items | Inventory management |

### Step 2 -- Handle Ambiguity

When an agent encounters a situation that does not clearly fall into the
execution domain, it MUST escalate to the human. The escalation format is:

```yaml
escalation:
  agent: string              # agent encountering the ambiguity
  plugin: string             # plugin the agent belongs to
  ticket: string             # ticket being worked (if applicable)
  situation: string          # what happened
  options:                   # 2-4 options, each with trade-offs
    - option: string
      trade_off: string
      recommendation: string # "recommended" or "not recommended"
  blocking: bool             # true if work cannot continue without decision
  context:                   # supporting data for the human
    - type: string           # "image" | "metric" | "config" | "log"
      path: string           # path to supporting artifact
```

**Rules for escalation**:
- Present 2-4 concrete options, never an open-ended question
- Each option must include its trade-off
- The agent may indicate a recommendation but must not act on it
- If blocking, the agent stops work on this task and moves to another
- The human's response is recorded in the ticket YAML as a decision

### Step 3 -- Record the Decision

Every human decision is recorded so agents can reference it later without
re-escalating.

```yaml
decision:
  id: string                 # unique decision ID (e.g., D-2026-02-15-001)
  date: ISO8601
  domain: string             # which decision domain (from the table above)
  decision: string           # what was decided
  rationale: string          # why (optional but valuable)
  applies_to:                # scope of the decision
    - scope: string          # "project" | "phase" | "wave" | "shot" | "ticket"
      id: string             # specific scope ID
  supersedes: string         # previous decision ID if this overrides one
```

Decisions with `scope: project` apply globally until superseded. Decisions
with `scope: shot` apply only to the named shot.

---

## The Firewall in Practice

### Contact Sheet Workflow

The contact sheet is the primary mechanism for parameter locking.

1. **Agent generates**: 50 wedge variations (mechanical execution)
2. **Human reviews**: Contact sheet printed or displayed at full resolution
3. **Human selects**: "Row 3, Column 7 -- lock these parameters"
4. **Agent records**: Parameter lock decision in YAML
5. **Agent executes**: All subsequent renders use locked parameters

The human never tunes individual parameters. The agent never selects the
winning wedge.

### Scope Cut Workflow

1. **Agent reports**: Velocity data shows timeline risk
2. **Agent presents**: 3 scope-cut options with trade-offs
3. **Human decides**: "Cut option B -- defer exhibition lookdev"
4. **Agent records**: Decision and updates ticket statuses
5. **Agent executes**: Deferred tickets move to later wave

The human never updates ticket YAML directly. The agent never decides
which features to cut.

### Visual Quality Workflow

1. **Agent renders**: Gallery images using locked parameters
2. **Critical-eye agent judges**: Pass/fail per image (mechanical
   evaluation against criteria)
3. **Human reviews**: Final approval of passing images for exhibition
4. **Agent records**: Approval decision

Critical-eye's judgment is mechanical (criteria-based), not creative. The
human's final approval is creative (exhibition-worthiness). These are
different domains and must not be conflated.

---

## Anti-Patterns

### 1. Agent Deciding Creatively

**Symptom**: An agent selects the "best looking" wedge from a contact
sheet and locks the parameters without human review. The rendering looks
fine, but the creative direction was not approved by the director.

**Cause**: The agent conflated "technically optimal" with "creatively
correct." A technically perfect image can be creatively wrong -- the plume
looks beautiful when it should look ominous.

**Fix**: Agents generate. Humans select. No exceptions. If the contact
sheet workflow is too slow, reduce the wedge count -- do not skip human
selection.

### 2. Human Micromanaging Implementation

**Symptom**: The human specifies exact Python code changes, specific VTK
parameter values, or precise pixel coordinates for camera placement. The
agent becomes a typist rather than a skilled crew member.

**Cause**: The human does not trust the agent's implementation skills, or
the human enjoys the implementation details more than the creative
direction.

**Fix**: The human specifies the "what" and "why." The agent determines
the "how." If the human has implementation preferences, they are expressed
as constraints in the task scope ("camera must be at least 500m from plume
center"), not as code ("set camera.position = (500, 200, 0)").

### 3. Boundary Drift

**Symptom**: Over time, agents begin making small creative decisions
("this color temperature looks right") and humans begin executing small
implementation tasks ("I'll just fix this import myself"). The boundary
erodes incrementally until no one is sure who owns what.

**Cause**: Convenience. Small boundary violations feel harmless in the
moment. But they accumulate into a state where creative decisions are
untracked (because agents made them implicitly) and implementation is
inconsistent (because humans bypassed the quality gates).

**Fix**: The boundary is reviewed at every monthly Braintrust. Any
decision made by an agent that should have been human is flagged and
recorded. Any implementation done by a human that should have been agent
is noted (no blame, but awareness). The boundary is a living document,
not a one-time definition -- but changes to it are themselves human
decisions.

### 4. The False Escalation

**Symptom**: An agent escalates every trivial implementation decision to
the human. "Should I use a for loop or list comprehension?" "Should the
variable be named `plume_data` or `volume_data`?" The human is overwhelmed
with decisions that do not require creative judgment.

**Cause**: The agent's escalation threshold is miscalibrated. It is
escalating implementation details rather than genuine ambiguities.

**Fix**: Escalation is for decisions that cross the boundary -- creative
direction, scope, timeline, parameter locks. Implementation details are
agent execution domain. If the agent is unsure whether a decision is
creative or implementation, the test is: "Would a different choice change
what the viewer feels?" If yes, escalate. If no, execute.

### 5. The Undocumented Decision

**Symptom**: The human makes a creative decision verbally or in an
unstructured chat message. The agent acts on it, but no decision YAML is
recorded. Three weeks later, a different agent makes a contradictory
choice because the original decision is invisible.

**Cause**: Decision recording feels like overhead. The decision was clear
in the moment.

**Fix**: Every human decision gets a decision YAML entry. The entry is
short (4-5 fields). The cost is 30 seconds. The cost of not recording is
a contradictory decision that wastes hours or days to untangle.

---

## Validation Checklist

- [ ] No agent has made a creative direction decision without human approval
- [ ] No human has directly modified code without going through an agent task
- [ ] All parameter locks trace to a human decision (contact sheet selection)
- [ ] All scope cuts trace to a human decision with recorded trade-offs
- [ ] Escalations present 2-4 concrete options with trade-offs
- [ ] Escalations do not include open-ended questions
- [ ] Decisions are recorded in YAML with unique IDs
- [ ] Decision scope is explicit (project / phase / wave / shot / ticket)
- [ ] Boundary is reviewed at monthly Braintrust
- [ ] No boundary drift detected (agents decide only execution, humans decide only direction)
- [ ] Contact sheet workflow followed for all parameter locks
- [ ] Critical-eye verdicts are mechanical; exhibition approval is human
