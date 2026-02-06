---
name: ideation
user-invocable: false
---

# Ideation Protocol — Creative Dialectic

A formalized four-phase dialectic between systematic analysis and divergent
provocation. The protocol generates creative direction through structured
tension between scientific ground truth and radical artistic interpretation.

---

## Phase 1: ANALYSIS (Claude — The Scientist)

The Auteur provides intent. Claude establishes Ground Truth.

**Process:**
- Statistical analysis of the data: histograms, density distributions, spatial gradients
- Technical canvas assessment: grid resolution, temporal range, variable bounds
- Linear interpretation: what the data literally shows, stripped of artistic intent
- Constraint mapping: physical limits, rendering boundaries, tier requirements

**Output:** A factual brief — "Here are the facts of the data."

**Tool:** Standard Claude analysis capabilities (Read, Bash for data inspection).

---

## Phase 2: PROVOCATION (Gemini — The Artist)

Receives Ground Truth and intentionally diverges. The Artist's role is to
shatter literal interpretation and propose radical reframings.

**Process:**
- Review the Ground Truth from Phase 1
- Propose 3-5 Artistic Theses that deliberately depart from literal reading
- Each thesis must reference art history, material practice, or perceptual theory
- Each thesis must be technically possible (radical, not impossible)

**Example Theses:**
- "Treat density as viscosity — lowest values = highest detail = palpable tension"
- "Francis Bacon lighting — trapped light source smothered by the volume"
- "Invert the TF — void becomes subject, CO2 carves negative space"
- "Geological time — compress 10,000 years of carbon into 60 seconds of accumulation"
- "The plume as wound — emission source as puncture, CO2 as hemorrhage"
- "Rothko fields — density bands as color field boundaries, meditative dread"
- "Beckett staging — single source, theatrical isolation, existential volume"

**Tool:** `mcp__pal__chat` with `model: gemini-2.5-pro`

**Prompt pattern:**
```
You are The Artist in a creative dialectic. Given this Ground Truth about
the data: [ground_truth]. The artistic intent is: [intent]. Propose 3-5
radical artistic theses that intentionally diverge from literal
interpretation. Be bold, reference art history, push beyond comfortable
interpretation. Each thesis should name: the concept, the art-historical
reference, the specific technical implication for volumetric rendering,
and the emotional target.
```

---

## Phase 3: SYNTHESIS (Auteur — The Director)

The Auteur reviews all Theses against Ground Truth. Does NOT simply pick
one — synthesizes across theses to create a unified creative direction.

**Process:**
- Evaluate each thesis for artistic conviction and technical feasibility
- Identify complementary elements across theses
- Resolve contradictions (e.g., maximal density vs. negative space)
- Produce the Director's Brief with specific directives per agent

**Director's Brief contains:**
- **Sculptor directive** — material quality, turbulence character, edge treatment
- **Tonalist directive** — density-to-luminance mapping, color temperature within achromatic
- **Choreographer directive** — temporal arc, camera intent, pacing

**Output:** `ideation_result` schema from output-schemas.

---

## Phase 4: EXECUTION (Claude — The Technician)

Translates the Director's Brief into concrete parameters and code.

**Process:**
- Convert artistic directives into VTK parameters, transfer function points, camera paths
- Respect technical boundaries established in Phase 1
- Produce specific parameter sets or code snippets
- Flag any directive that cannot be achieved within current pipeline capabilities

**Output:** Parameter dictionaries, code snippets, config YAML fragments.

---

## Protocol Rules

1. **Phase order is strict.** No phase may begin before the previous phase completes.
2. **Ground Truth is sacred.** Phase 2 may reinterpret but never falsify the data.
3. **Theses are disposable.** Not every provocation survives synthesis. That is the point.
4. **The Auteur has final authority.** Phase 3 synthesis is not democratic.
5. **Execution respects physics.** Phase 4 may push back on Phase 3 if a directive
   violates physical constraints — the Auteur decides whether to modify or override.
6. **Audit trail required.** Every parameter in Phase 4 must trace back through
   synthesis -> thesis -> ground truth -> data source.

---

## When to Invoke

- Beginning a new scene or sequence (full protocol)
- Significant change in data characteristics (Phases 1-3, then incremental Phase 4)
- Creative block or stagnation (Phase 2 only — fresh provocations)
- Technical discovery that changes the canvas (Phase 1 refresh, then cascade)
