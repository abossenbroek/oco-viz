---
name: audit
description: Comprehensive cross-stage pipeline audit with conceptual audit trail
user-invocable: true
---

# Audit Command

Comprehensive cross-stage pipeline audit orchestrated by the Auteur as creative
director. Reviews each stage with its domain agent, then synthesizes findings
into a unified assessment with a conceptual audit trail.

## Usage

```
/pipeline-expert:audit [--stages stage1,stage2,...] [--focus area]
```

## Arguments

- `--stages`: (optional) Comma-separated stages to audit. Default: all 5 stages
  (ingestion, reconstruction, conversion, rendering, exhibition).
- `--focus`: (optional) Focus area: `scientific-integrity`, `artistic-coherence`,
  `pipeline-health`, or `all`. Default: `all`.

## Agent Flow

1. **Auteur** orchestrates the audit as creative director
2. Each stage is reviewed by its primary agent (per review-stage routing):
   - Ingestion: Spectralist
   - Reconstruction: Spectralist
   - Conversion: Alchemist
   - Rendering: Tonalist + Sculptor
   - Exhibition: Installer
3. **Spectralist** provides scientific integrity assessment across all stages,
   verifying that artistic license does not violate the constraint envelope
4. **Auteur** provides artistic coherence assessment across all stages, checking
   that the creative vision survives every pipeline transformation
5. Cross-stage issues identified (e.g., constraint violation between stages,
   metadata lost in conversion that affects rendering quality)
6. Conceptual audit trail generated
7. Output: `audit_report` YAML per output-schemas

## The Conceptual Audit Trail

For any finding, the audit traces the full chain from data to emotion:

```
data source (OCO-2/3 sounding, ERA5 field)
  -> observation (XCO2 spike, wind shear)
    -> interpretation (emission event, atmospheric instability)
      -> artistic decision (density emphasis, turbulence direction)
        -> emotional intent (confrontation, dread, weight)
          -> parameter choice (TF curve, noise amplitude, camera position)
```

This ensures every artistic choice is traceable back to physical data, and
every technical parameter is justified by creative intent.

## Focus Areas

| Focus | What Is Assessed |
|-------|-----------------|
| scientific-integrity | Data quality, reconstruction fidelity, constraint envelope compliance |
| artistic-coherence | Creative vision preservation, emotional arc, material consistency |
| pipeline-health | Format conversions, metadata chain, dependency graph, cache validity |
| all | All three focus areas combined |

## Examples

```
/pipeline-expert:audit
/pipeline-expert:audit --stages ingestion,reconstruction --focus scientific-integrity
/pipeline-expert:audit --focus artistic-coherence
/pipeline-expert:audit --stages rendering,exhibition --focus pipeline-health
```

$ARGUMENTS parsed for `--stages` and `--focus` flags.
