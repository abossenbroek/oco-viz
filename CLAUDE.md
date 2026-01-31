# CLAUDE.md — oco-viz

## 1. Structure Requirements

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
wave-runner/    # Claude Code plugin for wave orchestration
```

### File Organization

- **1:1 mapping:** Each class, protocol, or major function gets its own file. Aim for crisp, small files (<200 lines).
- **Specific names:** Always use domain-specific file names — `depth_compositor.py`, `gaussian_plume.py`, `camera_orbit.py`. Generic names (`utils.py`, `helpers.py`, `misc.py`, `common.py`) are prohibited.
- **Structured directories:** Group related files in sub-packages. Prefer a directory with 5 focused files over one 500-line file.

**Config layering:** `configs/base.yaml` is always loaded, overlaid with `configs/dev_mac.yaml` or `configs/dev_linux.yaml` depending on platform.

**Docker:** `docker-compose.yml` at project root for containerized runs.

## 2. Deployment-First

**Package manager: pixi** — the sole package manager (replaces pip/conda).

### Key Entry Points

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `pixi run check` | Parallel lint + typecheck + test | Continuous development loop |
| `pixi run ci` | Full CI mirror (all gates + extra checks) | Before pushing |
| `pixi run fix` | Auto-fix formatting + imports + lint | Repair auto-fixable failures |

### Individual Tasks

**Quality gates:**
```bash
pixi run lint        # ruff check src/ tests/
pixi run typecheck   # mypy src/ && pyright src/
pixi run test        # pytest tests/ -x
pixi run mypy        # mypy src/ only
pixi run pyright     # pyright src/ only
```

**CI checks (run individually or via `pixi run ci`):**
```bash
pixi run format-check       # ruff format --check
pixi run import-sort        # ruff check --select I
pixi run spell              # typos
pixi run dead-code          # vulture --min-confidence 80
pixi run complexity         # radon cc --min D (fail on CC>15)
pixi run yaml-lint          # yamllint configs/ plan/ .github/
pixi run dockerfile-lint    # hadolint Dockerfile
pixi run file-size          # reject files >1MB
pixi run future-annotations # verify __future__ imports in src/
pixi run py-typed           # verify py.typed marker
```

### Workflow

1. Develop with `pixi run check` in the loop (fast feedback)
2. Before committing: `pixi run fix` to auto-repair, then `pixi run ci` for full validation
3. Push only when `pixi run ci` passes cleanly

## 3. Core Principles

### Prebuilt Components

- **Delegate to libraries.** VTK for rendering, xarray/zarr for data, scipy for numerics. Always use their built-in capabilities for their domain.
- **Untyped deps** (vtk, openvdb, cdsapi, scipy, xarray, zarr): always import at top of file. Handle type errors via mypy `[[tool.mypy.overrides]]` in `pyproject.toml`. Runtime-used imports must stay at module level (only put imports inside `TYPE_CHECKING` when they are exclusively used in annotations).

### Data Model Preferences

- **Standard data interchange:** `xr.Dataset` is the canonical data format between modules.
- **Array operations:** Prefer xarray's labeled dimensions and vectorized ops over manual loops.
- **Persistence:** Use zarr for chunked array storage, NetCDF for final outputs.

### Message & State Management

- **Config schemas:** Pydantic v2 + attrs. Config definitions live in `src/oco_viz/config/`.
- **YAML layering:** Base config (`configs/base.yaml`) overlaid with platform-specific overrides (`dev_mac.yaml`, `dev_linux.yaml`).
- **Immutability:** Config objects are frozen after construction. Runtime state lives in separate data structures.
- **Ticket-driven development:** Implementation specs are YAML files in `plan/tickets/`. Status flow: `todo` -> `in_progress` -> `done` -> `blocked`.

## 4. Tool Usage

### Quality Gate Commands

Four gates run **in parallel** via `pixi run check`:

| Gate | Command | Mode |
|------|---------|------|
| ruff | `pixi run ruff check src/ tests/` | `select = ["ALL"]` with documented ignores |
| mypy | `pixi run mypy src/` | strict |
| pyright | `pixi run pyright src/` | strict |
| pytest | `pixi run pytest tests/ -x` | fail-fast |

Full CI validation (13 checks) via `pixi run ci`.

### Auto-Fix Workflows

1. **Immediate repair:** `pixi run fix` applies formatting and auto-fixable lint rules
2. **Verify:** Re-run `pixi run check` or `pixi run ci` to confirm
3. **Manual fixes:** Address remaining failures per classification below

### Failure Classification

See `.claude/plugins/wave-runner/skills/gate-conventions/SKILL.md` for full tables.

| Category | Action | Example |
|----------|--------|---------|
| AUTO-FIX | Apply via `pixi run fix` | Unused import, unsorted imports, unused `noqa` |
| CONFIG-FIX | Change `pyproject.toml` or `pixi.toml` | Add mypy override for untyped dep |
| MANUAL | Requires human judgment | Incorrect type annotation, missing protocol impl |

### Wave-Runner Plugin

| Command | Purpose |
|---------|---------|
| `/wave-runner:gate` | Run quality gates with auto-fix loop |
| `/wave-runner:ticket <id>` | Execute a single ticket |
| `/wave-runner:wave <n>` | Orchestrate a full wave of tickets |
| `/wave-runner:wave-status` | Show progress across all waves |

**Ticket-driven workflow:** Each ticket declares `produces`, `depends`, `gates`, and `context.related_files`. Scope reads to files listed in `related_files` only.

## 5. Best Practices

- Every `.py` file under `src/` starts with `from __future__ import annotations`.
- **Selective context:** Scope reads to files listed in a ticket's `related_files` only.
- **Ticket-driven:** Implement features via YAML specs in `plan/tickets/`.
- **Parallel validation:** Always run gates concurrently via `pixi run check`.
- **Config over code:** If a fix belongs in `pyproject.toml` or `pixi.toml`, it's a CONFIG-FIX, not a code change.

## 6. Coding Standards

- **Python:** >=3.11, line-length 99
- **Linting:** ruff with `select = ["ALL"]`, ignores documented in `pyproject.toml` `[tool.ruff.lint]`
- **Type checking:** mypy strict + pyright strict (both configured in `pyproject.toml`). All new code must pass both with zero errors. Use the narrowest types possible — prefer `Sequence[float]` over `list[Any]`, `Path` over `str` for file paths, `Mapping` over `dict` for read-only access.
- **Always annotate concrete types.** When a third-party lib returns `Any`, annotate the binding with the actual type. Use `cast()` only when the type is provably correct.
- **Always catch specific exceptions.** Use the narrowest exception type (`KeyError`, `ValueError`, `FileNotFoundError`, etc.). For multiple types use a tuple: `except (KeyError, IndexError):`.
- **Tests:** pytest, function style. Fixtures live in test files unless shared across 3+ files.
- **Import order:** stdlib, then third-party, then local — each separated by a blank line. ruff enforces this via `I001`.

Standard module header:

```python
"""Module docstring."""

