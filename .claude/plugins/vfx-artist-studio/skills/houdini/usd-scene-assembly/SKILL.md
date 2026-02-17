---
name: usd-scene-assembly
user-invocable: false
type: instruction
primary_owner: houdini-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# USD Scene Assembly -- Scene Description for Karma XPU Rendering

USD is the scene description standard for the oco-viz production pipeline. Every volume,
light, camera, and material is authored as a USD prim in a structured hierarchy that
Karma XPU reads without translation. The scene graph is an API: every prim has a defined
path, every attribute has a defined type, and every relationship is explicit. Changing the
hierarchy breaks every tool that reads it.

This skill extends the cinematographer's USD patterns skill
(`.claude/plugins/cinematographer/skills/pipeline/usd-patterns/SKILL.md`) with
Houdini-specific assembly procedures for the Soot exhibition pipeline.

> "USD is not a file format. It is an opinion about how scenes should be organized."

---

## Principle

The oco-viz USD scene assembles VTK-generated OpenVDB volumes, Soot Crust MaterialX
shaders, physically-motivated lights, and cinematographic cameras into a single
composable stage. Houdini's Solaris context (LOPs) is the assembly environment, but
all assembly is scripted via Hython -- never performed interactively. The stage must
load in Karma XPU without manual intervention, with correct units, orientation, and
default prim set.

---

## Procedure

### Step 1 -- Establish Stage Defaults

Every USD stage begins with global settings that downstream tools depend on:

| Setting | Value | Impact of Error |
|---------|-------|-----------------|
| Up axis | Y | Wrong orientation in Houdini viewport and Karma |
| Meters per unit | 1.0 | Scale mismatch with VDB grids (all in meters) |
| Time codes per second | 24 | Animation timing errors (project is 24 fps) |
| Default prim | /World | Stage reference target for composition |
| Start time code | 1 | First frame of the shot |
| End time code | 720 | Last frame (30 sec at 24 fps) |

### Step 2 -- Build Prim Hierarchy

The standard hierarchy for oco-viz scenes:

```
/World                              # root -- default prim (Xform)
  /World/Volumes                    # all volume prims (Scope)
    /World/Volumes/{name}           # individual volume (Volume)
      /World/Volumes/{name}/density # VDB field asset (OpenVDBAsset)
      /World/Volumes/{name}/vel     # velocity field (OpenVDBAsset)
  /World/Lights                     # all light prims (Scope)
    /World/Lights/{name}            # individual light (DistantLight, etc.)
  /World/Camera                     # camera prim (Camera)
  /World/Environment                # optional environment (Scope)
    /World/Environment/{name}       # environment element (DomeLight, etc.)
  /World/Materials                  # MaterialX material prims (Scope)
    /World/Materials/{name}         # individual material (Material)
```

Every prim at every level must be purposeful and annotated.

### Step 3 -- Create Volume Prims with VDB References

Volume prims reference external VDB files through field asset relationships:

1. Define a `Volume` prim under `/World/Volumes/`.
2. For each grid in the VDB, define an `OpenVDBAsset` child prim.
3. Set `filePath` to the absolute VDB file path.
4. Set `fieldName` to the grid name (`density`, `vel`, `temperature`).
5. Create a field relationship binding the grid to the volume.

### Step 4 -- Apply Layer Composition

The oco-viz pipeline uses a two-layer composition pattern:

| Layer | Purpose | File |
|-------|---------|------|
| Base layer | Scene structure, geometry, default materials | `{shot}_base.usda` |
| Override layer | Per-tier or per-shot modifications | `{shot}_override.usda` |

The base layer is authored once per shot. The override layer contains only deltas --
tier-specific render settings, lookdev parameter overrides, camera adjustments. Multiple
override layers can stack without modifying the base.

### Step 5 -- Validate Stage

Before writing the stage to disk:

1. Verify stage metadata: up axis, meters per unit, time codes.
2. Traverse all prims and confirm `purpose` annotation exists.
3. Verify no orphaned prims (all reachable from /World).
4. Validate all VDB file references resolve to existing files.
5. Check layer composition resolves without errors.

---

## Verified Code Templates

### Stage Creation with Proper Defaults

