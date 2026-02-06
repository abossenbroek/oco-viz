# pipeline-expert

Seven-agent art-first pipeline expertise: from OCO-2/3 satellite data to museum-quality exhibition renders of Anthropocene industrial emissions.

## The Soot Aesthetic

This is not data visualization. This is material confrontation. The pipeline renders CO2 plumes as coal dust, volcanic ash, combustion residue -- substances with weight, texture, and toxicity. The visual language draws from the Anthropocene: industrial dread, the slow accumulation of atmospheric damage, the sublime terror of what we have put into the sky. Every rendering decision serves this confrontation. Pretty is failure. Comfortable is failure. The viewer should feel the weight.

## Quality Benchmark Artists

- **Refik Anadol** -- Data as sculptural material; massive-scale projections that transform architecture into living surfaces
- **Ryoji Ikeda** -- Data-driven minimalism; the sublime in pure information density and scale
- **Sergei Eisenstein** -- Montage as intellectual collision; every cut creates meaning through juxtaposition
- **Werner Herzog** -- The ecstatic truth; documentary that transcends fact to reveal deeper reality
- **William Kentridge** -- Charcoal as medium of erasure and memory; the mark-making of industrial history
- **James Turrell** -- Light as material; perception as the art object itself
- **Anish Kapoor** -- Void as presence; the black that swallows light and returns nothing

## The GenTech Pipeline

```
Stage 1              Stage 2                Stage 3               Stage 4
DATA FOUNDRY    -->  VOLUMETRIC        -->  MATERIAL &       -->  COMPOSITING &
                     SCULPTING              LIGHTING              EXHIBITION

OCO-2/3 L2 Lite     Data Assimilation      Transfer Functions     Camera + Motion
MODIS/TROPOMI        4D-Var / LETKF         Mie/Rayleigh          Deep EXR
ERA5 Reanalysis      Lagrangian Tracking    OpenVDB Shading        Color Grading
Cloud Screening      Tomographic Recon      Volumetric Lighting    Film Grain
Bias Correction      xr.Dataset Output      Emission Mode          Gallery Install
```

Real-world parallel: NASA's Scientific Visualization Studio (SVS) executes this pipeline regularly, converting OCO-2/3 mission data into scientifically accurate cinematic visualizations. VFX houses like Framestore bring the cinematic craft; SideFX Houdini provides the volumetric toolchain; NCAR/UCAR contributes the atmospheric science backbone.

## Agent Roster

```
                    +------------------+
                    |     AUTEUR       |
                    | Creative Director|
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
    +---------+--+  +--------+---+  +-------+------+
    | SCULPTOR   |  | TONALIST   |  | CHOREOGRAPHER|
    | Volume     |  | Color &    |  | Camera &     |
    | Craft      |  | Material   |  | Motion       |
    +-----+------+  +------+-----+  +------+-------+
          |                |               |
          +--------+-------+-------+-------+
                   |               |
          +--------+---+   +------+-------+
          | SPECTRALIST|   | ALCHEMIST    |
          | Atmospheric|   | Pipeline     |
          | Physics    |   | Intelligence |
          +------------+   +------+-------+
                                  |
                          +-------+------+
                          |  INSTALLER   |
                          |  Exhibition  |
                          |  Deployment  |
                          +--------------+
```

| Agent | Role | Model | Responsibility |
|-------|------|-------|----------------|
| **Auteur** | Creative Director | opus | Artistic vision, ideation synthesis, creative governance |
| **Sculptor** | Volume Craftsperson | opus | Turbulence structure, density sculpting, fBm parameters |
| **Tonalist** | Color & Material Scientist | opus | Transfer functions, soot palette, chromatic discipline |
| **Choreographer** | Cinematic Craftsperson | opus | Camera placement, motion design, temporal pacing |
| **Spectralist** | Atmospheric Physicist | opus | Physical constraints, scattering models, data fidelity |
| **Alchemist** | Pipeline TD | opus | Config generation, format conversion, procedural tooling |
| **Installer** | Exhibition Deployer | opus | Gallery setup, projection mapping, spatial audio, install docs |

