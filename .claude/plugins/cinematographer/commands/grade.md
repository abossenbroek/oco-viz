---
name: grade
description: Color grading session — show LUT creation, OCIO config, achromatic validation
user-invocable: true
---

# Grade Command

Color grading session. The colorist agent reads upstream collaboration YAML
and produces OCIO configuration, show LUT, CDL values, and achromatic
compliance data.

## Usage

```
/cinematographer:grade <shot-id|sequence-id> [--mode create-lut|apply|verify]
```

## Arguments

- `<shot-id|sequence-id>`: Shot or sequence identifier to grade
- `--mode`: Grading mode (default: create-lut)
  - `create-lut` — create the base show LUT for the project
  - `apply` — apply existing LUT with per-shot CDL trims
  - `verify` — verify achromatic compliance of existing grade

## Agent Flow

1. Load the colorist agent from `.claude/plugins/cinematographer/agents/colorist.md`
2. Colorist loads exclusive skills: `fraser-shift`, `aces-ocio`, `show-lut`, `skip-bleach`
3. Colorist reads upstream collaboration YAML:
   - `lighting_rig_delivery` — for lighting color temperatures and render config
   - `shot_execution_delivery` — for rendered frame paths
4. Colorist builds OCIO config, creates show LUT, generates CDL
5. Colorist validates achromatic compliance per tier
6. Colorist produces `grading_delivery` collaboration YAML

## Output

Collaboration YAML with `grading_delivery` payload:
- `show_lut_spec` — OCIO config path, CDL values, achromatic compliance
- `film_emulation` — SHIFT view transform, enabled status

## Next Action

The collaboration YAML suggests:
- `/pipeline-expert:consult tonalist` — for achromatic validation
- `/critical-eye:review` — for visual QA

## Examples

```
/cinematographer:grade hero_sequence --mode create-lut
/cinematographer:grade shot_001 --mode apply
/cinematographer:grade full_sequence --mode verify
```

$ARGUMENTS parsed as `<shot-id|sequence-id>` and optional `--mode` flag.
