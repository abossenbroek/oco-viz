---
name: openvdb-production
user-invocable: false
type: instruction
primary_owner: groundtruth
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# OpenVDB Production — Grid Metadata IS the Pipeline

Grid metadata IS the pipeline. Wrong metadata breaks every downstream tool. An OpenVDB
file without correct grid names, class annotations, and voxel size is not a production
asset — it is a debugging liability. These rules encode the metadata, naming, sparse
design, and file size constraints that make VDB files pipeline-safe from the moment they
are written.

> "The grid metadata is the API contract with every tool that reads it."

---

## Principle

OpenVDB is the industry standard for sparse volumetric data. Its power lies in two
properties: spatial sparsity (only active voxels consume storage) and rich metadata
(every grid carries self-describing information). Both properties must be exploited
correctly. A dense VDB file with missing metadata is worse than no file at all — it
wastes storage, misleads downstream tools, and creates false confidence that the asset
is production-ready.

The groundtruth agent is responsible for enforcing these rules. No VDB file passes
validation without correct metadata, correct naming, correct sparsity, and correct
file size.

---

## Procedure

### Step 1 — Define Grid Structure

Before creating any grid, determine the required fields for the sequence:

| Grid | Name | Class | Content | Required |
|------|------|-------|---------|----------|
| Primary density | `density` | fog_volume | CO2 concentration field | Always |
| Temperature | `temperature` | fog_volume | Kelvin (293-3000K) | When thermal viz needed |
| Velocity | `vel` | vec3 | Wind field in m/s | When motion viz needed |
| Emission | `emission` | fog_volume | Self-illumination intensity | When hot gas present |
| Mask | `mask` | fog_volume | Binary occupancy (0.0 or 1.0) | For compositing |

### Step 2 — Create Grids with Correct Metadata

Every grid must be created with all required metadata fields populated at creation time,
not as a post-processing step:

| Metadata Key | Type | Example | Description |
|-------------|------|---------|-------------|
| `name` | string | `density` | Grid name matching naming convention |
| `class` | string | `fog_volume` | Grid class for downstream tool behavior |
| `creator` | string | `oco-viz/1.0` | Creating tool and version |
| `voxel_size` | float | `0.125` | Voxel spacing in meters |
| `world_bbox_min` | vec3 | `(-5.0, 0.0, -5.0)` | World-space bounding box min (meters) |
| `world_bbox_max` | vec3 | `(5.0, 20.0, 5.0)` | World-space bounding box max (meters) |
| `data_range_min` | float | `0.0` | Minimum data value in active voxels |
| `data_range_max` | float | `1.0` | Maximum data value in active voxels |
| `tier` | string | `scout` | Production tier (scout / preview / final) |
| `source_dataset` | string | `oco3_20240115` | Source satellite dataset identifier |

### Step 3 — Enforce Sparse Design

Sparsity is not optional. Every empty region of the volume must be represented by the
grid's background value (exactly 0.0), consuming zero storage.

**Sparse design requirements:**

1. **Background value = 0.0** — Set at grid creation. All voxels outside the plume have
   this value and consume no disk or memory.

2. **Active voxels only where data exists** — Write non-zero values only to voxels that
   contain actual density/temperature/velocity data.

3. **Prune after population** — Call `grid.prune(tolerance=0.0)` after writing all
   values. This collapses uniform tiles and removes false actives.

4. **Verify sparsity** — Check the active-to-total voxel ratio. For typical plume data,
   active voxels should be 5-25% of the total bounding box volume. A ratio above 30%
   is suspicious and likely indicates a sparsity failure.

### Step 4 — Validate File Size Against Budget

File size is a hard constraint, not a guideline:

| Tier | Resolution | Max File Size | Typical Size |
|------|-----------|---------------|-------------|
| Scout | 128 cubed | 100 MB | 5 - 30 MB |
| Preview | 512 cubed | 1 GB | 100 - 500 MB |
| Final | 1024 cubed | 10 GB | 1 - 5 GB |

Files exceeding the budget indicate a sparsity failure, an incorrect resolution, or
data that should be thinned. The fix is always upstream — never compress a dense grid
when you should have created a sparse one.

### Step 5 — Write and Verify

Write the VDB file, then immediately re-read it and verify:

- All expected grids are present with correct names
- Metadata matches what was written
- Active voxel counts match expectations
- File size is within budget
- Grid transforms reproduce the correct world-space bounding box

---

