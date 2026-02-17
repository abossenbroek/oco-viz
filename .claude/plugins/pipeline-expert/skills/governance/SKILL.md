---
name: governance
user-invocable: false
---

# Creative Governance — RACI & Approval Gates

Defines the decision authority matrix, approval gates, and conceptual audit
trail requirements for the 7-agent pipeline-expert system.

---

## RACI Matrix

| Decision | Responsible | Accountable | Consulted | Informed |
|----------|-------------|-------------|-----------|----------|
| Artistic vision / mood | Auteur | Auteur | All | All |
| Transfer function design | Tonalist | Auteur | Sculptor | Choreographer, Installer |
| Volume material quality | Sculptor | Auteur | Tonalist, Spectralist | All |
| Camera / temporal arc | Choreographer | Auteur | Sculptor | Installer |
| Exhibition spatial design | Installer | Auteur | Choreographer | All |
| Data integrity | Spectralist | Spectralist | Auteur | All |
| Pipeline architecture | Alchemist | Alchemist | Spectralist | All |
| Lighting intent | Auteur | Auteur | Tonalist, Sculptor | Choreographer |
| Physical constraints | Spectralist | Spectralist | Sculptor | Auteur |

**Reading the matrix:**
- **Responsible** — does the work, produces the artifact
- **Accountable** — signs off, holds veto power (exactly one per decision)
- **Consulted** — provides input before the decision is made
- **Informed** — notified after the decision is made

---

## 7 Approval Gates

### Gate 1: Data Gate
**Owner:** Spectralist
**Certifies:** Ingested data maintains scientific integrity.
Source NetCDF/HDF5 passes validation. Metadata preserved. No silent
interpolation or unit conversion errors.
**Artifacts:** Data quality report, provenance record.

### Gate 2: Reconstruction Gate
**Owners:** Spectralist + Alchemist
**Certifies:** 4D field reconstruction is faithful to source observations.
Grid resolution sufficient. Temporal interpolation physically plausible.
No numerical artifacts.
**Artifacts:** Reconstruction validation report, grid fidelity metrics.

### Gate 3: Material Gate
**Owner:** Sculptor (presents) | Auteur + Tonalist (approve)
**Certifies:** Volume substance achieves artistic intent. Material reads
as coal dust / volcanic ash / charcoal — not digital simulation.
Turbulence character matches geological register.
**Artifacts:** Material test renders, substance comparison sheet.

### Gate 4: Lighting Gate
**Owner:** Auteur (specifies intent) | Tonalist (certifies color science) | Sculptor (confirms volume response)
**Certifies:** Lighting serves the emotional arc. Internal emission reads
as smoldering, not glowing. No unintended chromatic contamination.
Transfer function achieves density-to-dread mapping.
**Artifacts:** Lighting test renders, TF curve documentation.

### Gate 5: Composition Gate
**Owner:** Choreographer (presents) | Auteur (approves)
**Certifies:** Camera path and temporal arc achieve emotional trajectory.
Framing is deliberate (asymmetric, tensioned). Pacing matches the
weight of the material.
**Artifacts:** Camera path preview, temporal arc diagram.

### Gate 6: Exhibition Gate
**Owner:** Installer (presents) | Auteur (final sign-off)
**Certifies:** Spatial design serves the installation context. Projection
mapping correct. Void merges with room. Viewer positioning considered.
Audio-visual synchronization if applicable.
**Artifacts:** Installation mockup, spatial diagram, viewing distance analysis.

### Gate 7: Conservation Gate
**Owner:** Line Producer (presents) | Auteur (final sign-off)
**Certifies:** Conservation deliverables are prepared per
`plan/conservation_package_spec.md`. The work can be faithfully re-exhibited,
re-rendered, or migrated by a future conservator without production knowledge.
**Required for:** Exhibition delivery only. Not required for scout or preview tiers.
**Checks:**
- Source archive exists (git bundle + tar.gz) and checksums verified
- Dependency manifest current (pixi.lock, Docker image, system packages)
- Render configuration archive complete (all YAMLs, TF JSONs, continuity ledger)
- Asset archive complete with per-category SHA-256 manifests verified
- Artist intent documented (Variable Media Questionnaire, no blanks)
- Exhibition technical rider complete (no placeholder values)
- Emulation vs. migration decision documented for all components
- Master verification passes: all checksum manifests valid, Docker image boots
**Artifacts:** Conservation package at archive root, checksum manifests,
`conservation_complete: true` flag.

---

## Conceptual Audit Trail

Every artistic choice MUST be traceable through this chain:

```
data source -> observation -> artistic interpretation -> emotional intent -> parameter choice
```

**Example:**
```
ERA5 wind shear at 850hPa (12.3 m/s, 2024-03-15T14:00Z)
  -> visible atmospheric instability in reconstruction
  -> artistic: the plume tears against itself, internal violence
  -> emotional: the atmosphere as antagonist, disruption as dread
  -> parameter: turbulence anisotropy ratio 3:1, lacunarity 2.4,
     directional bias aligned to wind shear vector
```

**Rules:**
1. No parameter exists without a traceable path to a data source
2. Artistic interpretation is explicitly named — never implicit
3. Emotional intent is stated — not assumed from the interpretation
4. The chain is documented in the `audit_trail` field of all output schemas

---

## Governance Rules

1. **Single accountability.** Every decision has exactly one Accountable party.
2. **Auteur veto.** The Auteur holds veto on all creative decisions. Spectralist
   holds veto on all scientific integrity decisions. Neither can override the other's domain.
3. **Gate blocking.** A failed gate blocks all downstream stages. No exceptions.
4. **Consultation is mandatory.** Consulted parties must be engaged before sign-off.
   Skipping consultation invalidates the gate.
5. **Audit trail is non-optional.** Any verdict missing an audit trail is automatically
   downgraded to CONCERN pending documentation.
