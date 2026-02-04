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

## 5. Best Practices

- Every `.py` file under `src/` starts with `from __future__ import annotations`.
- **Untyped deps** (vtk, openvdb, cdsapi, scipy, xarray, zarr): import at top of file, handle via mypy `[[tool.mypy.overrides]]` in `pyproject.toml`. Do NOT put runtime-used imports inside `TYPE_CHECKING`.
- **Selective context:** Read only files listed in a ticket's `related_files`. Do not scan the entire codebase for context.
- **Ticket-driven:** Implement features via YAML specs in `plan/tickets/`. Each ticket declares `produces`, `depends`, `gates`, and `context.related_files`.

## 6. Coding Standards

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

## 7. Common Pitfalls

| Pitfall | Why it matters |
|---------|---------------|
| Importing untyped dep inside `TYPE_CHECKING` when used at runtime | Causes `NameError` at runtime |
| Omitting `from __future__ import annotations` | Breaks deferred annotation evaluation, mypy/pyright errors |
| Running gates sequentially | `pixi run check` runs them in parallel — do the same manually |
| Reading entire codebase for context | Use the ticket's `context.related_files` instead |
| Fixing a config problem by changing code | If the fix belongs in `pyproject.toml` or `pixi.toml`, it's a CONFIG-FIX |

## 8. Cinematic Pipeline Context

This project generates VTK volumetric data for downstream cinematic rendering. See `plan/coding_guide_2026.md` for the full 2026 production pipeline.

### Pipeline Overview

```
VTK Generation (oco-viz) → OpenVDB Conversion → Houdini Processing → GPU Rendering
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
