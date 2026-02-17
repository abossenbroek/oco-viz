---
name: usd-patterns
user-invocable: false
type: instruction
primary_owner: groundtruth
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# USD Patterns — Scene Structure for Production Pipelines

Every USD prim has a purpose. Unreferenced prims are removed. The scene graph is not a
dumping ground for data — it is a structured document that downstream tools parse,
override, and compose. A messy scene graph breaks layer composition, prevents selective
loading, and turns debugging into archaeology. These patterns encode the hierarchy,
annotation, and composition rules that keep the USD stage clean and production-ready.

> "USD is not a file format. It is an opinion about how scenes should be organized."

---

## Principle

USD (Universal Scene Description) is the scene description standard for VFX production.
The oco-viz pipeline exports VTK-generated volumes, lights, and cameras as USD stages
that flow into Houdini/Karma XPU for final rendering. Every prim in the stage must be
discoverable by name, purposeful by annotation, and composable by layer. The prim
hierarchy is the pipeline's API — changing it breaks every tool that reads it.

---

## Procedure

### Step 1 — Establish Stage Defaults

Every USD stage begins with global settings that downstream tools depend on:

| Setting | Value | Impact of Error |
|---------|-------|-----------------|
| Up axis | Y | Wrong orientation in Houdini viewport |
| Meters per unit | 1.0 | Scale mismatch with VDB grids |
| Time codes per second | 24 | Animation timing errors |
| Default prim | /World | Stage reference target |

### Step 2 — Build Prim Hierarchy

The standard hierarchy for oco-viz scenes:

```
/World                          # root — default prim
  /World/Volumes                # all volume prims
    /World/Volumes/{name}       # individual volume (e.g. co2_plume)
  /World/Lights                 # all light prims
    /World/Lights/{name}        # individual light (e.g. key_furnace)
  /World/Camera                 # camera prim
  /World/Environment            # optional environment (HDRI, ground plane)
    /World/Environment/{name}   # individual environment element
```

Every prim at every level must be purposeful. If a prim cannot be referenced by a
downstream tool, it should not exist.

### Step 3 — Annotate Required Metadata

Every prim carries custom metadata that documents its purpose and provenance:

| Annotation Key | Type | Description |
|----------------|------|-------------|
| `purpose` | string | Why this prim exists (e.g. "primary density volume") |
| `source_data` | string | Path to source data or generation script |
| `created_by` | string | Agent or tool that created this prim |
| `tier` | string | scout / preview / final |
| `schema_version` | string | Version of the USD pattern being followed |

### Step 4 — Apply Layer Composition

USD layers enable non-destructive overrides. The oco-viz pipeline uses a two-layer
pattern:

| Layer | Purpose | Example |
|-------|---------|---------|
| Base layer | Scene structure, geometry, default values | `scene_base.usda` |
| Override layer | Per-shot or per-tier modifications | `scene_override.usda` |

The base layer is authored by the pipeline. The override layer is authored by artists
or by automated per-shot tools. Overrides reference base prims by path and modify only
specific attributes.

### Step 5 — Validate Stage

Before writing, validate:

- Every prim has `purpose` annotation
- Hierarchy follows the standard pattern
- No orphaned prims (prims unreachable from /World)
- Stage metadata is complete (up axis, meters per unit, time codes)
- Layer composition resolves without errors

---

## Verified Code Templates

### Stage Creation with Proper Defaults

```python
"""Create a USD stage with correct global settings."""
from __future__ import annotations

from pxr import Usd, UsdGeom  # type: ignore[import-untyped]

def create_stage(path: str) -> Usd.Stage:
    """Create a new USD stage with oco-viz defaults.

    Parameters
    ----------
    path : str
        Output file path (.usda or .usdc).
    """
    stage = Usd.Stage.CreateNew(path)

    # Global settings
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)  # meters
    stage.SetTimeCodesPerSecond(24)

    # Root prim
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)

    # Standard hierarchy
    stage.DefinePrim("/World/Volumes", "Scope")
    stage.DefinePrim("/World/Lights", "Scope")
    stage.DefinePrim("/World/Camera", "Xform")

    return stage
```

### Volume Prim with Field Asset References

```python
"""Create a USD volume prim referencing an OpenVDB file."""
from __future__ import annotations

from pxr import Usd, UsdVol  # type: ignore[import-untyped]

def add_volume_prim(
    stage: Usd.Stage,
    name: str,
    vdb_path: str,
    grid_name: str = "density",
    purpose: str = "primary density volume",
) -> Usd.Prim:
    """Add a volume prim referencing an external VDB grid.

    Parameters
    ----------
    stage : Usd.Stage
        Target USD stage.
    name : str
        Volume identifier (e.g. "co2_plume").
    vdb_path : str
        Absolute path to .vdb file.
    grid_name : str
        Name of the grid within the VDB file.
    purpose : str
        Annotation describing this volume's role.
    """
    volume_path = f"/World/Volumes/{name}"
    volume = UsdVol.Volume.Define(stage, volume_path)

    # Field asset reference
    field_path = f"{volume_path}/{grid_name}"
    field = UsdVol.OpenVDBAsset.Define(stage, field_path)
    field.GetFilePathAttr().Set(vdb_path)
    field.GetFieldNameAttr().Set(grid_name)

    # Bind field to volume
    volume.CreateFieldRelationship(grid_name, field_path)

    # Annotations
    prim = stage.GetPrimAtPath(volume_path)
    prim.SetCustomDataByKey("purpose", purpose)
    prim.SetCustomDataByKey("source_data", vdb_path)
    prim.SetCustomDataByKey("created_by", "oco-viz")

    return prim
```

