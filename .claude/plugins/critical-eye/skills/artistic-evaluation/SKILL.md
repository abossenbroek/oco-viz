---
name: artistic-evaluation
user-invocable: false
---

# Artistic Evaluation Rubric

Five categories with tier-specific weights. Used by the art-director agent.

---

## Categories

### 1. Emotional Register

Does this image provoke a response? Is there dread, weight, confrontation? Or is it merely technical, merely correct, merely decorative?

**What to look for:**
- Visceral response on first viewing — before analysis kicks in
- Industrial oppression — the weight of combustion residue
- Dread — not horror, but the slow recognition of something wrong
- Confrontation — the image does not allow passive viewing

**What fails:**
- Pretty for its own sake
- Comfortable to look at
- Elicits "cool" rather than "heavy"
- No emotional response at all

### 2. Material Presence

Does the substance feel real? Can you sense its weight, its texture, its toxicity? Or does it read as digital, as simulated, as an effect?

**What to look for:**
- Physical conviction — you believe this material exists
- Texture at multiple scales — granular, not smooth
- Weight — it feels like it would settle, not float
- Materiality — coal dust, volcanic ash, charcoal, not CGI

**What fails:**
- Reads as "smoke effect" or "particle system"
- Glassy, smooth, digital feeling
- No texture or material character
- Feels weightless or ethereal

### 3. Compositional Authority

Does the frame command attention? Is there tension in the placement? Does the void serve the mass?

**What to look for:**
- Deliberate placement — the mass is positioned, not defaulted
- Tension between substance and void
- Vertical emphasis suggesting rising emissions
- Asymmetry creating unease
- The void is as intentional as the substance

**What fails:**
- Centered, symmetrical, "safe" composition
- Plume floating in space without compositional intent
- Void as leftover, not as active element
- No spatial tension

### 4. Chromatic Discipline

Is the palette serving the concept? Is the achromatic range purposeful? Or has color crept in?

**What to look for:**
- Purposeful use of the greyscale — each tonal value doing work
- Rich grey range — not flat, not uniform
- Discipline — the achromatic constraint feels chosen, not limiting
- Peak brightness that communicates contamination (dirty near-white)

**What fails:**
- Color contamination (any visible hue)
- Dead grey — no tonal richness
- Pure white (clean, not contaminated)
- Flat, uniform brightness

### 5. Void Quality

Is the black active or inert? Does the void have presence? Does the boundary between substance and nothing create a threshold?

**What to look for:**
- Active void — the black feels like a space, not an absence
- Threshold quality — the boundary between plume and void is a place, not just an edge
- Projection readiness — at gallery scale, the void becomes the room
- The void has as much presence as the substance

**What fails:**
- Inert background — just blank space around the subject
- No threshold sensation — the edge is just technical
- Void contaminated with noise, gradients, or haze (at exhibition tier)
- The black feels accidental rather than intentional

---

## Tier Weights

| Category | Exhibition | Study | Sketch |
|----------|-----------|-------|--------|
| Emotional Register | 30% | 15% | 0% |
| Material Presence | 25% | 20% | 0% |
| Compositional Authority | 20% | 10% | 50% |
| Chromatic Discipline | 15% | 15% | 0% |
| Void Quality | 10% | 5% | 50% |

**Sketch note:** At sketch tier, "Compositional Authority" reduces to "is the plume in frame?" and "Void Quality" reduces to "is the background not corrupted?" Scores are binary (0 or 10).

---

## Scoring Scale (0-10)

| Score | Level | Meaning |
|-------|-------|---------|
| 9-10 | Exceptional | Gallery-ready without reservation |
| 7-8 | Strong | Achieves intent, minor refinements possible |
| 5-6 | Developing | Direction right, execution needs work |
| 3-4 | Weak | Conceptual problems, not just technical |
| 1-2 | Failed | Does not serve artistic intent |
| 0 | Absent | Category requirements completely unmet |

---

## Verdict Thresholds

Calculated from weighted category scores:

| Verdict | Weighted Score | Meaning |
|---------|---------------|---------|
| **pass** | >= 8.0 | Ready for its context |
| **conditional_pass** | >= 6.0 | Acceptable with noted improvements |
| **revise** | >= 4.0 | Core concept sound, execution needs significant work |
| **fail** | < 4.0 | Not achieving artistic goals |

---

## Direction Notes

For any category scoring below 8, provide a direction note:

```yaml
direction:
  - priority: high | medium | low
    category: "category_name"
    note: "Persona-voiced guidance on what to address"
```

Priority mapping:
- **high**: Category below 5 — fundamental issue
- **medium**: Category 5-6 — clear improvement needed
- **low**: Category 7 — refinement opportunity

---

## Heuristic Lenses

Six design heuristics derived from the core artists (see `standing-on-shoulders`
skill). The art-director uses these as **evaluation lenses** during exhibition-tier
review — asking which heuristic(s) the shot *engages with*, not which it *satisfies*.

| Heuristic | Review Question |
|-----------|----------------|
| **Friction** (Atkins) | Does this shot expose its own artifice, or does seamless immersion risk complicity with spectacle? |
| **Shepherd** (Cheng / Miao) | Is there emergent behavior the artist did not fully control, held within conceptual guardrails? |
| **Transcoding** (Evans) | Does any production infrastructure — process, metadata, labor — surface as a formal element? |
| **Poor Image** (Steyerl) | Does the work resist resolution fetishism, or is technical fidelity mistaken for criticality? |
| **Ambient** (Cheng) | Does the shot sustain engagement across time scales — rewarding both the glance and the long gaze? |
| **Counterfeit** (Miao) | Does the work deploy official or institutional aesthetics at full fidelity to expose emptiness beneath? |

### How to Use

The art-director asks: **"Which heuristic(s) does this shot engage with, if any?"**

- The artist may name one or more heuristics and briefly describe the engagement.
- The artist may declare **"None — this shot operates outside the heuristic framework"**
  and that is a valid, complete answer.
- Heuristic engagement is an **evaluation lens**, not a pass/fail criterion. It informs
  the gallery-context positioning in Phase 4 of the review but does not affect scores
  or verdicts.
