---
description: Batch visual quality review with auto-detected tier
argument-hint: "<dir>"
---

Batch review all gallery images in a directory. Auto-detects tier from filenames and runs the full two-agent review pipeline for each tier group.

## Usage

```
/critical-eye:review-gallery output/examples/wave5/
/critical-eye:review-gallery output/examples/
```

## Tier Detection

Tier is inferred from filename patterns:

| Pattern | Detected Tier |
|---------|--------------|
| `*exhibition*` or `*exhibit*` | exhibition |
| `*study*` | study |
| `*sketch*` | sketch |
| No tier keyword | study (default) |

Images are grouped by detected tier. Each group is reviewed as a batch using the corresponding tier standard and persona.

## Agent Flow

1. Load the **critical-eye** agent from `.claude/plugins/critical-eye/agents/critical-eye.md`
2. Scan `<dir>` for `*.png` files using Glob
3. Group files by detected tier
4. For each tier group:
   a. Load the appropriate tier standard
   b. Run VFX evaluation across all images in the group
   c. Delegate to art-director for independent artistic evaluation
   d. Synthesize into group-level `review_report`
5. Output a summary across all tier groups

## Sequence Detection

If multiple images in a group share a base name with frame numbers (e.g., `easing_heavy_t02.png`, `easing_heavy_t04.png`), they are automatically treated as a sequence and temporal coherence is evaluated.

## Key Properties

- **Read-only**: No files are created or modified
- **Auto-tier**: No need to specify tier manually
- **Batch efficient**: Groups images to minimize agent context loading
- **Sequence-aware**: Detects frame sequences automatically

$ARGUMENTS passed through to critical-eye agent.