### Light Prim Pattern

```python
"""Create a USD light prim with motivation annotation."""
from __future__ import annotations

from pxr import Usd, UsdLux  # type: ignore[import-untyped]

def add_distant_light(
    stage: Usd.Stage,
    name: str,
    color_temp: int,
    intensity: float,
    motivation: str,
) -> Usd.Prim:
    """Add a distant light with physical motivation annotation.

    Parameters
    ----------
    stage : Usd.Stage
        Target USD stage.
    name : str
        Light identifier (e.g. "key_furnace").
    color_temp : int
        Color temperature in Kelvin.
    intensity : float
        Light intensity.
    motivation : str
        Physical source justification.
    """
    light_path = f"/World/Lights/{name}"
    light = UsdLux.DistantLight.Define(stage, light_path)
    light.GetColorTemperatureAttr().Set(float(color_temp))
    light.GetIntensityAttr().Set(intensity)
    light.GetEnableColorTemperatureAttr().Set(True)

    # Annotations
    prim = stage.GetPrimAtPath(light_path)
    prim.SetCustomDataByKey("purpose", f"light: {motivation}")
    prim.SetCustomDataByKey("created_by", "oco-viz/dp-agent")
    prim.SetCustomDataByKey("color_temp_kelvin", color_temp)

    return prim
```

---

## Parameters

### Stage Global Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `up_axis` | string | Y | Stage up axis (always Y for Houdini) |
| `meters_per_unit` | float | 1.0 | Scale factor (always 1.0 for meters) |
| `time_codes_per_second` | float | 24 | Frame rate |
| `default_prim` | string | /World | Stage default prim path |

### Prim Hierarchy Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `volumes_scope` | string | /World/Volumes | Parent scope for volume prims |
| `lights_scope` | string | /World/Lights | Parent scope for light prims |
| `camera_path` | string | /World/Camera | Camera prim path |
| `environment_scope` | string | /World/Environment | Environment scope |

### Annotation Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `purpose_required` | bool | true | Every prim must have purpose annotation |
| `source_data_required` | bool | true | Asset prims must cite source data |
| `created_by_required` | bool | true | Every prim must identify its creator |

### Layer Composition Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_layer_suffix` | string | _base | Base layer filename suffix |
| `override_layer_suffix` | string | _override | Override layer filename suffix |
| `max_layer_depth` | int | 3 | Maximum composition arc depth |

---

## Anti-Patterns

### 1. The Flat Hierarchy

**Symptom:** All prims sit directly under /World — volumes, lights, cameras, and
miscellaneous prims at the same level. The stage reads like an unsorted directory.

**Cause:** Skipping the hierarchy design step and creating prims wherever is convenient.
"It loads, so it works."

**Fix:** Follow the standard hierarchy: /World/Volumes, /World/Lights, /World/Camera.
Every prim must be reachable through a scoped parent. Flat hierarchies break namespace
isolation and make selective loading impossible.

### 2. The Undocumented Prim

**Symptom:** A prim exists in the stage with no `purpose` annotation. Six months later
nobody knows why it is there or whether it can be safely removed.

**Cause:** Creating prims for technical convenience without documenting their role.
"I'll annotate it later" (later never comes).

**Fix:** Annotation is not optional. Every prim gets `purpose`, `source_data`, and
`created_by` at creation time — not as a cleanup pass. If you cannot state the purpose,
the prim should not exist.

### 3. The Monolithic Layer

**Symptom:** A single USD file contains the entire scene definition including base
geometry, per-shot overrides, render settings, and artist adjustments. Any change
requires modifying the whole file.

**Cause:** Treating USD as a monolithic file format instead of a composition system.

**Fix:** Separate base layer from override layer. The base layer defines structure and
default values. The override layer contains only the delta. Multiple overrides can stack
without touching the base. This is not optional architecture — it is how USD is designed
to work.

### 4. The Orphaned Reference

**Symptom:** A prim references an external asset (VDB file, texture, HDRI) using a
relative path that breaks when the stage is moved or archived.

**Cause:** Using relative paths or paths with environment variables that resolve only
on the author's machine.

**Fix:** Use absolute paths for asset references in production stages. For portability,
use USD's asset resolver with a configured search path, not ad-hoc relative paths.
Always validate that referenced assets exist before writing the stage.

---

## Validation Checklist

- [ ] Stage up axis set to Y
- [ ] Meters per unit set to 1.0
- [ ] Time codes per second set to 24
- [ ] Default prim set to /World
- [ ] Hierarchy follows standard: /World/Volumes, /World/Lights, /World/Camera
- [ ] Every prim has `purpose` annotation
- [ ] Every asset prim has `source_data` annotation
- [ ] Every prim has `created_by` annotation
- [ ] No orphaned prims (all prims reachable from /World)
- [ ] Layer composition: base layer separate from override layer
- [ ] Asset references use absolute paths or configured resolver
- [ ] Stage validates without composition errors
- [ ] Referenced VDB files exist and contain expected grids
