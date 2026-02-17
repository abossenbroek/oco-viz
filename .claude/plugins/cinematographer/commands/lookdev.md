---
name: lookdev
description: Vermette-method visual bible session with material presets and color keys
user-invocable: true
---

# Lookdev Command

Multi-agent look development session. Three agents execute sequentially,
communicating via collaboration YAML. Produces visual bible, lighting rig,
and color pipeline configuration.

## Usage

```
/cinematographer:lookdev "subject" [--tier scout|preview|final]
```

## Arguments

- `"subject"`: Description of the subject or scene for look development
- `--tier`: Quality tier (default: preview). Controls keyframe count, resolution, and validation strictness.

## Agent Flow

Sequential execution — each agent reads the previous agent's collaboration YAML:

1. **production-designer** loads from `.claude/plugins/cinematographer/agents/production-designer.md`
   - Loads skills: `vermette-bible`, `visual-bible-protocol`, `material-library`
   - Produces `visual_bible_delivery` collaboration YAML
   - Includes: keyframes, material presets, spatial config

2. **dp** reads `visual_bible_delivery` → loads from `.claude/plugins/cinematographer/agents/dp.md`
   - Loads skills: `deakins-method`, `practical-first`, `review-in-the-cut`, `lighting-setups`
   - Produces `lighting_rig_delivery` collaboration YAML
   - Includes: lighting setup, render config, camera config

3. **colorist** reads `lighting_rig_delivery` → loads from `.claude/plugins/cinematographer/agents/colorist.md`
   - Loads skills: `fraser-shift`, `aces-ocio`, `show-lut`, `skip-bleach`
   - Produces `grading_delivery` collaboration YAML
   - Includes: OCIO config, show LUT, CDL values, achromatic compliance

Each agent loads ONLY its exclusive skills. No cross-loading.

## Output

Final output is `grading_delivery` collaboration YAML with full audit trail
chain linking all three agents' decisions.

## Next Action

The collaboration YAML suggests:
- `/cinematographer:shoot` — to execute shots with the established look
- `/pipeline-expert:consult auteur` — for creative vision review

## Examples

```
/cinematographer:lookdev "coal dust plume over Secunda" --tier preview
/cinematographer:lookdev "volcanic ash dispersion" --tier scout
/cinematographer:lookdev "bushfire emission sequence" --tier final
```

$ARGUMENTS parsed as `"subject"` and optional `--tier` flag.