```python
"""Create a USD stage with oco-viz defaults via Hython."""
from __future__ import annotations

from pxr import Usd, UsdGeom  # type: ignore[import-untyped]


def create_stage(
    path: str,
    start_frame: int = 1,
    end_frame: int = 720,
) -> Usd.Stage:
    """Create a new USD stage with oco-viz pipeline defaults.

    Parameters
    ----------
    path : str
        Output file path (.usda or .usdc).
    start_frame : int
        First frame of the shot.
    end_frame : int
        Last frame of the shot.
    """
    stage = Usd.Stage.CreateNew(path)

    # Global settings
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.SetTimeCodesPerSecond(24)
    stage.SetStartTimeCode(start_frame)
    stage.SetEndTimeCode(end_frame)

    # Root prim
    world = stage.DefinePrim("/World", "Xform")
    stage.SetDefaultPrim(world)

    # Standard hierarchy
    stage.DefinePrim("/World/Volumes", "Scope")
    stage.DefinePrim("/World/Lights", "Scope")
    stage.DefinePrim("/World/Camera", "Xform")
    stage.DefinePrim("/World/Environment", "Scope")
    stage.DefinePrim("/World/Materials", "Scope")

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
    grid_names: list[str] | None = None,
    purpose: str = "primary CO2 plume volume",
) -> Usd.Prim:
    """Add a volume prim referencing an external VDB file.

    Parameters
    ----------
    stage : Usd.Stage
        Target USD stage.
    name : str
        Volume identifier (e.g. "co2_plume").
    vdb_path : str
        Absolute path to .vdb file.
    grid_names : list[str] | None
        Grid names to reference. Defaults to ["density"].
    purpose : str
        Annotation describing this volume's role.
    """
    if grid_names is None:
        grid_names = ["density"]

    volume_path = f"/World/Volumes/{name}"
    volume = UsdVol.Volume.Define(stage, volume_path)

    for grid_name in grid_names:
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
    prim.SetCustomDataByKey("created_by", "oco-viz/houdini-td")

    return prim
```

### Light Prim with Motivation

```python
"""Create a USD light prim with physical motivation annotation."""
from __future__ import annotations

from pxr import Usd, UsdLux  # type: ignore[import-untyped]


def add_distant_light(
    stage: Usd.Stage,
    name: str,
    color_temp: int,
    intensity: float,
    motivation: str,
    angle: float = 0.53,
) -> Usd.Prim:
    """Add a distant light with physical motivation.

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
    angle : float
        Angular diameter in degrees (sun = 0.53).
    """
    light_path = f"/World/Lights/{name}"
    light = UsdLux.DistantLight.Define(stage, light_path)
    light.GetColorTemperatureAttr().Set(float(color_temp))
    light.GetIntensityAttr().Set(intensity)
    light.GetEnableColorTemperatureAttr().Set(True)
    light.GetAngleAttr().Set(angle)

    # Annotations
    prim = stage.GetPrimAtPath(light_path)
    prim.SetCustomDataByKey("purpose", f"light: {motivation}")
    prim.SetCustomDataByKey("created_by", "oco-viz/houdini-td")
    prim.SetCustomDataByKey("color_temp_kelvin", color_temp)

    return prim
```

### Camera Setup

```python
"""Create a USD camera prim for Karma XPU rendering."""
from __future__ import annotations

from pxr import Gf, Usd, UsdGeom  # type: ignore[import-untyped]


def setup_camera(
    stage: Usd.Stage,
    focal_length: float = 35.0,
    sensor_width: float = 36.0,
    near_clip: float = 0.1,
    far_clip: float = 10000.0,
) -> Usd.Prim:
    """Configure the scene camera for Karma XPU rendering.

    Parameters
    ----------
    stage : Usd.Stage
        Target USD stage.
    focal_length : float
        Focal length in mm.
    sensor_width : float
        Sensor width in mm (36mm = full frame).
    near_clip : float
        Near clipping plane in meters.
    far_clip : float
        Far clipping plane in meters.
    """
    camera = UsdGeom.Camera.Define(stage, "/World/Camera")
    camera.GetFocalLengthAttr().Set(focal_length)
    camera.GetHorizontalApertureAttr().Set(sensor_width)
    camera.GetClippingRangeAttr().Set(Gf.Vec2f(near_clip, far_clip))

    # Annotations
    prim = stage.GetPrimAtPath("/World/Camera")
    prim.SetCustomDataByKey("purpose", "primary render camera")
    prim.SetCustomDataByKey("created_by", "oco-viz/houdini-td")
    prim.SetCustomDataByKey("focal_length_mm", focal_length)

    return prim
```

