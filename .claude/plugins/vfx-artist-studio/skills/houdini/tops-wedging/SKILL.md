---
name: tops-wedging
user-invocable: false
type: instruction
primary_owner: houdini-td
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# TOPs Wedging -- PDG Network for Parallel Parameter Wedging (Contact Sheet Bible)

The Contact Sheet Bible (lookdev bible Technique 7) requires 100 parameter variations
rendered as a single contact sheet before any shot is animated. This is not optional
creative exploration -- it is a production gate. Lookdev must be locked on paper before
animation rendering begins. PDG/TOPs (Procedural Dependency Graph / Task Operator
Network) automates the wedge generation, parallel rendering, and contact sheet assembly
as a reproducible, farm-submittable graph.

> "Print everything, circle the winners, lock before animating."

---

## Principle

Wedging replaces hand-tuning. Instead of an artist manually adjusting parameters and
rendering test frames, a TOPs graph systematically explores the parameter space defined
by the lookdev bible wedge tables. The result is a 10x10 contact sheet mosaic showing
100 variations of a single representative frame. The artist's job shifts from "tune
parameters" to "select the winner" -- a fundamentally faster and more rigorous process.
The 3-day time box from wedge submission to locked lookdev enforces discipline.

---

## Procedure

### Step 1 -- Define Wedge Parameters

Parameter ranges come from the lookdev bible wedge tables (Techniques 1-6):

| Parameter | Range | Steps | Source Technique |
|-----------|-------|-------|-----------------|
| `grain_amplitude` | 0.02 - 0.10 | 5 | Technique 1: Paper Grain Manifold |
| `viscosity_strength` | 0.2 - 0.6 | 4 | Technique 2: Sedimentary Motion |
| `emission_intensity` | 0.8 - 2.5 | 5 | Technique 3: Curvature-Driven Emission |
| `crust_threshold` | 0.25 - 0.55 | derived | Technique 6: Soot Crust |
| `scattering_anisotropy` | 0.65 - 0.85 | derived | Technique 6: Soot Crust |

**Standard wedge:** 5 x 4 x 5 = 100 variations. The crust and anisotropy parameters
are paired with the remaining combinations to fill exactly 100 iterations.

### Step 2 -- Build TOPs Wedge Graph

The PDG graph has this structure:

```
[Wedge] -> [HDA Cook] -> [Karma Render] -> [Contact Sheet] -> [Parameter Log]
```

| Node | Type | Purpose |
|------|------|---------|
| Wedge | `wedge` | Generate 100 parameter combinations |
| HDA Cook | `ropfetch` or `hscript` | Apply wedge parameters to SOP/LOP network |
| Karma Render | `ropfetch` | Render single frame at final tier per variation |
| Contact Sheet | `imagemagick` or `ffmpeg` | Assemble 10x10 mosaic |
| Parameter Log | `pythonscript` | Write CSV/JSON log mapping variation to parameters |

### Step 3 -- Configure Render Settings

Each wedge variation renders at **final tier settings** for representative quality:

| Setting | Value |
|---------|-------|
| VDB Resolution | 1024^3 |
| Samples per Pixel | 512 + OIDN |
| Render Resolution | 4096x2160 (4K DCI) |
| Frame Count | 1 (single representative frame) |
| Approx. per-frame time | ~22 min |
| Total wedge time | ~37 GPU-hours |

### Step 4 -- Review Process

The review follows a strict elimination process:

| Step | Action | Output |
|------|--------|--------|
| 1 | Generate 10x10 contact sheet at screen resolution | Single mosaic image |
| 2 | Eliminate obvious failures | Remove blowout, banding, invisible grain, no crust |
| 3 | Circle top 10 candidates | Annotated contact sheet |
| 4 | Render top 10 at full resolution | 10 full-resolution frames |
| 5 | Print top 5 on Hahnemuhle Photo Rag Baryta 315 gsm | Physical prints, 13x19" |
| 6 | Evaluate on paper under D50 illuminant | Gallery-wall test |
| 7 | Lock winning parameter set | Parameters frozen for shot |

### Step 5 -- Time Box Enforcement

**3 calendar days maximum** from wedge submission to locked lookdev:

| Day | Activity |
|-----|----------|
| Day 1 | Submit wedge to farm, generate contact sheet, initial triage |
| Day 2 | Full-resolution renders of top 10, print top 5 |
| Day 3 | Paper evaluation, parameter lock, sign-off |

If no satisfactory result after 3 days, escalate to creative director for scope
reduction. Do not extend the time box.

---

## Verified Code Templates

### TOPs Wedge Graph Creation in Hython

