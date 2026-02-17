---
name: pre-production-intake
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-60
  L3: lines 61-end
---

# Pre-Production Intake — Creative Direction to Production Tasks

Translates creative direction outputs (storyboards, emotional arcs, camera
grammar) into structured production task lists. The line-producer uses this
skill to bridge the gap between what the artist wants and what agents execute.

> "Pre-production is where you make your mistakes on paper instead of on
> the render farm."

---

## Principle

Creative direction is expressed in artistic language — emotional arcs, visual
metaphors, compositional intent. Production execution requires concrete tasks
with single agents, bounded files, and binary exit criteria. This skill maps
one to the other without flattening the artistic intent into pure mechanics.
The translation preserves WHY while specifying WHAT and WHO.

---

## Translation Map

### Storyboard Shots to Task-Scoping Inputs

Each shot in a storyboard delivery becomes one or more scoped tasks:

| Storyboard Element | Production Task Seed | Owning Agent |
|--------------------|---------------------|-------------|
| `camera_move` + `easing` | Camera path config at declared tier | dp (cinematographer) |
| `emotional_beat` | TF parameter target for the beat's density feel | tonalist (pipeline-expert) |
| `color_palette` | OCIO / CDL / show-LUT config | colorist (cinematographer) |
| `duration_seconds` | Frame count at project fps, sequencer timing | choreographer (pipeline-expert) |
| `narrative_intent` | Composition brief for framing and void balance | storyboarder (cinematographer) |

### Emotional Arc to TF Parameter Targets

The storyboard's `emotional_arc` (e.g., "curiosity -> recognition -> dread
-> sublime") maps to transfer function and lighting progressions:

| Emotional Phase | TF Density Emphasis | Lighting Character |
|----------------|--------------------|--------------------|
| Curiosity | Low density visible, wispy detail | Soft, directional, inviting approach |
| Recognition | Mid density structure emerges | Rim light reveals scale |
| Dread | High density dominates, oppressive | Underlit, smothered, constricted |
| Sublime | Full range, overwhelming volume | Internal emission, self-illuminated mass |

These are starting points, not prescriptions. The artist overrides freely.

### Camera Grammar to Render Config Seeds

| Camera Grammar Term | Render Config Implication |
|--------------------|--------------------------|
| Push-in | Resolution must support zoom without visible degradation |
| Orbit | Volume must read from multiple angles — lighting rig must be 360-capable |
| Static hold | Temporal detail (turbulence, emission crackle) carries the shot alone |
| Pull-back | Wide framing — void balance dominates, plume scale must command at distance |

---

## Optional Methodological Starting Points

Four methodologies from the knowledge base (`standing-on-shoulders`) offer
alternative entry points for structuring pre-production. The artist picks one,
combines several, or ignores all of them. These are lenses, not procedures.

### Systems-First (Ian Cheng)
Start from simulation behavior. Let the data's emergent properties — density
peaks, turbulence patterns, temporal rhythms — dictate the shot list. Derive
the storyboard from what the simulation does, not what the artist imagines.

### Writing-First (Ed Atkins)
Start from narrative text. Write the emotional journey of the sequence in
prose before any parameters are set. Derive visual decisions from the words.
The text is the storyboard; the render is its illustration.

### Ideology-First (Miao Ying)
Start from the subject's material reality. Sasol Secunda is a coal-to-liquids
complex — let the industrial identity of the emitter drive the aesthetic. The
visual language is derived from the subject, not imposed on it.

### Assemblage (Cecile B. Evans)
Start from available assets, tools, and pipeline capabilities. What can the
current pipeline produce well? Compose the sequence from strengths rather
than aspirations. The constraints are the creative brief.

---

## Procedure

1. **Receive** creative direction output (storyboard, emotional arc, camera
   grammar) from cinematographer or pipeline-expert
2. **Select** methodology (or none) — document the choice in the intake log
3. **Map** each storyboard element to task seeds using the translation tables
4. **Scope** each task seed using the `task-scoping` skill (single agent,
   single deliverable, binary exit criteria)
5. **Sequence** tasks by dependency — camera before lighting, lighting before
   grade, grade before review
6. **Deliver** the scoped task list as ticket YAML entries ready for
   wave-runner orchestration

---

## Validation Checklist

- [ ] Every storyboard shot has at least one corresponding scoped task
- [ ] Emotional arc phases are mapped to TF parameter targets (or explicitly skipped)
- [ ] Camera grammar terms are mapped to render config implications
- [ ] Methodology choice (or deliberate skip) is documented
- [ ] All generated tasks pass the task-scoping checklist
- [ ] Task dependencies are explicit and acyclic
- [ ] No artistic intent was lost in translation — creative direction traceable in tasks
