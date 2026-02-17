---
description: "Shot finaling pass — 2% rule, sequence continuity, parameter lock"
argument-hint: "<shot-id> [--sequence <id>]"
---

Shot finaling pass. The VFX supe applies the 2% rule — systematic elimination of
every visible artifact, discontinuity, and quality shortfall. Reviews in sequence
context and verifies parameter locks against the continuity ledger.

## Agent

Load vfx-supe from `.claude/plugins/vfx-artist-studio/agents/vfx-supe.md`.

## Skills

Agent loads: `lambert-invisible-vfx`, `dailies-culture`, `two-percent-rule`,
`continuity-ledger`
from `.claude/plugins/vfx-artist-studio/skills/`.

## Procedure

1. Load shot context YAML and verify tier is `final`
2. Load continuity ledger for the sequence
3. **Parameter lock verification**: confirm all wedge parameters are human-locked
4. **Black level audit**: verify pure black background, no noise floor
5. **Grain consistency**: Paper Grain Manifold at density 0.1 (visible) and 0.8 (invisible)
6. **Crust integrity**: dual-state shader transitions smooth, no hard edges
7. **Emission behavior**: arrhythmic pulse perceptible but not distracting
8. **Temporal stability**: no flicker, OIDN temporal denoising effective
9. **Boundary dissolution**: plume-void boundary dissolves, not clips
10. **Cross-shot continuity**: parameters match continuity ledger exactly
11. Produce finaling report
12. **Conservation package** (exhibition tier only): trigger line-producer to
    execute `finaling/conservation-package` skill --- source archive, dependency
    manifest, render configs, asset archive, artist intent, technical rider,
    emulation/migration decisions. Verify `conservation_complete: true`.

## Output

Finaling report with:
- Per-check pass/fail with specific observations
- Continuity ledger verification results
- Any 2% issues found with severity and suggested fix
- Sequence-level assessment (if --sequence provided)
- Conservation package status (exhibition tier: PASS/FAIL; other tiers: SKIPPED)

Next action: if all pass → `/vfx-artist-studio:promote` for exhibition review.
If any fail → specific agent task to fix the issue.
If conservation incomplete (exhibition tier) → line-producer runs conservation-package skill.

$ARGUMENTS: `<shot-id>`, optional `--sequence` for cross-shot continuity check.
