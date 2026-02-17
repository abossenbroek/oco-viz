---
description: "Shot finaling pass — 2% rule, sequence continuity, parameter lock"
argument-hint: "<shot-id> [--sequence <id>]"
---

Shot finaling via the VFX supe agent using the 2% rule.

## Agent

Load vfx-supe from `.claude/plugins/vfx-artist-studio/agents/vfx-supe.md`.

## Skills

Agent loads methodology and finaling skills from `.claude/plugins/vfx-artist-studio/skills/`.

## Output

Finaling report with per-check pass/fail, continuity ledger verification,
and sequence-level assessment.

$ARGUMENTS: `<shot-id>`, optional `--sequence` for cross-shot continuity.
