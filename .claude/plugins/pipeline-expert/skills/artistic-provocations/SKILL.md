---
name: artistic-provocations
user-invocable: false
owner: auteur
type: instruction
---

# Artistic Provocations — Five Core Artists as Critique Lenses

Five provocations derived from the art-historical positions of the core artists
in `standing-on-shoulders`. These are **review-time prompts**, not creation-time
constraints. They surface conversationally during relevant pipeline stages to
deepen artistic intent — never as forms, checklists, or gates.

---

## The Five Provocations

### 1. Steyerl Provocation (TF-as-Politics)

> "What does this transfer function make visible? What does it hide? Every
> opacity curve is a decision about what the viewer is forced to confront and
> what they're allowed to ignore."

Surfaces during TF review in density-to-dread discussions. When the tonalist
adjusts opacity curves, the auteur may ask what political choices those curves
encode. Creates a `tf_rationale` field in the continuity ledger — auto-populated
with the parameter choices, artist adds intent in their own words.

### 2. Atkins Provocation (Writing-First Affect)

> "Write the emotional journey of this shot in three sentences before touching
> the camera. What does the plume feel like? What does it want?"

Optional writing template available during cinematographer storyboarding. The
choreographer may offer the template; the artist is free to skip it entirely.
The point is affect-before-apparatus — words before parameters.

### 3. Cheng Provocation (Emergent Behavior)

> "Which aspect of this plume's behavior would surprise its creator? Does the
> simulation produce anything you didn't expect? If not, you haven't let the
> data speak."

Surfaces during simulation review. Maps to behavioral parameters
(`data_influence`, turbulence seed variation). The sculptor may raise this when
reviewing volume construction — are we sculpting the data or letting it sculpt
itself?

### 4. Evans Provocation (Curated Transparency)

> "What part of the making-of process would you exhibit alongside the final
> work? The git log? The agent conversations? The failed renders?"

Automated provenance: pipeline metadata (git commits, agent tool calls, render
configs) is auto-logged regardless. The provocation asks the artist to *select*
what surfaces in exhibition materials. The installer raises this during
installation planning.

### 5. Miao Provocation (Industrial Ideology)

> "Sasol Secunda is not a neutral data source — it's a coal-to-liquids
> industrial complex. How does the industrial identity of the emitter inform the
> visual language? Is the aesthetic derived from the subject's material reality
> or imposed from outside?"

Surfaces during material library and lookdev bible discussions. The auteur
raises this when establishing visual language for a new emitter source — before
the first render, not after.

---

## When to Surface

| Provocation | Pipeline Stage | Raising Agent | Receiving Agent(s) |
|-------------|---------------|---------------|---------------------|
| Steyerl | TF review / density-to-dread | auteur | tonalist |
| Atkins | Storyboarding / shot planning | choreographer | artist (human) |
| Cheng | Simulation review / volume QC | sculptor | auteur, artist |
| Evans | Installation planning / exhibition prep | installer | auteur, artist |
| Miao | Material library / lookdev bible | auteur | tonalist, sculptor |

---

## Provocation Protocol

Agents present provocations **conversationally during review**, not as structured
forms. The pattern is:

1. The raising agent encounters the relevant pipeline stage.
2. If the provocation has not been addressed for this shot/sequence, the agent
   quotes the provocation naturally in review commentary — e.g., "Steyerl would
   ask: what is this opacity curve hiding?"
3. The artist responds however they choose — a sentence, a paragraph, a shrug.
4. The response (or explicit skip) is noted in the continuity ledger.
5. No score. No gate. No follow-up enforcement.

The tone is a colleague raising an interesting question over coffee, not a
compliance officer checking a box.

---

## Not Checklists

These provocations are **not mandatory**, **not quality gates**, and **not
pass/fail criteria**. The artist is free to reject any provocation with a
one-line reason ("not relevant to this shot," "already addressed in the brief,"
or simply "no"). A rejected provocation is logged as acknowledged — it does not
block any pipeline stage or review verdict. The goal is to deepen intent, not
to police it.
