# Import Organizer Reference

Decision tree with concrete examples for handling imports, especially untyped dependencies. Used by ticket-executor and gate-runner when organizing imports.

---

## Import Decision Tree

```
Is the dependency typed (has py.typed marker or type stubs)?
│
├── YES → Standard import at top of file
│         Example: import numpy as np
│
└── NO → Is it used at runtime (not just for type annotations)?
    │
    ├── YES → Import at top + add mypy override
    │         Example: import vtk
    │         Config:  [[tool.mypy.overrides]]
    │                  module = "vtk.*"
    │                  ignore_missing_imports = true
    │
    └── NO (annotations only) → Use TYPE_CHECKING guard
              Example:
              from __future__ import annotations
              from typing import TYPE_CHECKING
              if TYPE_CHECKING:
                  import vtk
```

---

## Untyped Dependency Catalog

### vtk

**Usage**: Runtime (3D rendering, data processing)
**Strategy**: Top-level import + mypy override

```python
import vtk
```

```toml
[[tool.mypy.overrides]]
module = "vtk.*"
ignore_missing_imports = true
```

---

### openvdb

**Usage**: Runtime (volumetric data)
**Strategy**: Top-level import + mypy override

```python
import openvdb
```

```toml
[[tool.mypy.overrides]]
module = "openvdb.*"
ignore_missing_imports = true
```

---

### cdsapi

**Usage**: Runtime (climate data store API)
**Strategy**: Top-level import + mypy override

```python
import cdsapi
```

```toml
[[tool.mypy.overrides]]
module = "cdsapi.*"
ignore_missing_imports = true
```

---

### scipy

**Usage**: Runtime (scientific computing)
**Strategy**: Top-level import + mypy override

```python
import scipy
from scipy import ndimage
```

```toml
[[tool.mypy.overrides]]
module = "scipy.*"
ignore_missing_imports = true
```

---

### xarray

**Usage**: Runtime (labeled arrays, datasets)
**Strategy**: Top-level import + mypy override

```python
import xarray as xr
```

```toml
[[tool.mypy.overrides]]
module = "xarray.*"
ignore_missing_imports = true
```

---

### zarr

**Usage**: Runtime (chunked array storage)
**Strategy**: Top-level import + mypy override

```python
import zarr
```

```toml
[[tool.mypy.overrides]]
module = "zarr.*"
ignore_missing_imports = true
```

---

## Standard Import Order

Every Python file follows this import order, with blank lines between sections:

```python
"""Module docstring."""

from __future__ import annotations

# 1. Standard library
import os
import sys
from pathlib import Path

# 2. TYPE_CHECKING imports (if needed)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from some_untyped_lib import SomeType

# 3. Third-party
import numpy as np
import xarray as xr

# 4. Local
from oco_viz.config.schema import Config
```

---

## Handling importlib (Lazy Imports)

Use `importlib` only when a dependency is:
1. Very heavy to import (>1s import time)
2. Used conditionally (not every code path needs it)

```python
def render_vtk():
    import vtk  # noqa: PLC0415 — lazy import for optional heavy dep
    renderer = vtk.vtkRenderer()
```

For this pattern, add `PLC0415` to ruff's `per-file-ignores` for the specific file:

```toml
[tool.ruff.lint.per-file-ignores]
"src/oco_viz/render/vtk_backend.py" = ["PLC0415"]
```

---

## Common Mistakes

1. **Don't** put runtime deps in TYPE_CHECKING — causes `NameError` at runtime
2. **Don't** use `importlib.import_module` for deps that are always needed
3. **Don't** add mypy overrides for typed dependencies (numpy, pandas have stubs)
4. **Do** use `from __future__ import annotations` in every file — enables string-based annotation evaluation
