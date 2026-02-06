---
name: knowledge-query
description: Query the pipeline knowledge bases for domain expertise
user-invocable: false
---

# Knowledge Query

Structured access to the two pipeline knowledge bases stored as YAML in
`.claude/plugins/pipeline-expert/knowledge/`.

## Knowledge Bases

### pipeline-roles-and-processes.yaml

Expert roles, technical processes, and governance for the CO2 visualization
pipeline. Covers all 4 stages plus management and real-world examples.

**Sections (query with `yq '.sections.<key>'`):**

| Key | Content | Primary Agent |
|-----|---------|---------------|
| `executive_summary` | Pipeline overview, 4-stage architecture | Auteur |
| `key_expert_roles_summary` | Role definitions across all stages | Auteur |
| `stage_1_ingestion_experts` | Data ingestion specialists | Spectralist |
| `stage_2_reconstruction_experts` | 3D reconstruction specialists | Spectralist |
| `stage_3_conversion_experts` | VFX asset conversion specialists | Alchemist |
| `stage_4_rendering_experts` | Cinematic rendering specialists | Tonalist, Sculptor |
| `management_and_qa_experts` | Project governance, QA roles | Auteur |
| `data_ingestion_technical_process` | Ingestion pipeline steps | Spectralist |
| `reconstruction_technical_process` | Reconstruction pipeline steps | Spectralist |
| `asset_conversion_technical_process` | Conversion pipeline steps | Alchemist |
| `cinematic_rendering_technical_process` | Rendering pipeline steps | Tonalist, Sculptor, Choreographer |
| `project_governance_and_management` | RACI, gates, audit trail | Auteur |
| `real_world_examples` | NASA SVS, Framestore, SideFX, NCAR | All |

### pipeline-technical-expertise.yaml

Technical expertise for Eisenstein-inspired volumetric rendering: aesthetic
philosophy, shading playbook, satellite sensors, USD workflow, deep compositing,
and validation protocols.

**Sections (query with `yq '.sections.<key>'`):**

| Key | Content | Primary Agent |
|-----|---------|---------------|
| `pipeline_overview` | End-to-end pipeline architecture | All |
| `eisenstein_aesthetic_summary` | Chiaroscuro, shadows, textures (NOT pictorial flattening) | Tonalist, Sculptor |
| `satellite_data_ingestion_and_preprocessing` | OCO-2/3, TROPOMI, CALIOP, MODIS | Spectralist |
| `multimodal_data_fusion_framework` | 4D-Var, EnKF, hybrid assimilation | Spectralist |
| `three_dimensional_atmospheric_reconstruction_methods` | Vertical profiles, transport | Spectralist |
| `vfx_asset_conversion_pipeline` | VDB, point clouds, mesh extraction | Alchemist |
| `eisenstein_inspired_shading_and_lighting_playbook` | PxrVolume, Arnold params, lighting | Tonalist, Sculptor |
| `rendering_performance_and_scalability_strategies` | LOD, caching, GPU acceleration | Alchemist |
| `usd_integration_and_workflow` | UsdVol, Solaris, scene description | Alchemist |
| `point_cloud_generation_strategy` | Houdini scatter, density-weighted | Alchemist |
| `deep_compositing_workflow` | AOV separation, Nuke deep comp | Tonalist |
| `validation_and_quality_assurance_protocols` | QA thresholds, visual checks | All |
| `key_satellite_sensors_and_products` | Sensor specs, retrieval algorithms | Spectralist |
| `recommended_software_and_libraries` | Tool versions, dependencies | Alchemist |

## How to Query

Use `yq` (YAML processor) via Bash to extract specific sections:

```bash
# Extract a single section
yq '.sections.eisenstein_aesthetic_summary' \
  .claude/plugins/pipeline-expert/knowledge/pipeline-technical-expertise.yaml

# Extract multiple sections
yq '.sections | pick(["stage_1_ingestion_experts", "stage_2_reconstruction_experts"])' \
  .claude/plugins/pipeline-expert/knowledge/pipeline-roles-and-processes.yaml

# Search for a keyword across all sections
yq '.. | select(type == "!!str" and test("OCO-2"))' \
  .claude/plugins/pipeline-expert/knowledge/pipeline-technical-expertise.yaml

# List all available section keys
yq '.sections | keys' \
  .claude/plugins/pipeline-expert/knowledge/pipeline-roles-and-processes.yaml
```

If `yq` is not available, use Python:

```python
import yaml
from pathlib import Path

kb_dir = Path(".claude/plugins/pipeline-expert/knowledge")
with open(kb_dir / "pipeline-technical-expertise.yaml") as f:
    data = yaml.safe_load(f)
section = data["sections"]["eisenstein_aesthetic_summary"]
```

## When to Query

- **Before writing agent prompts**: Extract the relevant sections for that agent's domain
- **During review**: Verify technical claims against the knowledge base
- **For ideation**: Feed domain context into the ideation protocol
- **For standards**: Cross-reference QA thresholds against source material

## IMPORTANT

These knowledge bases are **consultative reference material**. They inform agent
behavior but are NOT loaded at runtime. Agents distill this knowledge into their
own skills and personas. The knowledge bases are the source of truth when
verifying technical accuracy.
