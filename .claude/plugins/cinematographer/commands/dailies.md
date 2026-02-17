---
name: dailies
description: Review in the cut — sequence review with critical-eye delegation
user-invocable: true
---

# Dailies Command

Review in the cut — the dp agent reviews shots in sequence context, applying
John Nelson's principle of never evaluating a shot in isolation. Produces
review notes and delegates to critical-eye for independent visual QA.

## Usage

```
/cinematographer:dailies <shot-ids|sequence-id>
```

## Arguments

- `<shot-ids|sequence-id>`: Comma-separated shot IDs or sequence identifier

## Agent Flow

1. Load the dp agent from `.claude/plugins/cinematographer/agents/dp.md`
2. dp loads skill: `review-in-the-cut` (primary), plus standard skills
3. dp assembles the sequence from specified shots
4. dp reviews in sequence context:
   - Temporal continuity across shots
   - Lighting consistency across sequence
   - Emotional pacing and arc fulfillment
   - Camera motion coherence
5. dp produces `dailies_delivery` collaboration YAML

## Output

Collaboration YAML with `dailies_delivery` payload:
- Sequence review with per-shot notes
- Temporal continuity assessment
- Lighting consistency check
- Emotional pacing evaluation
- Frame-by-frame annotations where needed

## Next Action

The collaboration YAML suggests:
- `/critical-eye:review` — for independent VFX + artistic QA
- Specific re-render requests for shots that fail review

## Examples

```
/cinematographer:dailies shot_001,shot_002,shot_003
/cinematographer:dailies opening_sequence
/cinematographer:dailies hero_sequence
```

$ARGUMENTS parsed as shot IDs or sequence identifier.
