---
description: "Define multi-pass compositing specification for a shot/sequence"
argument-hint: "<shot-id> [--tier scout|preview|final]"
---

Define multi-pass compositing specification. The compositor specifies AOV integration,
deep compositing setup, grain restoration, and delivery format conversion.

## Agent

Load compositor from `.claude/plugins/vfx-artist-studio/agents/compositor.md`.

## Skills

Agent loads: `multi-pass-integration`, `deep-compositing`, `aov-specification`,
`exhibition-delivery`
from `.claude/plugins/vfx-artist-studio/skills/`.

Also loads knowledge: `compositing-standards.yaml`, `exhibition-delivery-spec.yaml`,
`asset-naming-conventions.yaml`.

## Procedure

1. Read shot context YAML for current tier and status
2. Define AOV specification from compositing-standards.yaml
3. Specify multi-pass merge order (deep resolve first, then flat)
4. Configure grain restoration (10-15% NoisyBeauty blend)
5. Specify delivery format conversions per exhibition-delivery-spec.yaml
6. Validate AOV completeness against render config
7. Produce comp delivery collaboration YAML

## Output

Compositing specification with:
- AOV manifest with expected channels and formats
- Merge order and operations
- Grain restoration parameters
- Delivery format specifications per target (projection, print, archive, review)

Next action: `/vfx-artist-studio:final` for shot finaling after comp.

$ARGUMENTS: `<shot-id>`, optional `--tier` flag.