## Verified Code Templates

### Grid Creation and Metadata Injection

```python
"""Create production-grade OpenVDB grids with full metadata."""
from __future__ import annotations

import pyopenvdb as vdb  # type: ignore[import-untyped]
import numpy as np

def create_production_grid(
    data: np.ndarray,
    name: str,
    voxel_size: float,
    grid_class: str = "fog_volume",
    tier: str = "scout",
    source_dataset: str = "unknown",
) -> vdb.FloatGrid:
    """Create a sparse VDB grid with production metadata.

    Parameters
    ----------
    data : np.ndarray
        3D float32 array. Zeros become sparse background.
    name : str
        Grid name (must follow naming convention).
    voxel_size : float
        Voxel spacing in meters.
    grid_class : str
        Grid class: fog_volume or level_set.
    tier : str
        Production tier: scout, preview, or final.
    source_dataset : str
        Identifier for the source satellite dataset.
    """
    grid = vdb.FloatGrid()
    grid.name = name
    grid.transform = vdb.createLinearTransform(voxelSize=voxel_size)

    if grid_class == "fog_volume":
        grid.gridClass = vdb.GridClass.FOG_VOLUME
    elif grid_class == "level_set":
        grid.gridClass = vdb.GridClass.LEVEL_SET

    # Sparse copy — only non-zero values become active
    grid.copyFromArray(data, tolerance=0.0)
    grid.prune(tolerance=0.0)

    # Inject production metadata
    grid["creator"] = "oco-viz"
    grid["voxel_size"] = voxel_size
    grid["tier"] = tier
    grid["source_dataset"] = source_dataset

    # Data range from active voxels
    active = data[data != 0.0]
    if active.size > 0:
        grid["data_range_min"] = float(np.min(active))
        grid["data_range_max"] = float(np.max(active))

    return grid
```

### Sparse Verification

```python
"""Verify VDB grid sparsity meets production requirements."""
from __future__ import annotations

import pyopenvdb as vdb  # type: ignore[import-untyped]

def verify_sparsity(
    grid: vdb.FloatGrid,
    max_active_ratio: float = 0.3,
) -> dict[str, object]:
    """Check that a grid is properly sparse.

    Parameters
    ----------
    grid : vdb.FloatGrid
        Grid to verify.
    max_active_ratio : float
        Maximum acceptable active/total voxel ratio.

    Returns
    -------
    dict
        Sparsity report with pass/fail status.
    """
    active_count = grid.activeVoxelCount()
    bbox = grid.evalActiveVoxelBoundingBox()

    if bbox is None:
        return {"status": "pass", "active_count": 0, "note": "empty grid"}

    dims = [bbox[1][i] - bbox[0][i] + 1 for i in range(3)]
    total_in_bbox = dims[0] * dims[1] * dims[2]
    ratio = active_count / total_in_bbox if total_in_bbox > 0 else 0.0

    return {
        "status": "pass" if ratio <= max_active_ratio else "fail",
        "active_count": active_count,
        "bbox_total": total_in_bbox,
        "active_ratio": round(ratio, 4),
        "threshold": max_active_ratio,
    }
```

### File Write with Post-Write Verification

```python
"""Write VDB file with immediate re-read verification."""
from __future__ import annotations

import os

import pyopenvdb as vdb  # type: ignore[import-untyped]

def write_and_verify(
    grids: list[vdb.FloatGrid],
    output_path: str,
    max_size_mb: int = 100,
) -> dict[str, object]:
    """Write VDB file and verify integrity.

    Parameters
    ----------
    grids : list[vdb.FloatGrid]
        Grids to write.
    output_path : str
        Output .vdb file path.
    max_size_mb : int
        Maximum acceptable file size in MB.
    """
    vdb.write(output_path, grids=grids)

    # Verify file size
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    if size_mb > max_size_mb:
        msg = f"File size {size_mb:.1f}MB exceeds budget {max_size_mb}MB"
        raise ValueError(msg)

    # Re-read and verify grids
    read_grids = vdb.readAll(output_path)
    written_names = {g.name for g in grids}
    read_names = {g.name for g in read_grids}

    if written_names != read_names:
        msg = f"Grid mismatch: wrote {written_names}, read {read_names}"
        raise ValueError(msg)

    return {
        "status": "pass",
        "file_size_mb": round(size_mb, 2),
        "grid_count": len(read_grids),
        "grid_names": sorted(read_names),
    }
```

---

