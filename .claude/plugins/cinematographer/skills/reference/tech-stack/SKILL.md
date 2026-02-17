---
name: tech-stack
user-invocable: false
type: reference
primary_owner: shared
---

# Tech Stack

Per-agent technology preferences and constraints for the cinematographer
plugin. Defines the tools, formats, and validation methods each agent uses
to produce its artifacts.

---

## Principle

Each agent operates within a bounded technology stack. Agents write only
the formats listed for their role and validate using only the tools
specified. This prevents technology sprawl and ensures every artifact
can be validated by its producing agent.

---

## Agent Technology Matrix

| Agent | Primary Language | Formats Written | Libraries / Tools | Validation Method |
|-------|-----------------|-----------------|-------------------|-------------------|
| **dp** | Python / Hython | .py, .json, .yaml | VTK, Houdini, OpenVDB, NumPy | `pixi run check` |
| **production-designer** | YAML + USD | .yaml, .usda, .json | pxr.Usd, MaterialX, OpenVDB | `Stage.Open()` + schema check |
| **colorist** | YAML + OCIO | .ocio, .yaml, .json | PyOpenColorIO, ACES, NumPy | `Config.CreateFromFile()` |
| **storyboarder** | YAML (read-only code) | .yaml only | N/A (pure YAML authoring) | YAML schema validation |
| **groundtruth** | Python | .py (validation scripts) | VTK, OpenVDB, pxr.Usd, MaterialX, SciPy | `pixi run check` |

---

## Format Specifications

### YAML artifacts (.yaml)

- UTF-8 encoding, no BOM
- 2-space indentation
- Flow scalars for single-line values, block scalars for multi-line
- All files must parse with `yaml.safe_load()`
- Schema validation against output-schemas before delivery

### USD artifacts (.usda)

- ASCII USD format for human readability during development
- Binary `.usdc` for production delivery (final tier only)
- All stages composed via `Usd.Stage.Open()`
- Layer structure follows USD composition arc conventions

### OCIO artifacts (.ocio)

- OCIO v2 config format
- Must validate with `PyOpenColorIO.Config.CreateFromFile()`
- ACES 1.3+ compatible color spaces
- ACEScg as working color space

### Python artifacts (.py)

- Follows project coding standards (CLAUDE.md section 7)
- `from __future__ import annotations` at top of every file
- Type hints on all public functions
- Validated by `pixi run check` (ruff + mypy + pyright + pytest)

### JSON artifacts (.json)

- UTF-8 encoding
- 2-space indentation for readability
- Must parse with `json.loads()` without errors
- Used for machine-readable configs and intermediate data

---

## Template-Based Generation Rule

All agents MUST use template-based generation for artifacts:

1. **Template**: A structured format with placeholder fields
2. **Population**: Fill placeholders from upstream collaboration YAML data and agent-specific logic
3. **Validation**: Verify populated template against format specification

**Rationale**: Template-based generation ensures reproducibility. Given
identical inputs, the same artifact must result. This makes debugging
tractable and version control meaningful.

**Prohibited**: Free-form text generation for any artifact field except
`audit_trail`, `creative_brief`, and `narrative_intent` (which are
inherently descriptive).

---

## Dependency Matrix

Which agents depend on which tools at runtime:

| Tool | dp | production-designer | colorist | storyboarder | groundtruth |
|------|----|--------------------|----------|-------------|-------------|
| VTK | primary | - | - | - | validation |
| OpenVDB | primary | read | - | - | validation |
| Houdini/Hython | primary | - | - | - | - |
| pxr.Usd | - | primary | - | - | validation |
| MaterialX | - | primary | - | - | validation |
| PyOpenColorIO | - | - | primary | - | validation |
| NumPy | primary | - | primary | - | primary |
| SciPy | - | - | - | - | primary |
| YAML parser | all | all | all | primary | all |

---

## Anti-Patterns

- **Format sprawl**: An agent writing formats not listed in its row. The storyboarder writes YAML only; it does not produce Python scripts.
- **Tool sharing without declaration**: Using a library not listed in the dependency matrix. If a tool is needed, declare it here first.
- **Free-form generation**: Producing artifacts by generating unstructured text instead of populating templates. Templates ensure reproducibility.
- **Binary-first development**: Writing binary formats (`.usdc`, `.vdb`) during development. Use ASCII/text formats until final tier.
- **Validation bypass**: Skipping the validation method listed for this agent. Every artifact must pass its format-specific validation.

---

## Validation Checklist

- [ ] Agent is writing only formats listed in its technology matrix row
- [ ] All artifacts pass format-specific validation (yaml.safe_load, Stage.Open, etc.)
- [ ] Python artifacts pass `pixi run check`
- [ ] Template-based generation used (not free-form)
- [ ] Dependencies are declared in the matrix
- [ ] Encoding is UTF-8 for all text formats
