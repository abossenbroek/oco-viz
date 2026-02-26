# CLAUDE.md — oco-viz

## 1. Project Overview & Structure

**oco-viz** is a 3D volumetric CO2 plume visualization tool for OCO-3 satellite data.

```
src/oco_viz/
  config/       # Pydantic v2 + attrs config schemas
  data/         # Data loading and xarray/zarr pipelines
  plume/        # Plume generation (Gaussian, protocol)
  postprocess/  # Post-processing steps
  render/       # VTK-based 3D rendering
  sequencer/    # Animation sequencing
configs/        # YAML config files (base + platform overrides)
scripts/        # Standalone scripts (render_synthetic, tune_transfer, validate_backend)
tests/          # pytest test suite
plan/tickets/   # YAML ticket specs for wave-based development
.claude/plugins/wave-runner/  # Claude Code plugin for wave orchestration
```

## 2. Build & Run

**Package manager: pixi** (not pip or conda directly).

```bash
pixi run lint        # ruff check src/ tests/
pixi run typecheck   # mypy src/ && pyright src/
pixi run test        # pytest tests/ -x
pixi run check       # all three above (lint, typecheck, test)
```

**Config layering:** `configs/base.yaml` is always loaded, overlaid with `configs/dev_mac.yaml` or `configs/dev_linux.yaml` depending on platform.

**Docker:** `docker-compose.yml` at project root for containerized runs.

## 3. Core Principles

- **Use prebuilt components.** VTK for rendering, xarray/zarr for data, scipy for numerics. Do not reimplement what these libraries provide.
- **Standard data interchange:** `xr.Dataset` is the canonical data format between modules.
- **Config schemas:** Pydantic v2 + attrs. Config definitions live in `src/oco_viz/config/`.
- **Ticket-driven development:** Implementation specs are YAML files in `plan/tickets/`. Status flow: `todo` -> `in_progress` -> `done` -> `blocked`.

## 4. Quality Gates

Four gates run **in parallel** via `pixi run check`:

| Gate | Command | Mode |
|------|---------|------|
| ruff | `pixi run ruff check src/ tests/` | `select = ["ALL"]` with documented ignores |
| mypy | `pixi run mypy src/` | strict |
| pyright | `pixi run pyright src/` | strict |
| pytest | `pixi run pytest tests/ -x` | fail-fast |

**Failure classification** (see `.claude/plugins/wave-runner/skills/gate-conventions/SKILL.md` for full tables):

| Category | Action | Example |
|----------|--------|---------|
| AUTO-FIX | Apply programmatically | Unused import, unsorted imports, unused `noqa` |
| CONFIG-FIX | Change `pyproject.toml` | Add mypy override for untyped dep |
| MANUAL | Requires human judgment | Incorrect type annotation, missing protocol impl |

**Wave-runner plugin commands:**

| Command | Purpose |
|---------|---------|
| `/wave-runner:gate` | Run quality gates with auto-fix loop |
| `/wave-runner:ticket <id>` | Execute a single ticket |
| `/wave-runner:wave <n>` | Orchestrate a full wave of tickets |
| `/wave-runner:wave-status` | Show progress across all waves |

### 4.1 Pre-PR Checklist

Before raising or pushing to a PR, **always** run these two commands locally and confirm they pass:

```bash
pixi run spell       # typos spellcheck (must match CI version >= 1.43)
pixi run ci          # full CI suite: format, lint, typecheck, test, spell, dead-code, complexity, etc.
```

If either fails, fix the issue before pushing. This prevents CI failures on GitHub that could have been caught locally.

### 4.2 Commit Message & PR Title Convention

This repo enforces **Conventional Commits** via `commitlint` (config: `.commitlintrc.yml`). Both commit messages and PR titles must follow the format:

```
<type>: <lowercase subject>
```