## Parameters

### Grid Naming Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `density_name` | string | density | Primary density grid name |
| `temperature_name` | string | temperature | Temperature grid name |
| `velocity_name` | string | vel | Velocity grid name |
| `emission_name` | string | emission | Emission intensity grid name |
| `mask_name` | string | mask | Binary occupancy mask name |

### Metadata Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | yes | Grid name matching naming convention |
| `class` | string | yes | fog_volume or level_set |
| `creator` | string | yes | Creating tool identifier |
| `voxel_size` | float | yes | Voxel spacing in meters |
| `tier` | string | yes | scout / preview / final |
| `source_dataset` | string | yes | Source data identifier |
| `data_range_min` | float | yes | Minimum active voxel value |
| `data_range_max` | float | yes | Maximum active voxel value |

### Sparse Design Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `background_value` | float | 0.0 | 0.0 | Must be exactly 0.0 |
| `prune_tolerance` | float | 0.0 | 0.0 - 1e-7 | Tolerance for pruning false actives |
| `max_active_ratio` | float | 0.3 | 0.01 - 0.5 | Alert threshold for dense grids |

### File Size Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `scout_max_mb` | int | 100 MB maximum for scout tier |
| `preview_max_mb` | int | 1000 MB maximum for preview tier |
| `final_max_mb` | int | 10000 MB maximum for final tier |

---

## Anti-Patterns

### 1. The Renamed Grid

**Symptom:** Downstream Houdini tools fail to find the density grid because it is named
`rho`, `concentration`, `co2_density`, or any other non-standard name.

**Cause:** Using domain-specific naming (atmospheric science conventions, custom project
names) instead of the Houdini pipeline standard.

**Fix:** Grid names are `density`, `vel`, `temperature`, `emission`, `mask`. These
names are not configurable — they are the pipeline contract. If additional grids are
needed for domain-specific data, add them alongside the standard grids, never as
replacements.

### 2. The Dense Fill

**Symptom:** VDB file is unexpectedly large. Active voxel ratio exceeds 30%.
Processing is slow. Memory consumption is 10x expected.

**Cause:** Writing non-zero values to voxels that should be empty, either by
initializing the array with a non-zero default, or by not masking the data to the plume
boundary before grid population.

**Fix:** Initialize data arrays with 0.0. Apply the plume boundary mask before writing
to the grid. Set grid background to 0.0. Call `prune()` after population. Verify
sparsity before writing to disk.

### 3. The Metadata-Free Grid

**Symptom:** VDB file loads but downstream tools cannot determine voxel size, data
range, source dataset, or production tier. Manual inspection is required for every
processing step.

**Cause:** Treating metadata as optional documentation rather than required pipeline
data. "The data is in the grid — you can compute the rest."

**Fix:** Inject all required metadata at grid creation time: name, class, creator,
voxel_size, tier, source_dataset, data_range_min, data_range_max. Metadata is not
documentation — it is the grid's self-description that downstream tools read
programmatically.

### 4. The Unverified Write

**Symptom:** A VDB file is written successfully (no Python errors) but contains
corrupted data, missing grids, or incorrect metadata. The problem is discovered hours
later during Houdini processing.

**Cause:** No post-write verification step. The code trusts that `vdb.write()` succeeded
because it did not raise an exception — but file system errors, truncation, and
serialization bugs can produce invalid files silently.

**Fix:** After every write, re-read the file and verify: correct grid count, correct
grid names, metadata matches, file size within budget. This verification adds seconds
and prevents hours of debugging.

---

## Validation Checklist

- [ ] Grid names follow convention: `density`, `vel`, `temperature`, `emission`, `mask`
- [ ] Grid class set correctly: `fog_volume` for scalar fields, `vec3` for velocity
- [ ] All required metadata present: name, class, creator, voxel_size, tier, source_dataset
- [ ] Data range metadata (min/max) populated from active voxels
- [ ] Background value is exactly 0.0
- [ ] `grid.prune()` called after population
- [ ] Active voxel ratio below 0.3 (sparsity verified)
- [ ] File size within tier budget (Scout < 100MB, Preview < 1GB, Final < 10GB)
- [ ] Post-write verification: re-read and check grid names, count, metadata
- [ ] Voxel size set explicitly as `world_size / resolution`
- [ ] World-space bounding box metadata matches expected physical dimensions
- [ ] Temperature grids use Kelvin (293-3000K range)
- [ ] Velocity grids use m/s
