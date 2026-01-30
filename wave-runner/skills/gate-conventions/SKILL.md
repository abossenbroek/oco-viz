---
name: gate-conventions
user-invocable: false
---

# Gate Conventions

Standard conventions for running and fixing quality gates in oco-viz Python projects.

## Gate Tools

Four gates run in parallel:

1. **ruff** — linting and formatting (`pixi run ruff check --output-format json src/ tests/`)
2. **mypy** — static type checking (`pixi run mypy src/`)
3. **pyright** — type checking (`pixi run pyright src/`)
4. **pytest** — test suite (`pixi run pytest -x`)

---

## Failure Classification

Every gate failure falls into one of three categories:

### AUTO-FIX

Failures that can be fixed programmatically without human judgment.

**Ruff auto-fixable rules:**

| Rule | Description | Fix |
|------|-------------|-----|
| PLC0415 | `import` not at top of file | Move import to top |
| F401 | Unused import | Remove the import |
| I001 | Import block unsorted | Run `ruff check --fix --select I001` |
| SIM108 | Use ternary operator | Rewrite as ternary |
| F541 | f-string without placeholders | Remove `f` prefix |
| RUF100 | Unused `noqa` directive | Remove the `noqa` comment |
| PERF401 | Use list comprehension | Rewrite as comprehension |
| ARG001 | Unused function argument | Prefix with `_` |

**Mypy auto-fixable patterns:**

| Pattern | Fix |
|---------|-----|
| Unused `type: ignore` comment | Remove the comment |
| `no-any-return` on typed function | Add explicit return type annotation |

**Pyright auto-fixable patterns:**

| Pattern | Fix |
|---------|-----|
| Already-suppressed rule still reported | Update or remove `# type: ignore` |

### CONFIG-FIX

Failures requiring a configuration change (pyproject.toml, pixi.toml, ruff.toml).

Examples:
- Adding a module to mypy `[[tool.mypy.overrides]]` for untyped deps
- Adding a ruff rule to `extend-ignore`
- Adding a pyright `reportMissingTypeStubs` override

### MANUAL

Failures requiring human architectural judgment.

Examples:
- Test logic errors
- Incorrect type annotations on public API
- Missing protocol implementations
- Architectural design flaws

---

## Import Strategy Decision Tree

```
Is the dependency typed (has py.typed or stubs)?
├── YES → import normally at top of file
└── NO → Is it used at runtime?
    ├── YES → import at top, add mypy override:
    │         [[tool.mypy.overrides]]
    │         module = "dep_name.*"
    │         ignore_missing_imports = true
    └── NO (type annotations only) → use TYPE_CHECKING:
              from __future__ import annotations
              from typing import TYPE_CHECKING
              if TYPE_CHECKING:
                  import dep_name
```

### Known Untyped Dependencies

These deps lack `py.typed` and require mypy overrides:

- `vtk`
- `openvdb`
- `cdsapi`
- `scipy`
- `xarray`
- `zarr`

---

## Standard Module Header Template

Every Python source file under `src/` must begin with:

```python
"""Module docstring."""

from __future__ import annotations
```

Followed by stdlib imports, then third-party imports, then local imports — each block separated by a blank line.

---

## Auto-Fix Loop Protocol

1. Run all 4 gates in parallel
2. Collect failures, classify each as AUTO-FIX / CONFIG-FIX / MANUAL
3. Apply all AUTO-FIX changes
4. Re-run only the gates that had AUTO-FIX failures
5. Repeat up to 4 cycles
6. Report remaining CONFIG-FIX and MANUAL issues
