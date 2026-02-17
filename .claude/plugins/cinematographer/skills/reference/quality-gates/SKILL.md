---
name: quality-gates
user-invocable: false
type: reference
primary_owner: shared
---

# Quality Gates

Five-gate validation specification for all cinematographer artifacts.
Every artifact must pass all applicable gates before delivery via
collaboration YAML. Gates are ordered by dependency: earlier gates
must pass before later gates are meaningful.

---

## Principle

Quality is verified at production time, not at review time. Each agent
validates its own output through these gates before producing the
collaboration YAML delivery. A gate failure produces a `status: blocked`
collaboration YAML; it does not silently propagate to downstream agents.

---

## Gate 1: Plugin Structure

Validates that the plugin itself is correctly configured and all
referenced files exist.

| Check | Tool | Pass Criteria |
|-------|------|---------------|
| plugin.json valid | `validate_plugin.py` | All required fields present, JSON parses |
| Skill files exist | `validate_plugin.py` | Every skill referenced in plugin.json has a SKILL.md |
| Agent files exist | `validate_plugin.py` | Every agent referenced in plugin.json has an AGENT.md |
| Command files exist | `validate_plugin.py` | Every command referenced in plugin.json has a .md file |
| No orphan files | `validate_plugin.py` | No SKILL.md/AGENT.md files exist that are not referenced |

**When to run**: Once per plugin modification, not per artifact.

---

## Gate 2: Artifact Format

Validates that an artifact conforms to its declared format specification
per the tech-stack skill.

| Format | Validation Tool | Pass Criteria |
|--------|----------------|---------------|
| `.yaml` | `yaml.safe_load()` | Parses without error, UTF-8 |
| `.json` | `json.loads()` | Parses without error, UTF-8 |
| `.py` | `pixi run check` | ruff + mypy + pyright pass |
| `.usda` | `pxr.Usd.Stage.Open()` | Stage opens without error |
| `.usdc` | `pxr.Usd.Stage.Open()` | Stage opens without error |
| `.ocio` | `PyOpenColorIO.Config.CreateFromFile()` | Config loads without error |
| `.vdb` | `openvdb.io.read()` | File reads, expected grids present |

**When to run**: Every artifact, every time.

---

## Gate 3: Collaboration Schema

Validates that the collaboration YAML conforms to the collaboration-protocol
and output-schemas specifications.

| Check | Pass Criteria |
|-------|---------------|
| Required fields present | All fields from collaboration-protocol universal format |
| Field types correct | String, int, float, bool, array match declared types |
| `from_agent` valid | Must be a recognized cinematographer agent |
| `to_agent` valid | Must be a recognized cinematographer or pipeline-expert agent |
| `tier` valid | Must be scout, preview, or final |
| `status` valid | Must be ready, pending_approval, blocked, or superseded |
| `payload` conforms | Matches exactly one output-schema |
| `audit_trail` non-empty | Provenance chain present |
| `next_action` non-empty | Downstream directive present |
| Independence firewall | No subjective language in payload |

**When to run**: Every collaboration YAML, every time.

---

## Gate 4: Code Quality

Validates that any Python code artifacts pass the project's standard
quality checks.

| Check | Tool | Pass Criteria |
|-------|------|---------------|
| Lint | `pixi run ruff check` | No errors with project ruff config |
| Type check (mypy) | `pixi run mypy` | No errors in strict mode |
| Type check (pyright) | `pixi run pyright` | No errors in strict mode |
| Tests | `pixi run pytest` | All tests pass |
| Spell check | `pixi run spell` | No typos |

**When to run**: Every `.py` artifact. Not applicable to YAML-only agents
(storyboarder, colorist).

---

## Gate 5: Constraint

Self-check against the golden rules defined in verdict-protocol's
constraint verification table.

| Constraint | Check Method | Pass Criteria |
|------------|-------------|---------------|
| Length units (meters) | Grid extent inspection | Physical dimensions match real-world scale |
| Temperature (Kelvin) | Grid value range check | Values in 293-3000K range |
| Voxel spacing | world_size / resolution | Computed spacing matches declared spacing |
| Grid names | OpenVDB grid name list | "density", "vel", "temperature" present |
| Sparse design | Non-zero voxel ratio | Exact 0.0 in empty regions |
| ACES pipeline | OCIO config inspection | ACEScg working space confirmed |
| Achromatic compliance | CDL neutral test | Neutral gray in = neutral gray out |

**When to run**: Final validation step, after all other gates pass.
Not all constraints apply to all artifact types — agents check only
the constraints relevant to their artifact.

---

## Gate Ordering

Gates must be evaluated in order. A failure at an earlier gate makes
later gates unreliable:

```
Gate 1 (Structure) -> Gate 2 (Format) -> Gate 3 (Schema) -> Gate 4 (Code) -> Gate 5 (Constraint)
```

If Gate 2 fails (artifact does not parse), Gate 3 (schema validation)
cannot meaningfully run. If Gate 4 fails (code quality), Gate 5
(constraint checks that run the code) cannot be trusted.

---

## Anti-Patterns

- **Gate skipping**: Running Gate 5 without confirming Gates 1-4 passed. Gate ordering exists because later gates depend on earlier ones.
- **Partial gate runs**: Running ruff but not mypy/pyright for a Python artifact. Gate 4 requires ALL code quality checks to pass.
- **Format assumption**: Assuming a YAML file is valid because it was generated by code. Always validate with `yaml.safe_load()`.
- **Silent gate failure**: A gate fails but the collaboration YAML is produced with `status: ready`. Failed gates MUST produce `status: blocked`.
- **Gate inflation**: Adding custom gate checks that are not defined here. New gates must be added to this specification first.

---

## Validation Checklist

- [ ] Gate 1 passed (plugin structure valid)
- [ ] Gate 2 passed (artifact format validates)
- [ ] Gate 3 passed (collaboration YAML conforms to schema)
- [ ] Gate 4 passed (code quality checks pass, if applicable)
- [ ] Gate 5 passed (golden rule constraints verified, if applicable)
- [ ] Gates evaluated in order (1 -> 2 -> 3 -> 4 -> 5)
- [ ] Failed gates produce `status: blocked` collaboration YAML