from __future__ import annotations
```

## 7. Common Pitfalls

| Instead of... | Do this | Why |
|---------------|---------|-----|
| Adding a script to `scripts/` alone | Also add a `pixi run` task for it | Ensures the script is covered by `pixi run ci` linting and type checks |
| Naming a file `utils.py` or `helpers.py` | Use a domain-specific name (`coordinate_transform.py`, `zarr_encoding.py`) | Keeps files focused; generic names attract unrelated code |
| Putting multiple classes in one file | Give each class its own file in a sub-package | Maintains 1:1 file mapping, improves navigability |
| Annotating with `Any` to satisfy the type checker | Annotate the concrete type, use `cast()` when provably correct | Preserves type safety for all callers |
| Placing a runtime import inside `TYPE_CHECKING` | Keep it at module top level; suppress via mypy `[[tool.mypy.overrides]]` | Avoids `NameError` at runtime |
| Running `pixi run check` before pushing | Run `pixi run ci` (the full CI mirror) | `check` is the fast subset; `ci` catches spelling, dead code, complexity, etc. |
| Changing code to fix a config issue | Edit `pyproject.toml` or `pixi.toml` instead (CONFIG-FIX) | Keeps config concerns in config files |
| Using `dict` for a read-only parameter | Use `Mapping` | Signals immutability to callers; reserve `dict` for mutation |
| Returning `list[Any]` or `dict[str, object]` | Return the narrowest concrete type | Callers retain full type safety |
