---
name: hda-authoring
user-invocable: false
type: instruction
primary_owner: houdini-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# HDA Authoring -- Houdini Digital Asset Creation for Reusable VFX Tools

Every reusable operation in the oco-viz Houdini pipeline is packaged as a Houdini
Digital Asset (HDA). HDAs encapsulate SOP networks, parameter interfaces, and
documentation into a single versioned file that can be shared across shots, deployed
to render farms, and updated without breaking existing scenes. An HDA is a contract:
given these inputs and parameters, it produces this output. Breaking the contract
breaks every scene that references the asset.

> "An HDA is a function, not a file. It has inputs, outputs, and a version."

---

## Principle

HDAs are the reusable building blocks of the oco-viz Houdini pipeline. Each HDA wraps
a SOP network that performs a specific VDB processing operation -- smoothing, combining,
crust field computation, grain manifold generation. The internal network is generated
programmatically via the `hou` module, never by hand. The parameter interface exposes
only the knobs that lookdev artists need, with ranges derived from the lookdev bible
wedge tables. Every HDA is versioned, and version changes follow semantic rules.

---

## Procedure

### Step 1 -- Define HDA Structure

Every HDA follows a standard structure:

| Component | Purpose |
|-----------|---------|
| Inputs | VDB grids (density, vel, temperature) from upstream |
| Parameters | Wedge-friendly controls with ranges from lookdev bible |
| Internal network | SOP chain generated programmatically |
| Outputs | Processed VDB grids matching pipeline naming convention |
| Documentation | Help card describing purpose, parameters, version history |

### Step 2 -- Version Control

HDA files follow a strict naming convention:

```
{category}_{name}.{major}.{minor}.hda
```

| Component | Example | Rule |
|-----------|---------|------|
| Category | `sop`, `shop`, `lop` | Houdini operator category |
| Name | `soot_crust`, `grain_manifold` | Descriptive, snake_case |
| Major | `1` | Breaking change (input/output contract change) |
| Minor | `0` | Non-breaking change (new parameter, bug fix) |

Example: `sop_soot_crust.1.0.hda`, `sop_grain_manifold.2.1.hda`

**Version rules:**

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| New parameter with default | Minor | Add `blend_mode` with default "smooth" |
| Parameter range change | Minor | Widen `grain_amplitude` range |
| Input/output count change | Major | Add second VDB input |
| Output grid name change | Major | Rename output from "mask" to "crust" |
| Internal algorithm change | Minor (if output unchanged) | Optimize smoothing loop |

### Step 3 -- Parameter Interface Design

Parameters are organized into tabs with production-ready defaults and ranges:

| Tab | Contents |
|-----|----------|
| Main | Primary controls that artists adjust per-shot |
| Advanced | Fine-tuning controls with sensible defaults |
| Debug | Diagnostic outputs, bypass toggles, verbose logging |

**Parameter rules:**

- Every parameter has a default value from the lookdev bible.
- Every float/int parameter has a min/max range from wedge tables.
- Parameters are labeled with artist-friendly names (not code variable names).
- Wedge-critical parameters are marked in the help card.

### Step 4 -- Internal Network Generation

The HDA's internal SOP network is created programmatically:

1. Create the HDA definition via `hou.hda.definitionsInFile()`.
2. Build the internal network node-by-node using `createNode()`.
3. Wire parameters to internal nodes via channel references.
4. Set display/render flags on the output node.
5. Lock the HDA definition after validation.

### Step 5 -- Validation

Before saving an HDA:

1. Cook the output node with test input data.
2. Verify output grid names match pipeline convention.
3. Verify all parameters are accessible and produce expected results.
4. Test with edge cases: empty input, single-voxel input, maximum density.
5. Verify the HDA loads cleanly in a fresh Houdini session.

---

## Verified Code Templates

### Create HDA from SOP Network

