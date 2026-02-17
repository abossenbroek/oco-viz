# cinematographer

**v1.0.0** -- VFX production coding toolkit encoding Blade Runner 2049 and Dune methodology. Agents communicate exclusively through collaboration YAML with shared schema. Storyboarding, look development, color science, and physical validation from creative brief to exhibition-grade delivery.

## Architecture

```
pipeline-expert                 cinematographer                    critical-eye
(upstream domain expertise)     (production execution)             (quality review)

  auteur ----brief----->  dp  -----collaboration.yaml----->  critical-eye
  sculptor --volumes-->  production-designer --lookdev-->     art-director
  tonalist --palette-->  colorist -----------grade------>
  spectralist -phys-->   groundtruth --------validate-->
                         storyboarder ------boards----->

                    Collaboration YAML is the shared contract.
                    No agent reads another agent's internal state.
```

### Data Flow

```
Creative Brief
    |
    v
/storyboard  -->  storyboarder  -->  shot_list.yaml
    |
    v
/lookdev     -->  dp + production-designer  -->  lookdev_package.yaml
    |
    v
/shoot       -->  dp + groundtruth  -->  rendered frames + validation
    |
    v
/grade       -->  colorist  -->  graded frames + show LUT
    |
    v
/dailies     -->  all agents  -->  review notes + verdicts
    |
    v
/wrap        -->  dp  -->  final delivery package
```

## Agent Roster

| Agent | Role | Model | Responsibility |
|-------|------|-------|----------------|
| **dp** | Director of Photography | opus | Shot design, lighting strategy, camera grammar, overall visual authority |
| **production-designer** | Production Designer | opus | Material library, set dressing, visual bible, environment design |
| **colorist** | Colorist | opus | ACES pipeline, show LUT, skip-bleach, grade layers, color science |
| **groundtruth** | Physical Validator | opus | Atmospheric physics, scattering validation, data fidelity, unit checks |
| **storyboarder** | Storyboard Artist | opus | Sequence design, shot grammar, color palette, beat mapping |

## Commands

| Command | Description | Primary Agent(s) |
|---------|-------------|-------------------|
| `/cinematographer:storyboard` | Generate storyboard from creative brief | storyboarder, dp |
| `/cinematographer:lookdev` | Look development session for materials, lighting, atmosphere | dp, production-designer |
| `/cinematographer:shoot` | Execute a render pass with physical validation | dp, groundtruth |
| `/cinematographer:grade` | Color grading session: show LUT, skip-bleach, final grade | colorist |
| `/cinematographer:dailies` | Review rendered frames with full agent panel | all agents |
| `/cinematographer:wrap` | Final delivery: package, validate, document | dp |

## Skill Categories

### Reference (7 skills)
Core protocols shared by all agents:
- `collaboration-protocol` -- YAML interchange contract between agents
- `governance-bridge` -- Escalation paths to pipeline-expert and critical-eye
- `output-schemas` -- YAML output format definitions per agent type
- `phase-template` -- Standard 4-phase execution pattern
- `quality-gates` -- Per-tier quality thresholds (scout/preview/final)
- `tech-stack` -- Approved tools, versions, and integration points
- `verdict-protocol` -- PASS/CONCERN/FAIL verdict synthesis

### Standards (3 skills)
Tier-specific quality definitions:
- `scout-tier` -- 128-cube rapid iteration checks
- `preview-tier` -- 512-cube lighting/material validation
- `final-tier` -- 1024-cube exhibition-grade requirements

### Methodology (5 skills)
Cinematographic methodology and creative process:
- `deakins-method` -- Roger Deakins' approach to motivated lighting
- `fraser-shift` -- Greig Fraser's controlled desaturation technique
- `practical-first` -- Practical lighting as foundation before CG augmentation
- `review-in-the-cut` -- Evaluation methodology for frames in editorial context
- `vermette-bible` -- Patrice Vermette's visual bible production design method

### Storyboarding (3 skills)
Visual storytelling and sequence planning:
- `color-palette` -- Per-sequence palette definition and emotional mapping
- `sequence-design` -- Beat structure, tension curves, temporal pacing
- `shot-grammar` -- Lens, angle, movement vocabulary for volumetric subjects

### Look Development (3 skills)
Material and lighting design:
- `lighting-setups` -- Key/fill/rim patterns for volumetric rendering
- `material-library` -- Soot, ash, vapor material definitions
- `visual-bible-protocol` -- Living reference document for show consistency

### Pipeline (3 skills)
Production pipeline integration:
- `hython-standards` -- SideFX Houdini scripting patterns
- `openvdb-production` -- Sparse volume production workflow
- `usd-patterns` -- Universal Scene Description layering and composition

### Color Science (3 skills)
Color management and grading:
- `aces-ocio` -- ACES color pipeline with OpenColorIO configuration
- `show-lut` -- Show-specific look-up table design and baking
- `skip-bleach` -- Bleach bypass / silver retention emulation technique

## Collaboration YAML Protocol

All inter-agent communication uses a shared YAML schema. No agent reads another agent's internal state -- the collaboration YAML is the single source of truth for handoffs.

```yaml
# Example collaboration YAML structure
collaboration:
  session_id: "shoot-2026-02-15-001"
  phase: "lookdev"
  tier: "preview"

  from_agent: "dp"
  to_agent: "production-designer"

  brief:
    intent: "Dusty industrial plume, late afternoon"
    references: ["BR2049-furnace", "Dune-spice-blow"]

  deliverables:
    - type: "material_definition"
      format: "yaml"
      status: "requested"

  verdict:
    status: "pending"
    notes: []
```

## Quality Gates

| Tier | Resolution | Purpose | Gate Strictness |
|------|------------|---------|-----------------|
| Scout | 128-cube | Creative direction approval | Relaxed |
| Preview | 512-cube | Lighting, material, composition | Standard |
| Final | 1024-cube | Exhibition delivery | Maximum |

Each command triggers tier-appropriate validation. The `groundtruth` agent enforces physical plausibility at every tier. The `dp` holds final visual authority.

## Validation

```bash
# Validate plugin structure (agents, commands, skills, cross-references)
python .claude/plugins/cinematographer/validate_plugin.py

# Validate artifact formats (Python, YAML, JSON, OCIO, USD)
python .claude/plugins/cinematographer/validate_artifacts.py --self-test
```

## Version Roadmap

| Version | Status | Scope |
|---------|--------|-------|
| **v1.0** | Current | Core agents, commands, skills. Collaboration YAML protocol. Scout/preview/final tiers. |
| **v1.1** | Planned | Houdini bridge integration: live HDA parameter exchange via collaboration YAML. |
| **v1.2** | Planned | Multi-shot sequence orchestration: automated dailies across frame ranges. |
| **v1.3** | Planned | Exhibition installer agent: projection mapping, spatial audio, gallery tech specs. |