```python
#!/usr/bin/env hython
"""Create a PDG/TOPs wedge graph for Contact Sheet Bible lookdev."""
from __future__ import annotations

import json
import sys

import hou  # type: ignore[import-untyped]


# Wedge parameter definitions from lookdev bible
WEDGE_PARAMS = {
    "grain_amplitude": {
        "range": (0.02, 0.10),
        "steps": 5,
        "technique": "T1: Paper Grain Manifold",
    },
    "viscosity_strength": {
        "range": (0.2, 0.6),
        "steps": 4,
        "technique": "T2: Sedimentary Motion",
    },
    "emission_intensity": {
        "range": (0.8, 2.5),
        "steps": 5,
        "technique": "T3: Curvature-Driven Emission",
    },
}

CONTACT_SHEET_GRID = (10, 10)  # 10 columns x 10 rows = 100 variations


def create_wedge_graph(
    top_net: hou.Node,
    karma_rop_path: str,
    output_dir: str,
    frame: int = 1,
) -> hou.Node:
    """Build a PDG wedge graph for lookdev parameter exploration.

    Parameters
    ----------
    top_net : hou.Node
        The TOP network node to build in.
    karma_rop_path : str
        Path to the Karma ROP to render with.
    output_dir : str
        Output directory for rendered frames and contact sheet.
    frame : int
        The representative frame number to render.

    Returns
    -------
    hou.Node
        The final contact sheet node.
    """
    # --- Wedge Node ---
    wedge = top_net.createNode("wedge", "lookdev_wedge")

    # Add wedge attributes for each parameter
    wedge_idx = 0
    for param_name, param_def in WEDGE_PARAMS.items():
        low, high = param_def["range"]
        steps = param_def["steps"]

        wedge.parm(f"wedgeattribs").set(wedge_idx + 1)
        wedge.parm(f"name{wedge_idx}").set(param_name)
        wedge.parm(f"type{wedge_idx}").set(1)  # float
        wedge.parm(f"range{wedge_idx}x").set(low)
        wedge.parm(f"range{wedge_idx}y").set(high)
        wedge.parm(f"steps{wedge_idx}").set(steps)
        wedge_idx += 1

    # --- ROP Fetch (Karma Render) ---
    rop_fetch = top_net.createNode("ropfetch", "render_variation")
    rop_fetch.parm("roppath").set(karma_rop_path)
    rop_fetch.parm("f1").set(frame)
    rop_fetch.parm("f2").set(frame)
    rop_fetch.setInput(0, wedge)

    # --- Parameter Log ---
    param_log = top_net.createNode("pythonscript", "log_params")
    param_log.parm("script").set(
        'import json\n'
        'work_item = kwargs["work_item"]\n'
        'params = {a.name: a.value for a in work_item.attribs}\n'
        'log_path = work_item.tempDir + "/params.json"\n'
        'with open(log_path, "w") as f:\n'
        '    json.dump(params, f, indent=2)\n'
    )
    param_log.setInput(0, rop_fetch)

    # --- Wait for All ---
    wait = top_net.createNode("waitforall", "collect")
    wait.setInput(0, param_log)

    # --- Contact Sheet Assembly ---
    contact = top_net.createNode("pythonscript", "assemble_contact_sheet")
    cols, rows = CONTACT_SHEET_GRID
    contact.parm("script").set(
        f'import subprocess\n'
        f'work_items = kwargs["work_items"]\n'
        f'image_paths = [wi.resultData[0].tag for wi in work_items]\n'
        f'# Use ImageMagick montage for 10x10 grid\n'
        f'cmd = ["montage"] + image_paths\n'
        f'cmd += ["-tile", "{cols}x{rows}", "-geometry", "+2+2"]\n'
        f'cmd += ["{output_dir}/contact_sheet.jpg"]\n'
        f'subprocess.run(cmd, check=True)\n'
    )
    contact.setInput(0, wait)

    # Layout
    top_net.layoutChildren()

    return contact


def main() -> int:
    """Create wedge graph from command line."""
    hou.hipFile.load(sys.argv[1] if len(sys.argv) > 1 else "scene.hip")

    karma_rop = sys.argv[2] if len(sys.argv) > 2 else "/stage/karma_final"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "$HIP/wedge_output"

    # Create TOP network
    obj = hou.node("/obj")
    top_net = obj.createNode("topnet", "lookdev_wedge_net")

    try:
        contact_node = create_wedge_graph(top_net, karma_rop, output_dir)
    except hou.OperationFailed as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    hou.hipFile.save()
    print(f"SUCCESS: Wedge graph created with {contact_node.path()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### Parameter Combination Log

```python
"""Generate a CSV log of all wedge parameter combinations."""
from __future__ import annotations

import csv
import itertools
from pathlib import Path


def generate_wedge_log(
    output_path: str,
    params: dict[str, dict],
) -> int:
    """Write a CSV log of all parameter combinations.

    Parameters
    ----------
    output_path : str
        Path to output CSV file.
    params : dict
        Parameter definitions with range and steps.

    Returns
    -------
    int
        Total number of combinations.
    """
    # Generate per-parameter value lists
    param_values = {}
    for name, defn in params.items():
        low, high = defn["range"]
        steps = defn["steps"]
        param_values[name] = [
            low + (high - low) * i / (steps - 1)
            for i in range(steps)
        ]

    # Cartesian product
    names = list(param_values.keys())
    all_combos = list(itertools.product(*param_values.values()))

    with Path(output_path).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["variation_id", *names])
        for idx, combo in enumerate(all_combos):
            writer.writerow([idx, *[f"{v:.4f}" for v in combo]])

    return len(all_combos)
