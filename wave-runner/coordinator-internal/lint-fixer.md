# Lint Fixer Reference

Comprehensive before/after catalog for every auto-fixable error in the project's gate tools. Used as a lookup by gate-runner when applying fixes.

---

## Ruff Auto-Fixable Rules

### PLC0415 — `import` not at top of file

**Before:**
```python
def process():
    import numpy as np
    return np.array([1, 2, 3])
```

**After:**
```python
import numpy as np

def process():
    return np.array([1, 2, 3])
```

**Fix**: Move import to the top of the file, after `from __future__` and docstring.

---

### F401 — Unused import

**Before:**
```python
import os
import sys

def main():
    print(sys.argv)
```

**After:**
```python
import sys

def main():
    print(sys.argv)
```

**Fix**: Remove the unused import line entirely.

---

### I001 — Import block unsorted

**Before:**
```python
import sys
import os
from pathlib import Path
import json
```

**After:**
```python
import json
import os
import sys
from pathlib import Path
```

**Fix**: Run `ruff check --fix --select I001` or sort manually: stdlib alphabetical, then third-party, then local.

---

### SIM108 — Use ternary operator

**Before:**
```python
if condition:
    value = "yes"
else:
    value = "no"
```

**After:**
```python
value = "yes" if condition else "no"
```

**Fix**: Rewrite as ternary. Only apply when both branches are simple assignments.

---

### F541 — f-string without placeholders

**Before:**
```python
msg = f"Hello world"
```

**After:**
```python
msg = "Hello world"
```

**Fix**: Remove the `f` prefix.

---

### RUF100 — Unused `noqa` directive

**Before:**
```python
x = 1  # noqa: F841
# But F841 is not actually triggered
```

**After:**
```python
x = 1
```

**Fix**: Remove the `# noqa` comment.

---

### PERF401 — Use list comprehension

**Before:**
```python
result = []
for item in items:
    result.append(item.name)
```

**After:**
```python
result = [item.name for item in items]
```

**Fix**: Rewrite as list comprehension. Only apply when the loop body is a single append.

---

### ARG001 — Unused function argument

**Before:**
```python
def callback(event, context):
    return event.data
```

**After:**
```python
def callback(event, _context):
    return event.data
```

**Fix**: Prefix the unused argument with `_`.

---

## Mypy Auto-Fixable Patterns

### Unused `type: ignore` comment

**Before:**
```python
x: int = 42  # type: ignore[assignment]
```

**After:**
```python
x: int = 42
```

**Fix**: Remove the `# type: ignore` comment when mypy reports it as unused.

---

### `no-any-return` on typed function

**Before:**
```python
def get_value() -> str:
    return some_untyped_func()
```

**After:**
```python
def get_value() -> str:
    result: str = some_untyped_func()
    return result
```

**Fix**: Add intermediate variable with explicit type annotation, or cast the return.

---

## Pyright Auto-Fixable Patterns

### Already-suppressed rule still reported

**Before:**
```python
x = untyped_call()  # type: ignore[no-any-return]
# But pyright reports a different error code
```

**After:**
```python
x = untyped_call()  # type: ignore[no-any-return, reportUnknownMemberType]
```

**Fix**: Add the pyright error code to the existing `type: ignore` comment.

---

## Config-Fix Patterns (not auto-fixable in code)

### Untyped dependency mypy override

Add to `pyproject.toml`:
```toml
[[tool.mypy.overrides]]
module = "vtk.*"
ignore_missing_imports = true
```

### Ruff rule suppression

Add to `pyproject.toml`:
```toml
[tool.ruff.lint]
extend-ignore = ["RULE_CODE"]
```

### Pyright missing type stubs

Add to `pyproject.toml`:
```toml
[tool.pyright]
reportMissingTypeStubs = false
```