**Rules:**
- **Subject must be lowercase** — `feat: add new skill` not `feat: Add new skill`
- **No sentence-case, start-case, pascal-case, or upper-case** in the subject
- **Allowed types:** `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `plan`, `refactor`, `revert`, `style`, `test`
- **PR titles** follow the same convention — GitHub Actions checks both

**Local check:** `pixi run commit-lint` validates the latest commit message (also included in `pixi run ci`).

## 5. Visual Quality Gate

The `output/examples/` directory contains gallery PNGs (tracked via Git LFS) that serve as **visual regression baselines**. These are the ground truth for rendering quality.

**Any change that could affect rendered output** — transfer functions, scattering/lighting configs, post-processing, camera, normalization, volume construction, tier definitions — **must include a gallery re-render and visual inspection before the PR is raised.**

### 5.1 Gallery Scripts as Living Coverage

The unified gallery runner (`pixi run gallery`, backed by `scripts/render_gallery_all.py`) is the single entry point for rendering all gallery images. Individual wave scripts still live in `scripts/render_*_gallery.py` but are invoked through the unified runner. Together they must exercise every stage of the rendering pipeline — normalization, transfer functions, volume construction, lighting, camera paths, easing, composition, post-processing, and tier configs. **When a new rendering capability is added, the gallery scripts must be extended to generate images that cover it.** The gallery is not a static snapshot; it grows with the pipeline so that `output/examples/` always provides end-to-end visual proof that the full pipeline works. For selective rendering use `pixi run gallery -- --wave 3 --tier study`.

### 5.2 Re-render and Inspect

1. Run `pixi run gallery` to regenerate the full image set (all waves at native tiers). For automated verification: `pixi run gallery-verify`.
2. If any image regresses — darker, flatter, clipped, banded, loses structure, or simply looks worse — the PR is not ready. Fix the root cause, re-render, re-inspect.

### 5.3 Critical Eye Review via Opus Agent

The visual inspection must be performed by a **dedicated Opus agent** (via the Task tool) that reviews the generated images out of context — without access to the code changes, config diffs, or rationale. The agent receives only the images and judges them on their own merit as a supercritical Pixar/Disney lighting TD would review a final shot. This ensures the review is unbiased by implementation knowledge.

The agent should evaluate each image against these criteria:
- Does the plume have visible edges and a wispy halo, or does it clip to a hard blob?
- Is there directional depth from lighting, or is the volume flat and lifeless?
- Is cross-tier coherence maintained — same plume structure, different cinematic mood?
- Are bloom, fog, exposure, and tonemapping contributing to the intended look?
- Do camera paths and easing produce smooth, intentional motion across keyframes?
- Would this frame hold up projected on a gallery wall at 4K?

The agent must return a pass/fail verdict per image with specific critique. A single fail blocks the PR.

### 5.4 Gallery Images as PR Evidence

The gallery images are committed to the repo so reviewers can compare before/after visually in the PR diff. **Treat output/examples/ as the definitive proof that the rendering pipeline produces exhibition-quality results.**

### 5.5 Gallery CLI Reference

| Command | Purpose |
|---------|---------|
| `pixi run gallery` | Render all waves at native tiers |
| `pixi run gallery-verify` | Render + automated image_stats verification |
| `pixi run gallery -- --wave 3,4 --tier exhibition` | Selective wave/tier cross-product |
| `pixi run gallery -- --dry-run` | List all ~115 images without rendering |
| `pixi run gallery -- --verify-output report.yaml` | Custom verification output path |

## 6. Best Practices

- Every `.py` file under `src/` starts with `from __future__ import annotations`.
- **Untyped deps** (vtk, openvdb, cdsapi, scipy, xarray, zarr): import at top of file, handle via mypy `[[tool.mypy.overrides]]` in `pyproject.toml`. Do NOT put runtime-used imports inside `TYPE_CHECKING`.
- **Selective context:** Read only files listed in a ticket's `related_files`. Do not scan the entire codebase for context.
- **Ticket-driven:** Implement features via YAML specs in `plan/tickets/`. Each ticket declares `produces`, `depends`, `gates`, and `context.related_files`.

## 7. Coding Standards

- **Python:** >=3.11, line-length 99
- **Linting:** ruff with `select = ["ALL"]`, ignores documented in `pyproject.toml` `[tool.ruff.lint]`
- **Type checking:** mypy strict + pyright strict (both configured in `pyproject.toml`)
- **Tests:** pytest, function style. Fixtures live in test files unless shared across 3+ files.
- **Import order:** stdlib, then third-party, then local — each separated by a blank line. ruff enforces this via `I001`.

Standard module header:

```python
"""Module docstring."""

from __future__ import annotations
```

## 8. Common Pitfalls

| Pitfall | Why it matters |
|---------|---------------|
| Importing untyped dep inside `TYPE_CHECKING` when used at runtime | Causes `NameError` at runtime |
| Omitting `from __future__ import annotations` | Breaks deferred annotation evaluation, mypy/pyright errors |
| Running gates sequentially | `pixi run check` runs them in parallel — do the same manually |
| Reading entire codebase for context | Use the ticket's `context.related_files` instead |
| Fixing a config problem by changing code | If the fix belongs in `pyproject.toml` or `pixi.toml`, it's a CONFIG-FIX |

## 8. Cinematic Pipeline Context

This project generates VTK volumetric data for downstream cinematic rendering. See `plan/coding_guide_2026.md` for the full 2026 production pipeline.

### Pipeline Stages

| Stage | Renderer | Quality Level | Status |
|-------|----------|---------------|--------|
| **Stage 0: VTK Pre-Viz** | VTK (Python) | Study/pre-visualization | **Active** (Waves 1-9) |
| **Stage 1+: Production** | Karma XPU (Houdini) | Exhibition/gallery-quality | Planned (Waves 12-13) |

The current oco-viz pipeline produces **pre-visualization quality** imagery via VTK. This is suitable for creative direction approval, timing validation, and composition exploration. Exhibition-grade output requires the downstream Karma XPU pipeline, which is not yet implemented.

### Pipeline Overview

```
Stage 0: VTK Generation (oco-viz) → OpenVDB Export → Pre-viz review
Stage 1+: OpenVDB → Houdini Processing → Karma XPU → Nuke Compositing → Exhibition
```

### Critical VTK Design Decisions

| Parameter | Correct Specification | Impact of Error |
|-----------|----------------------|-----------------|
| Length Units | Meters (real-world scale) | Wrong volume size, broken physics |
| Temperature | Kelvin (293-3000K) | Completely wrong fire colors |
| Voxel Spacing | world_size ÷ resolution | Scale mismatch in Houdini |
| Grid Names | "density", "vel", "temperature" | Manual renaming, pipeline breaks |
| Sparse Design | Exact 0.0 where empty | 10× file sizes, slow I/O |

### Quality Philosophy

> "Fix it in pre, not post" — Validate at VTK generation, not at final render.

**Progressive Validation:**
1. **Scout (128³)** — Motion timing, creative direction approval
2. **Preview (512³)** — Lighting, materials, technical settings
3. **Final (1024³)** — Maximum detail, no creative surprises

### Key Quality Principles
- Physical accuracy from VTK origin (meters, Kelvin, m/s)
- Non-linear shader response (exponential curves, not linear)
- Subtle imperfection (grain, variation, turbulence 2.5-4.0)
