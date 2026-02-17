---
name: hython-standards
user-invocable: false
type: instruction
primary_owner: groundtruth
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Hython Standards — VFX Production Coding for Pipeline Integrity

Every asset must load. Format validation before creative evaluation. A grid that renders
beautifully in VTK but fails to import in Houdini is a pipeline break, and pipeline
breaks are the most expensive failures in production. These standards encode the naming
conventions, unit systems, and coding patterns that ensure every VTK-generated asset
flows seamlessly through the downstream Houdini/Karma XPU pipeline.

> "Fix it in pre, not post." — VFX production axiom

---

## Principle

The Hython/Python coding standards exist to guarantee interoperability between the
VTK generation stage (oco-viz) and the downstream Houdini processing stage. Every
naming convention, every unit choice, every metadata field is dictated by what Houdini
expects when it opens the file. Creative freedom operates within these constraints, never
outside them. A beautiful render that cannot be imported is a failure.

---

## Procedure

### Step 1 — Validate Unit System

Before writing any grid or geometry, confirm the unit system:

| Dimension | Unit | Standard | Violation Impact |
|-----------|------|----------|------------------|
| Length | meters | SI base unit | Wrong volume size in Houdini |
| Temperature | Kelvin | Absolute scale, 293-3000K | Wrong fire/emission colors |
| Velocity | m/s | SI derived | Broken fluid simulations |
| Voxel spacing | world_size / resolution | Explicit calculation | Scale mismatch |
| Time | seconds | SI base unit | Animation timing errors |

### Step 2 — Apply Grid Naming Convention

Grid names are the pipeline's addressing system. Houdini expects specific names:

| Grid Name | Content | Type | Notes |
|-----------|---------|------|-------|
| `density` | Primary density field | fog_volume | Must be the first grid |
| `vel` | Velocity field | vec3 | Components: vel.x, vel.y, vel.z |
| `temperature` | Temperature in Kelvin | fog_volume | Range: 293-3000K |
| `emission` | Emission intensity | fog_volume | For self-illuminating volumes |
| `mask` | Binary occupancy mask | fog_volume | 0.0 or 1.0 only |

Non-standard grid names require manual renaming in Houdini, which is error-prone and
breaks automated pipeline tools.

### Step 3 — Enforce Sparse Design

VDB's power comes from sparse storage. Every voxel with a value of exactly 0.0 is free
— it occupies no disk space and no memory. Dense grids waste 10x or more storage.

| Rule | Implementation | Impact |
|------|----------------|--------|
| Background = 0.0 | Set grid background value to exactly 0.0 | Free empty voxels |
| Active voxels only | Write non-zero values only where data exists | 10x file reduction |
| Prune after write | Call `grid.prune()` before saving | Removes false actives |
| Verify sparsity | Check active voxel count vs total voxels | Catch dense mistakes |

### Step 4 — Inject Required Metadata

Every grid must carry metadata that downstream tools read:

| Metadata Key | Type | Description |
|-------------|------|-------------|
| `name` | string | Grid name matching the naming convention |
| `class` | string | `fog_volume` for density, `level_set` for surfaces |
| `creator` | string | `oco-viz/{version}` |
| `voxel_size` | float | Explicit voxel spacing in meters |
| `file_bbox_min` | vec3 | World-space bounding box minimum |
| `file_bbox_max` | vec3 | World-space bounding box maximum |

### Step 5 — Validate Before Write

Run all validation checks before writing the file to disk. A failed validation means
the asset is not written — silent failures are never acceptable.

---

## Verified Code Templates

### OpenVDB Grid Creation with Proper Metadata

```python
"""Create an OpenVDB density grid with correct metadata for Houdini."""
from __future__ import annotations

import pyopenvdb as vdb  # type: ignore[import-untyped]
import numpy as np

def create_density_grid(
    data: np.ndarray,
    voxel_size: float,
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> vdb.FloatGrid:
    """Create a sparse density grid from numpy array.

    Parameters
    ----------
    data : np.ndarray
        3D density array. Zeros become background (sparse).
    voxel_size : float
        Voxel spacing in meters (world_size / resolution).
    origin : tuple
        World-space origin in meters.
    """
    grid = vdb.FloatGrid()
    grid.name = "density"
    grid.gridClass = vdb.GridClass.FOG_VOLUME
    grid.transform = vdb.createLinearTransform(voxelSize=voxel_size)

    # Copy only non-zero values (sparse design)
    grid.copyFromArray(data, tolerance=0.0)

    # Inject metadata
    grid["creator"] = "oco-viz"
    grid["voxel_size"] = voxel_size

    # Prune false actives
    grid.prune()

    return grid
```

### VTK Volume Actor Setup with Correct Spacing

```python
"""Create a VTK volume actor with explicit voxel spacing."""
from __future__ import annotations

import vtk  # type: ignore[import-untyped]
import numpy as np

def create_vtk_volume(
    data: np.ndarray,
    voxel_size: float,
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> vtk.vtkVolume:
    """Create VTK volume with correct spacing in meters.

    Parameters
    ----------
    data : np.ndarray
        3D density array (float32).
    voxel_size : float
        Voxel spacing in meters (world_size / resolution).
    origin : tuple
        World-space origin in meters.
    """
    image_data = vtk.vtkImageData()
    image_data.SetDimensions(*data.shape)
    image_data.SetSpacing(voxel_size, voxel_size, voxel_size)
    image_data.SetOrigin(*origin)

    scalars = vtk.vtkFloatArray()
    scalars.SetNumberOfValues(data.size)
    flat = data.ravel(order="F")  # VTK expects Fortran order
    for i in range(data.size):
        scalars.SetValue(i, float(flat[i]))
    image_data.GetPointData().SetScalars(scalars)

    mapper = vtk.vtkSmartVolumeMapper()
    mapper.SetInputData(image_data)

    volume = vtk.vtkVolume()
    volume.SetMapper(mapper)

    return volume
```

