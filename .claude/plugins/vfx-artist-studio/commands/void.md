---
description: "Design void/environment specification for a shot or derived format"
argument-hint: "<shot-id> [--format projection|print|installation]"
---

Design void/environment specification. The matte-artist designs void quality,
plume-void boundary dissolution, and derived format compositions. Read-only agent —
produces design specifications, not code.

## Agent

Load matte-artist from `.claude/plugins/vfx-artist-studio/agents/matte-artist.md`.

## Skills

Agent loads: `void-design`, `boundary-dissolution`, `derived-formats`,
`atmospheric-context`
from `.claude/plugins/vfx-artist-studio/skills/`.

## Procedure

1. Read shot context YAML for current tier and plume characteristics
2. Design void quality: absolute, atmospheric, or textured
3. Specify boundary dissolution behavior (crisp, wispy, crumbling, dissolving)
4. If --format specified, design derived format composition for that medium
5. Validate against achromatic manifesto: no environmental context in exhibition
6. Produce void design delivery collaboration YAML

## Output

Void design specification with:
- Void quality definition and rationale
- Boundary dissolution parameters and emotional intent
- Derived format composition notes (if applicable)
- References to artistic precedent (Kapoor, Turrell, Reinhardt)

Next action: effects-td implements boundary dissolution in code;
compositor applies void parameters in comp.

$ARGUMENTS: `<shot-id>`, optional `--format` for derived format design.