```python
"""Create an HDA from a SOP network programmatically."""
from __future__ import annotations

import hou  # type: ignore[import-untyped]


def create_hda(
    geo_node: hou.Node,
    hda_path: str,
    hda_name: str,
    hda_label: str,
    version: str = "1.0",
    min_inputs: int = 1,
    max_inputs: int = 1,
) -> hou.HDADefinition:
    """Create an HDA from an existing SOP network.

    Parameters
    ----------
    geo_node : hou.Node
        The geo node containing the SOP network to wrap.
    hda_path : str
        Output file path for the .hda file.
    hda_name : str
        Internal operator name (e.g. "sop_soot_crust").
    hda_label : str
        Human-readable label (e.g. "Soot Crust").
    version : str
        Version string (e.g. "1.0").
    min_inputs : int
        Minimum number of inputs.
    max_inputs : int
        Maximum number of inputs.
    """
    # Get the subnet to wrap
    subnet = geo_node

    # Create the HDA definition
    hda_def = subnet.createDigitalAsset(
        name=hda_name,
        hda_file_name=hda_path,
        description=hda_label,
        min_num_inputs=min_inputs,
        max_num_inputs=max_inputs,
        version=version,
    )

    return hda_def
```

### Add Parameters to HDA

```python
"""Add a parameter interface to an HDA definition."""
from __future__ import annotations

import hou  # type: ignore[import-untyped]


def add_parameter_interface(
    hda_node: hou.Node,
) -> None:
    """Add lookdev parameters to an HDA.

    Parameters are organized into tabs with ranges from
    the lookdev bible wedge tables.
    """
    ptg = hda_node.parmTemplateGroup()

    # --- Main Tab ---
    main_folder = hou.FolderParmTemplate(
        "main_tab", "Main", folder_type=hou.folderType.Tabs,
    )

    # Crust threshold (from Technique 6 wedge table)
    main_folder.addParmTemplate(
        hou.FloatParmTemplate(
            "crust_threshold", "Crust Threshold",
            1,  # num components
            default_value=(0.4,),
            min=0.2, max=0.6,
            min_is_strict=True, max_is_strict=True,
            help="Gradient magnitude threshold for crust/interior transition",
        ),
    )

    # Blend width
    main_folder.addParmTemplate(
        hou.FloatParmTemplate(
            "blend_width", "Blend Width",
            1,
            default_value=(0.05,),
            min=0.02, max=0.15,
            min_is_strict=True, max_is_strict=True,
            help="Smooth transition width around crust threshold",
        ),
    )

    # Scattering anisotropy
    main_folder.addParmTemplate(
        hou.FloatParmTemplate(
            "scattering_anisotropy", "Scattering Anisotropy",
            1,
            default_value=(0.8,),
            min=0.6, max=0.9,
            min_is_strict=True, max_is_strict=True,
            help="Forward scattering strength (0=isotropic, 1=fully forward)",
        ),
    )

    ptg.append(main_folder)

    # --- Advanced Tab ---
    adv_folder = hou.FolderParmTemplate(
        "advanced_tab", "Advanced", folder_type=hou.folderType.Tabs,
    )

    adv_folder.addParmTemplate(
        hou.FloatParmTemplate(
            "crust_absorption", "Crust Absorption",
            1,
            default_value=(1.0,),
            min=0.8, max=1.0,
            help="Absorption coefficient for crust state",
        ),
    )

    adv_folder.addParmTemplate(
        hou.FloatParmTemplate(
            "interior_scattering", "Interior Scattering",
            1,
            default_value=(0.8,),
            min=0.5, max=0.95,
            help="Scattering coefficient for interior state",
        ),
    )

    ptg.append(adv_folder)

    # Apply
    hda_node.setParmTemplateGroup(ptg)
```

### Save and Version HDA

```python
"""Save and version an HDA with proper metadata."""
from __future__ import annotations

import hou  # type: ignore[import-untyped]


def save_hda(
    hda_node: hou.Node,
    hda_path: str,
    version: str,
    comment: str,
) -> None:
    """Save HDA with version metadata.

    Parameters
    ----------
    hda_node : hou.Node
        The HDA instance node.
    hda_path : str
        Output .hda file path.
    version : str
        Version string (e.g. "1.0").
    comment : str
        Version comment describing changes.
    """
    definition = hda_node.type().definition()

    # Set metadata
    definition.setVersion(version)
    definition.setComment(comment)

    # Save to file
    definition.save(hda_path)

    print(f"HDA saved: {hda_path} (v{version})")
```

