# critical-eye

A Claude Code plugin implementing a **two-agent visual quality review** system for rendered gallery images. A VFX Technical Eye evaluates against deep cinematic craft principles, then consults an independent Art Director whose personality shifts by tier. Neither agent sees the other's findings before forming its own judgment.

## Architecture

```
/critical-eye:review exhibition <image>
       |
       v
critical-eye agent (VFX TD)
  1. Read tier standard + visual language + configs
  2. Read image, run pixel stats
  3. Evaluate 7 VFX categories -> vfx_findings
  4. Build art_director_request (WITHOUT vfx_findings)
  5. Delegate to art-director agent
       |
       v
art-director agent (tier persona)
  1. Activate tier persona (Curator / Studio Mentor / Quick-Check)
  2. Read image independently
  3. Evaluate 5 artistic categories -> art_director_review
  4. Return to critical-eye
       |
       v
critical-eye agent (continued)
  6. Synthesize VFX + artistic reviews
  7. Surface disagreements explicitly
  8. Output final review_report
```

## Independence Firewall

The art-director **never sees** the VFX agent's findings before forming its own judgment. The delegation payload includes only: images, tier, config snapshot. No VFX scores, no technical notes. This prevents rubber-stamping.

## Commands

| Command | Description |
|---------|-------------|
| `/critical-eye:review <tier> <path> [--sequence]` | Full two-agent review of specified image(s) |
| `/critical-eye:review-gallery <dir>` | Batch review with auto-detected tier from filenames |

## Agents

| Agent | Role | Model | Tools |
|-------|------|-------|-------|
| critical-eye | Senior VFX Lighting TD | opus | Read, Glob, Bash (read-only pixel analysis) |
| art-director | Independent artistic voice | opus | Read, Glob (purely consultative) |

## Context Fidelity

| Agent | Context Level | Reads |
|-------|--------------|-------|
| critical-eye | SELECTIVE | Tier standard (one of three) + visual language + tier config + images |
| art-director | MINIMAL | Images + tier name + config snapshot (no VFX findings) |

## Output Contract

Final output is a `review_report` YAML with:
- `vfx_review`: 7 technical categories with pass/fail per category
- `artistic_review`: 5 artistic categories with scores + persona voice
- `synthesis`: combined verdict, key strengths/concerns, disagreements, actionable suggestions