```

---

## Parameters

### Wedge Parameters (from Lookdev Bible)

| Parameter | Range | Steps | Source Technique |
|-----------|-------|-------|-----------------|
| `grain_amplitude` | 0.02 - 0.10 | 5 | T1: Paper Grain Manifold |
| `viscosity_strength` | 0.2 - 0.6 | 4 | T2: Sedimentary Motion |
| `emission_intensity` | 0.8 - 2.5 | 5 | T3: Curvature-Driven Emission |
| `crust_threshold` | 0.25 - 0.55 | derived | T6: Soot Crust |
| `scattering_anisotropy` | 0.65 - 0.85 | derived | T6: Soot Crust |

### Contact Sheet Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `contact_sheet_grid` | tuple | (10, 10) | -- | Grid layout for mosaic (cols x rows) |
| `total_variations` | int | 100 | 50 - 200 | Total parameter combinations |
| `render_tier` | string | final | -- | Render at final tier for representative quality |
| `representative_frame` | int | 1 | -- | Single frame rendered per variation |
| `output_format` | string | jpg | jpg / png | Contact sheet image format |

### Time Box Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `time_box_days` | int | 3 | 3 | Maximum days from wedge to locked lookdev |
| `top_candidates` | int | 10 | 5 - 20 | Number of candidates for full-resolution render |
| `print_count` | int | 5 | 3 - 10 | Number of prints for paper evaluation |
| `print_paper` | string | Hahnemuhle Photo Rag Baryta 315 gsm | -- | Print substrate |
| `print_size` | string | 13x19" | -- | Print dimensions |

---

## Anti-Patterns

### 1. The Hand-Tuner

**Symptom:** An artist spends 5 days manually adjusting shader parameters, rendering
test frames one at a time, and saying "I think this one looks better." After a week,
lookdev is still not locked.

**Cause:** Treating lookdev as an iterative manual process instead of a systematic
parameter sweep. The artist is exploring a 5-dimensional parameter space one point
at a time.

**Fix:** Use the TOPs wedge graph to explore the full parameter space in parallel.
100 variations render in ~37 GPU-hours on the farm. The contact sheet shows the entire
space at once. The artist selects from the results instead of generating them.
The 3-day time box enforces the discipline.

### 2. The Exceeded Time Box

**Symptom:** Day 4, day 5, day 7 -- lookdev is still not locked. Each day brings "one
more variation" and "let me try this different range." The animation render schedule
is delayed.

**Cause:** No hard deadline on the lookdev phase. The pursuit of the "perfect" parameter
set prevents progress.

**Fix:** 3 calendar days maximum. If no satisfactory result after 3 days, escalate to
creative director for scope reduction (fewer techniques, narrower ranges). Do not
extend the time box. A good-enough locked lookdev rendered on time beats a perfect
lookdev that delays the exhibition.

### 3. The Wrong Tier Wedge

**Symptom:** The contact sheet was rendered at scout tier (64 spp, HD resolution). The
winning parameters look good at scout but produce different results at final tier
because OIDN denoising, higher bounce counts, and finer step size change the visual
appearance.

**Cause:** Wedging at a lower tier to save render time. The scout-to-final gap is too
large for reliable parameter selection.

**Fix:** Always wedge at final tier settings (512 spp + OIDN, 4K). The 22 min per
frame cost is justified: 100 frames at ~37 GPU-hours on RTX 6000 Ada costs approximately
$41 in compute. This is a fraction of the cost of re-rendering 720 animation frames
because the lookdev was locked at the wrong tier.

### 4. The Partial Wedge

**Symptom:** Only 2 of the 5 key parameters are wedged. The locked lookdev has a good
`crust_threshold` but the `grain_amplitude` was never explored -- it defaults to 0.05
and nobody knows if 0.08 would be better.

**Cause:** Wedging only the "obvious" parameters and leaving others at defaults.
"We can adjust those later."

**Fix:** Wedge all parameters listed in the lookdev bible wedge tables. The 5 x 4 x 5
grid is designed to cover the interaction effects between parameters. A good
`crust_threshold` with a bad `grain_amplitude` is still a bad lookdev. If the total
combinations exceed 100, prioritize the parameters with the widest perceptual impact
and pair the others.

---

## Validation Checklist

- [ ] All lookdev bible wedge parameters included in the wedge node
- [ ] Parameter ranges match lookdev bible tables
- [ ] Total variations = 100 (5 x 4 x 5 standard wedge)
- [ ] Render tier is final (512 spp + OIDN, 4K resolution)
- [ ] Single representative frame selected (not a sequence)
- [ ] Contact sheet generated as 10x10 mosaic
- [ ] Parameter log (CSV/JSON) maps each variation to its parameter values
- [ ] Obvious failures eliminated from contact sheet
- [ ] Top 10 candidates rendered at full resolution
- [ ] Top 5 printed on Hahnemuhle Photo Rag Baryta 315 gsm at 13x19"
- [ ] Paper evaluation done under D50 illuminant at 50 cm
- [ ] Winning parameter set locked within 3-day time box
- [ ] Locked parameters committed to shot configuration
- [ ] No further lookdev iteration during animation rendering