---

## Parameters

### Stage Global Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `up_axis` | string | Y | Stage up axis (always Y for Houdini/Karma) |
| `meters_per_unit` | float | 1.0 | Scale factor (always 1.0 for meters) |
| `time_codes_per_second` | float | 24 | Frame rate |
| `default_prim` | string | /World | Stage default prim path |
| `start_time_code` | int | 1 | First frame of the shot |
| `end_time_code` | int | 720 | Last frame (30 sec at 24 fps) |

### Prim Hierarchy Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `volumes_scope` | string | /World/Volumes | Parent scope for volume prims |
| `lights_scope` | string | /World/Lights | Parent scope for light prims |
| `camera_path` | string | /World/Camera | Camera prim path |
| `environment_scope` | string | /World/Environment | Environment scope |
| `materials_scope` | string | /World/Materials | Materials scope |

### Layer Composition Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_layer_suffix` | string | _base | Base layer filename suffix |
| `override_layer_suffix` | string | _override | Override layer filename suffix |
| `max_layer_depth` | int | 3 | Maximum composition arc depth |

---

## Anti-Patterns

### 1. The Flat Hierarchy

**Symptom:** All prims sit directly under /World -- volumes, lights, cameras, and
materials at the same level. The stage reads like an unsorted directory listing.

**Cause:** Skipping the hierarchy design and creating prims wherever is convenient.
"It loads, so it works."

**Fix:** Follow the standard hierarchy: /World/Volumes, /World/Lights, /World/Camera,
/World/Materials. Every prim must be reachable through a scoped parent. Flat hierarchies
break namespace isolation, selective loading, and composition overrides.

### 2. The Undocumented Prim

**Symptom:** A prim exists in the stage with no `purpose` annotation. Six months later
nobody knows why it is there or whether it can be safely removed.

**Cause:** Creating prims for technical convenience without documenting their role.

**Fix:** Every prim gets `purpose`, `source_data`, and `created_by` custom data at
creation time. If you cannot state the purpose, the prim should not exist.

### 3. The Monolithic Layer

**Symptom:** A single USD file contains the entire scene -- structure, overrides,
render settings, and artist adjustments. Any change requires modifying the whole file.
Per-tier overrides require duplicating the entire scene.

**Cause:** Treating USD as a single-file format instead of a composition system.

**Fix:** Separate base from override. The base layer defines structure and defaults.
Override layers contain only deltas. Tier-specific settings (scout vs. final render
resolution, sample counts) live in override layers, not the base. Multiple overrides
stack without touching the base.

### 4. The Wrong Units

**Symptom:** VDB volumes appear at the wrong scale in the Karma render. A 10-meter
plume renders as a 10-millimeter dot or a 10-kilometer cloud.

**Cause:** Stage `metersPerUnit` does not match the VDB grid's voxel spacing. The VDB
was authored in meters but the stage uses centimeters (metersPerUnit = 0.01).

**Fix:** Always set `metersPerUnit = 1.0`. All VDB grids in the oco-viz pipeline are
authored in meters. The stage must match. Verify by checking that the volume prim's
bounding box in the viewport matches the expected physical dimensions.

---

## Validation Checklist

- [ ] Stage up axis set to Y
- [ ] Meters per unit set to 1.0
- [ ] Time codes per second set to 24
- [ ] Default prim set to /World
- [ ] Start and end time codes match shot frame range
- [ ] Hierarchy follows standard: /World/Volumes, /World/Lights, /World/Camera, /World/Materials
- [ ] Every prim has `purpose` annotation
- [ ] Every asset prim has `source_data` annotation
- [ ] Every prim has `created_by` annotation
- [ ] No orphaned prims (all reachable from /World)
- [ ] Volume prims reference VDB files with correct grid names
- [ ] All referenced VDB files exist on disk
- [ ] Layer composition: base layer separate from override layer
- [ ] Stage loads in Karma XPU without manual intervention
- [ ] Volume bounding boxes match expected physical dimensions in meters