## Command Reference

| Command | Description | Routes To |
|---------|-------------|-----------|
| `/pipeline-expert:review` | Full pipeline review at specified stage and tier | Stage-appropriate agents |
| `/pipeline-expert:ideate` | Multi-model creative ideation session | Auteur + Gemini provocation |
| `/pipeline-expert:audit` | Cross-stage pipeline audit with audit trail | All agents in sequence |
| `/pipeline-expert:install` | Exhibition installation planning and validation | Installer + Choreographer |

## Skills Architecture

### Reference (3)
- `output-schemas` -- YAML output contracts for all agent types
- `verdict-protocol` -- PASS/CONCERN/FAIL + artistic verdict synthesis
- `phase-template` -- Standard 4-phase execution pattern (Context/Analysis/Validation/Verdict)

### Critical (7)
- `artistic-direction` -- Soot aesthetic, Anthropocene visual language
- `volumetric-craft` -- fBm parameters, turbulence structure, density sculpting
- `transfer-function-design` -- Opacity/color mapping, emission mode, exhibition TFs
- `cinematic-language` -- Camera grammar, motion tempo, compositional authority
- `atmospheric-constraints` -- Physical plume behavior, scattering, wind coherence
- `pipeline-intelligence` -- Config synthesis, format pipelines, procedural generation
- `exhibition-deployment` -- Gallery tech, projection, spatial requirements

### Exhibition (4)
- `gallery-standards` -- Museum-grade output requirements
- `projection-mapping` -- Display technology and spatial calibration
- `spatial-audio` -- Sound design integration for installations
- `documentation` -- Artist statements, technical riders, install guides

### Atmospheric / Pipeline (3)
- `data-provenance` -- OCO-2/3 data chain, bias correction, quality flags
- `scattering-models` -- Mie, Rayleigh, phase functions for rendering
- `config-synthesis` -- Automated config generation from creative briefs

### Toolchains (3)
- `vtk-rendering` -- VTK volume mapper, sample distance, jittering
- `openvdb-workflow` -- Sparse volume conversion and optimization
- `houdini-bridge` -- SideFX Houdini interop patterns

### Standards (10)
- `exhibition-tier` -- Full exhibition quality requirements
- `study-tier` -- Study-level relaxed thresholds
- `sketch-tier` -- Rapid iteration minimal checks
- `ingestion-standard` -- Stage 1 data quality gates
- `reconstruction-standard` -- Stage 2 volume fidelity gates
- `conversion-standard` -- Stage 3 format compliance gates
- `rendering-standard` -- Stage 4 visual quality gates
- `sequence-standard` -- Temporal coherence across frames
- `physical-plausibility` -- Atmospheric physics constraints
- `color-science` -- Chromatic discipline and soot palette spec

## The Ideation Protocol

```
Phase 1: ANALYSIS        Phase 2: PROVOCATION      Phase 3: SYNTHESIS       Phase 4: EXECUTION
(Claude)                 (Gemini)                  (Auteur)                 (All Agents)

Ground truth from        Wild creative             Director's brief         Parameter configs
data analysis            provocations              reconciling              and code snippets
                         challenging               art + physics
Technical canvas         assumptions                                        Agent-specific
of what's possible                                 Per-agent                directives
                         Risk assessment           directives
```

The protocol deliberately uses different models for different phases. Claude provides rigorous ground truth. Gemini provides creative disruption. The Auteur synthesizes. This prevents groupthink and produces ideas no single model would generate alone.

## Decision Tree

```
Your Goal                              Command
-------------------------------------------
"Review this render"               --> /pipeline-expert:review
"I need new visual ideas"          --> /pipeline-expert:ideate
"Is the full pipeline sound?"      --> /pipeline-expert:audit
"Plan the gallery installation"    --> /pipeline-expert:install
"Evaluate artistic quality"        --> /critical-eye:review (sister plugin)
```

## Validation

Run the structural validator to check that all agents, commands, and skills are correctly wired:

```bash
python .claude/plugins/pipeline-expert/validate_plugin.py
```

Reports missing files (errors), orphan skills (warnings), and summary counts.
