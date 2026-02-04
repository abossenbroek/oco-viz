# Test Scaffolder Reference

Test boilerplate templates and patterns for oco-viz. Used by ticket-executor when creating test files.

---

## Test File Template

```python
"""Tests for {module_name}."""

from __future__ import annotations

import numpy as np
import pytest

from oco_viz.{module_path} import {classes_or_functions}


class TestClassName:
    """Tests for ClassName."""

    def test_basic_usage(self):
        """Verify basic functionality."""
        ...

    def test_edge_case(self):
        """Verify edge case handling."""
        ...
```

**Preferred style**: Use pytest function style when testing standalone functions. Use classes when grouping related tests for a single class.

---

## Standard Fixtures

### tmp_path (built-in)

For tests that create temporary files:

```python
def test_write_output(tmp_path):
    output_file = tmp_path / "output.nc"
    write_dataset(output_file)
    assert output_file.exists()
```

### Mock network calls

For tests that would hit external APIs:

```python
from unittest.mock import patch, MagicMock

def test_fetch_data():
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [1, 2, 3]}
    with patch("oco_viz.data.fetch.requests.get", return_value=mock_response):
        result = fetch_data("endpoint")
        assert result == [1, 2, 3]
```

### xarray Dataset fixture

For tests that need sample datasets:

```python
@pytest.fixture
def sample_dataset():
    return xr.Dataset(
        {
            "concentration": (["x", "y"], np.random.default_rng(42).random((10, 10), dtype=np.float32)),
        },
        coords={
            "x": np.arange(10, dtype=np.float32),
            "y": np.arange(10, dtype=np.float32),
        },
    )
```

### Config fixture

For tests that need a config object:

```python
@pytest.fixture
def config():
    return Config(
        grid_resolution=0.1,
        domain_size=(100, 100),
        time_steps=24,
    )
```

---

## Assertion Patterns

### Shape checks

```python
result = generate_plume(config)
assert result["concentration"].shape == (100, 100)
```

### dtype checks

```python
assert result["concentration"].dtype == np.float32
```

### Non-negative value checks

```python
assert (result["concentration"].values >= 0).all()
```

### Floating-point comparison (allclose)

```python
expected = np.array([1.0, 2.0, 3.0], dtype=np.float32)
np.testing.assert_allclose(result, expected, rtol=1e-5)
```

### xarray equality

```python
xr.testing.assert_equal(result, expected_dataset)
```

### xarray approximate equality

```python
xr.testing.assert_allclose(result, expected_dataset, atol=1e-6)
```

---

## Parametrize Patterns

### Testing multiple inputs

```python
@pytest.mark.parametrize(
    "wind_speed, expected_spread",
    [
        (1.0, 10.0),
        (5.0, 50.0),
        (10.0, 100.0),
    ],
)
def test_plume_spread(wind_speed, expected_spread):
    result = compute_spread(wind_speed)
    assert pytest.approx(result, rel=1e-2) == expected_spread
```

### Testing error conditions

```python
@pytest.mark.parametrize(
    "invalid_input, error_type",
    [
        (-1.0, ValueError),
        (None, TypeError),
        (float("nan"), ValueError),
    ],
)
def test_invalid_inputs(invalid_input, error_type):
    with pytest.raises(error_type):
        process(invalid_input)
```

---

## VTK / Volumetric Data Assertions

Tickets producing VTK output or VDB exports must validate physical correctness.
See `plan/coding_guide_2026.md` for full pipeline context.

### VTK ImageData fixture

```python
@pytest.fixture
def sample_vtk_dataset():
    return xr.Dataset(
        {
            "concentration": (["time", "z", "y", "x"], np.zeros((2, 16, 16, 16), dtype=np.float32)),
        },
        coords={
            "time": np.arange(2),
            "z": np.linspace(0, 1000, 16, dtype=np.float32),
            "y": np.linspace(0, 1000, 16, dtype=np.float32),
            "x": np.linspace(0, 1000, 16, dtype=np.float32),
        },
    )
```

### Grid spacing validation

```python
spacing = (grid_cfg.dx, grid_cfg.dy, grid_cfg.dz)
assert all(s > 0 for s in spacing), "Spacing must be positive meters"
expected = grid_cfg.world_size / grid_cfg.resolution
np.testing.assert_allclose(spacing[0], expected, rtol=1e-5)
```

### Grid name conventions

`"concentration"` is the primary variable for CO2 plume data. `"temperature"` and
`"vel"` are optional atmospheric context fields.

```python
assert "concentration" in ds.data_vars, "Dataset must contain 'concentration'"
OPTIONAL_GRID_NAMES = {"temperature", "vel"}
```

### Sparsity check (exact zero where empty)

```python
data = ds["concentration"].values
empty_mask = data == 0.0
assert empty_mask.sum() / data.size > 0.5, (
    "Volume should be mostly empty (>50% exact zeros for sparsity)"
)
```

### Temperature range (Kelvin, atmospheric CO2 plume context)

CO2 plumes exist at atmospheric temperatures (~150K upper stratosphere to ~330K
hot surface). Values outside this range indicate a unit error (e.g. Celsius) or
data corruption.

```python
if "temperature" in ds:
    temp = ds["temperature"].values
    assert temp[temp > 0].min() >= 150, "Temperature below 150K — check units or data source"
    assert temp.max() <= 350, "Temperature exceeds atmospheric range (>350K)"
```

### Value range bounds

```python
assert (ds["concentration"].values >= 0).all(), "Concentration must be non-negative"
assert ds["concentration"].values.max() <= 10.0, "Concentration exceeds expected range"
```

---

## Test Organization

- One test file per source module: `src/oco_viz/plume/gaussian.py` → `tests/test_plume_gaussian.py`
- Group related tests in classes when testing a single class
- Use standalone functions when testing module-level functions
- Name tests descriptively: `test_{what}_{condition}_{expected}`
- Keep fixtures in the test file unless shared across 3+ test files (then use `conftest.py`)