---

## Parameters

### HDA Structure Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `hda_category` | string | Sop | Sop / Shop / Lop | Houdini operator category |
| `version_format` | string | {major}.{minor} | -- | Version string format |
| `min_inputs` | int | 1 | 0 - 4 | Minimum input connections |
| `max_inputs` | int | 1 | 0 - 4 | Maximum input connections |

### Parameter Interface Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `tab_count` | int | 3 | 1 - 5 | Number of parameter tabs (Main, Advanced, Debug) |
| `range_source` | string | lookdev_bible | -- | Source for parameter ranges |
| `default_source` | string | lookdev_bible | -- | Source for default values |
| `help_required` | bool | true | -- | Every parameter must have help text |

### Version Control Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `auto_version` | bool | false | -- | Auto-increment minor version on save |
| `require_comment` | bool | true | -- | Require version comment on save |
| `backup_previous` | bool | true | -- | Back up previous version before overwrite |

---

## Anti-Patterns

### 1. The Manual HDA

**Symptom:** An HDA was created by right-clicking in the Houdini GUI and selecting
"Create Digital Asset." The internal network was wired by hand. Nobody can reproduce
the exact parameter wiring or node connections.

**Cause:** Using the GUI as the authoring tool instead of scripting the HDA creation.
The resulting HDA cannot be regenerated from code, audited for correctness, or
updated systematically.

**Fix:** All HDAs are created via Hython scripts using `createDigitalAsset()`,
`parmTemplateGroup()`, and `createNode()`. The script is version-controlled. The
HDA file is a generated artifact, regenerable from the script.

### 2. The Unversioned HDA

**Symptom:** An HDA file is named `soot_crust.hda` with no version information.
Different versions of the file exist on different machines. Nobody knows which version
a scene references.

**Cause:** Skipping the version convention, treating the HDA as a single mutable file
rather than a versioned artifact.

**Fix:** Follow `{category}_{name}.{major}.{minor}.hda` naming. Increment minor for
non-breaking changes. Increment major for contract-breaking changes. Never overwrite
a released version -- create a new version instead.

### 3. The Missing Parameter Ranges

**Symptom:** An artist sets `crust_threshold` to 5.0 (the valid range is 0.2-0.6).
The cook produces garbage. The artist wastes hours debugging before realizing the
parameter was out of range.

**Cause:** Parameters created without min/max ranges or with ranges that do not match
the lookdev bible wedge tables.

**Fix:** Every float and int parameter has `min`, `max`, `min_is_strict`, and
`max_is_strict` set from the lookdev bible. The parameter interface prevents artists
from entering values that produce undefined behavior.

### 4. The Monolithic HDA

**Symptom:** A single HDA performs VDB import, smoothing, crust computation, emission
calculation, MaterialX assignment, and Karma ROP setup. It has 47 parameters across
a single tab. Any change risks breaking unrelated functionality.

**Cause:** Packing too much functionality into one asset. "It's convenient to have
everything in one node."

**Fix:** One HDA per operation. Each HDA has a focused purpose: `sop_soot_crust`
computes the crust field, `sop_grain_manifold` generates the grain field,
`sop_vdb_smooth` wraps smoothing with pipeline-standard parameters. Compose HDAs
in a network, do not merge them into one.

---

## Validation Checklist

- [ ] HDA created programmatically via Hython (not GUI)
- [ ] File naming follows `{category}_{name}.{major}.{minor}.hda`
- [ ] All parameters have min/max ranges from lookdev bible wedge tables
- [ ] All parameters have default values from lookdev bible
- [ ] All parameters have help text describing purpose and impact
- [ ] Parameters organized into tabs: Main, Advanced, Debug
- [ ] Internal network generated via `hou` API, not hand-wired
- [ ] Input/output contract documented in help card
- [ ] Output grid names match pipeline convention
- [ ] HDA cooks successfully with test input data
- [ ] Edge cases tested: empty input, single voxel, max density
- [ ] Version comment describes changes from previous version
- [ ] HDA loads cleanly in a fresh Houdini session
- [ ] No manual HDA editing after programmatic creation
