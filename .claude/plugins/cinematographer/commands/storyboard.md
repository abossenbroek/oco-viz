---
name: storyboard
description: Generate shot sequence with emotional arc, camera grammar, palettes
user-invocable: true
---

# Storyboard Command

Generate a shot sequence with emotional arc, camera grammar, and palette
assignments from a creative brief. The storyboarder agent designs the
emotional experience; downstream agents execute it.

## Usage

```
/cinematographer:storyboard "creative brief or scene description"
```

## Arguments

- `"creative brief"`: Description of the scene, subject, or emotional intent

## Agent Flow

1. Load the storyboarder agent from `.claude/plugins/cinematographer/agents/storyboarder.md`
2. Storyboarder loads exclusive skills: `shot-grammar`, `sequence-design`, `color-palette`
3. Storyboarder processes brief through 4-phase template (CONTEXT → EXECUTE → VALIDATE → DELIVER)
4. Storyboarder produces collaboration YAML with `storyboard_delivery` payload

## Output

Collaboration YAML with `storyboard_delivery` payload:
- `creative_brief` — the original brief
- `shots` — array of shot specs (shot_id, duration_seconds, camera_move, easing, emotional_beat, color_palette, narrative_intent)
- `emotional_arc` — three-act emotional structure
- `timing_map` — beat-to-timecode mapping

## Next Action

The collaboration YAML suggests:
- `/cinematographer:lookdev` — to create visual bible, lighting rig, and color pipeline
- `/cinematographer:shoot` — if lookdev is already complete

## Examples

```
/cinematographer:storyboard "Australian bushfire CO2 plume — confrontation with industrial emission, geological dread"
/cinematographer:storyboard "Secunda coal plant — 90-second sequence, building from distant observation to intimate immersion"
/cinematographer:storyboard "Volcanic ash dispersion over Pacific — scale and insignificance"
```

$ARGUMENTS parsed as creative brief string.