### Hython Batch Processing Template

```python
"""Hython batch processing template for OpenVDB import and validation."""
from __future__ import annotations

# Hython-specific imports (run inside Houdini's Python)
import hou  # type: ignore[import-untyped]

def validate_and_import_vdb(
    vdb_path: str,
    expected_grids: list[str] | None = None,
) -> hou.Node:
    """Import VDB and validate grid names and metadata.

    Parameters
    ----------
    vdb_path : str
        Absolute path to .vdb file.
    expected_grids : list[str] | None
        Expected grid names. Defaults to ["density"].
    """
    if expected_grids is None:
        expected_grids = ["density"]

    # Create File node
    obj = hou.node("/obj")
    geo = obj.createNode("geo", "imported_volume")
    file_node = geo.createNode("file")
    file_node.parm("file").set(vdb_path)

    # Validate grids
    file_node.cook(force=True)
    geo_data = file_node.geometry()

    found_grids = [prim.attribValue("name") for prim in geo_data.prims()]

    for expected in expected_grids:
        if expected not in found_grids:
            msg = f"Missing grid '{expected}' in {vdb_path}. Found: {found_grids}"
            raise ValueError(msg)

    return file_node
```

---

## Parameters

### Unit System Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `length_unit` | string | meters | -- | World-space length unit (always meters) |
| `temp_unit` | string | kelvin | -- | Temperature unit (always Kelvin) |
| `velocity_unit` | string | m/s | -- | Velocity unit (always m/s) |
| `time_unit` | string | seconds | -- | Time unit (always seconds) |

### Sparse Design Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `background_value` | float | 0.0 | 0.0 | Grid background (must be exactly 0.0) |
| `prune_tolerance` | float | 0.0 | 0.0 - 1e-7 | Pruning tolerance for false actives |
| `sparsity_check` | bool | true | -- | Verify active/total voxel ratio |
| `max_active_ratio` | float | 0.3 | 0.01 - 0.5 | Maximum active voxels / total voxels |

### File Size Budget Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `scout_max_mb` | int | 100 | 10 - 200 | Scout tier max file size in MB |
| `preview_max_mb` | int | 1000 | 100 - 2000 | Preview tier max file size in MB |
| `final_max_mb` | int | 10000 | 1000 - 20000 | Final tier max file size in MB |

---

## Anti-Patterns

### 1. The Implicit Scale

**Symptom:** VDB file loads in Houdini but the volume is 1000x too large or too small.
Camera, lights, and simulation parameters are all wrong because voxel spacing was not
explicitly set.

**Cause:** Relying on default voxel spacing (often 1.0 in arbitrary units) instead of
computing `world_size / resolution` and setting it explicitly on the grid transform.

**Fix:** Always compute and set voxel spacing explicitly:
`voxel_size = world_size_meters / resolution`. Inject `voxel_size` as grid metadata.
Validate by checking that the grid's world-space bounding box matches the expected
physical dimensions.

### 2. The Dense Grid

**Symptom:** VDB file is 2GB when it should be 200MB. Load times are 10x expected.
Memory usage spikes during Houdini import.

**Cause:** Writing non-zero values to every voxel in the grid, including regions that
should be empty space. The grid is dense when it should be sparse.

**Fix:** Ensure background value is exactly 0.0. Write values only where data exists.
Call `grid.prune()` after population. Verify with active voxel count: if
`active_count / total_voxels > 0.3`, the grid is suspiciously dense.

### 3. The Silent Failure

**Symptom:** A VDB file is written to disk without error, but downstream Houdini
processing fails with cryptic messages about missing grids or wrong types.

**Cause:** No validation step between grid creation and file write. The code assumes
success because no Python exception was raised.

**Fix:** Validate every grid before writing: check name matches convention, class is
correct, metadata is present, voxel spacing is set, sparse ratio is acceptable. Raise
an explicit error with diagnostic information if any check fails. Never write a grid
that has not passed validation.

### 4. The Renamed Grid

**Symptom:** Pipeline scripts break because the density grid is named "rho" or "dens"
or "volume_density" instead of "density". Houdini VDB SOPs cannot find the expected grid.

**Cause:** Using project-specific or physics-convention naming instead of the Houdini
pipeline standard.

**Fix:** Use exactly the names in the naming convention table: `density`, `vel`,
`temperature`. These are not suggestions — they are the pipeline's addressing system.
If a custom grid is needed, add it alongside the required grids, never instead of them.

---

## Validation Checklist

- [ ] All lengths in meters (SI)
- [ ] All temperatures in Kelvin (293-3000K range)
- [ ] All velocities in m/s
- [ ] Voxel spacing explicitly set as `world_size / resolution`
- [ ] Grid names follow convention: `density`, `vel`, `temperature`
- [ ] Grid class set correctly: `fog_volume` for density, `vec3` for velocity
- [ ] Background value is exactly 0.0
- [ ] `grid.prune()` called before file write
- [ ] Active voxel ratio below 0.3 (sparse verification)
- [ ] Required metadata injected: name, class, creator, voxel_size
- [ ] File size within tier budget (Scout < 100MB, Preview < 1GB, Final < 10GB)
- [ ] Validation checks run before file write (no silent failures)
- [ ] Asset loads successfully in Houdini without manual intervention
