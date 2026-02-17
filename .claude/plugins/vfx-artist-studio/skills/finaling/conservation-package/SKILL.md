---
name: conservation-package
user-invocable: false
type: instruction
primary_owner: line-producer
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Conservation Package --- MoMA/Tate-Grade Preservation Pipeline

A shot can pass all 6 governance gates and be delivered without any conservation
deliverables. This skill closes that gap. It operationalizes the authoritative
specification in `plan/conservation_package_spec.md` into a step-by-step
procedure that the line-producer executes after shot finaling and exhibition
delivery are complete. Conservation is not optional for exhibition delivery ---
it is the final production obligation before the work leaves the studio.

The conservation package ensures that *Soot* can be faithfully re-exhibited,
re-rendered, or migrated decades from now, following Variable Media Network
best practices, Tate's time-based media conservation guidelines, and MoMA's
digital art acquisition protocols.

> "The work must survive the death of its dependencies."

---

## Principle

Exhibition delivery produces the media. Conservation preserves the means of
production. Without a conservation package, the exhibition media is an orphan ---
playable today, unreproducible tomorrow. Every software dependency, every
creative decision, every hardware specification, and every data source must be
archived in a form that a conservator with no knowledge of the production can
use to reconstruct or migrate the work.

The conservation package is REQUIRED for exhibition-tier delivery. It is not
required for scout or preview tiers, where the pipeline is still evolving and
archival snapshots would be premature.

---

## Procedure

### Step 1 --- Source Code Archive

Create a complete, self-contained snapshot of the repository at the exhibition
version.

```
SOURCE CODE ARCHIVE:
1. Tag the exhibition commit:
   git tag -a v1.0-exhibition -m "Exhibition version for conservation archive"
2. Create git bundle (single-file, portable):
   git bundle create oco-viz-v1.0-exhibition.bundle --all
3. Create working tree snapshot:
   git archive --format=tar.gz --prefix=oco-viz-v1.0-exhibition/ HEAD \
     > oco-viz-v1.0-exhibition.tar.gz
4. Verify git bundle:
   git bundle verify oco-viz-v1.0-exhibition.bundle
5. Generate SHA-256 for both artifacts:
   sha256sum oco-viz-v1.0-exhibition.bundle >> checksums/source.sha256
   sha256sum oco-viz-v1.0-exhibition.tar.gz >> checksums/source.sha256
6. Place in archive: /source/

EXCLUDES: .git/hooks, .env files, credentials, API keys
```

### Step 2 --- Dependency Manifest

Capture the exact frozen state of every dependency --- language-level, OS-level,
and toolchain.

```
DEPENDENCY MANIFEST:
1. Copy pixi.lock to archive:
   cp pixi.lock /source/dependencies/
2. Copy pyproject.toml:
   cp pyproject.toml /source/dependencies/
3. Generate pip freeze from Docker image:
   docker run oco-viz:exhibition pip freeze > requirements-frozen.txt
   cp requirements-frozen.txt /source/dependencies/
4. Record system packages:
   docker run oco-viz:exhibition dpkg -l > system-packages.txt
   cp system-packages.txt /source/dependencies/
5. Save Docker image:
   docker save oco-viz:exhibition | gzip > oco-viz-exhibition.tar.gz
   cp oco-viz-exhibition.tar.gz /source/docker/
   cp Dockerfile /source/docker/
6. Verify Docker image round-trips:
   docker load < /source/docker/oco-viz-exhibition.tar.gz
   docker run oco-viz:exhibition python -c "import oco_viz; print(oco_viz.__version__)"
7. Generate SHA-256:
   sha256sum /source/dependencies/* >> checksums/source.sha256
   sha256sum /source/docker/* >> checksums/docker.sha256
```

### Step 3 --- Render Configuration Archive

Archive every configuration artifact that governs the rendered output.

```
RENDER CONFIGURATION ARCHIVE:
1. Copy all YAML configs:
   cp -r configs/ /documentation/plan/configs/
2. Copy transfer function JSONs:
   cp -r src/oco_viz/config/tf_*.json /documentation/plan/tf/
3. Copy visual_language.yaml:
   cp plan/visual_language.yaml /documentation/plan/
4. Copy continuity ledger:
   cp continuity_ledger.yaml /documentation/plan/
5. Copy exhibition-delivery-spec.yaml:
   cp exhibition-delivery-spec.yaml /documentation/plan/
6. Copy all plan documents:
   cp plan/shot_design.md /documentation/plan/
   cp plan/curatorial_framework.md /documentation/plan/
   cp plan/technical_rider.md /documentation/plan/
   cp plan/print_spec.md /documentation/plan/
   cp plan/prd.md /documentation/plan/
7. Generate SHA-256 for all config artifacts:
   find /documentation/plan/ -type f -exec sha256sum {} \; >> checksums/documentation.sha256
```

### Step 4 --- Asset Archive

Archive all rendered assets with integrity verification.

```
ASSET ARCHIVE:
1. Copy OpenVDB caches:
   cp -r output/vdb/ /data/processed/vdb/
2. Copy gallery PNGs:
   cp -r output/examples/ /media/gallery/
3. Copy EXR frame sequences (exhibition masters):
   cp -r output/exr/ /media/master/
4. Copy ProRes master:
   cp output/descent-of-carbon.mov /media/master/
5. Copy H.265 playback version:
   cp output/descent-of-carbon.mp4 /media/master/
6. Copy print hero EXRs:
   cp output/print/*.exr /media/print/
7. Generate per-category SHA-256 manifests:
   find /data/processed/ -type f -exec sha256sum {} \; > checksums/data-processed.sha256
   find /media/master/ -type f -exec sha256sum {} \; > checksums/media-master.sha256
   find /media/gallery/ -type f -exec sha256sum {} \; >> checksums/media-master.sha256
   find /media/print/ -type f -exec sha256sum {} \; >> checksums/media-master.sha256
8. Verify all checksums pass:
   sha256sum -c checksums/data-processed.sha256
   sha256sum -c checksums/media-master.sha256
```

### Step 5 --- Artist Intent Documentation

Complete the Variable Media Questionnaire from `plan/conservation_package_spec.md`
Section 5. This is the conservator's primary reference for understanding what is
essential vs. migratable.

```
ARTIST INTENT DOCUMENTATION:
1. Extract Variable Media Questionnaire (Section 5) from conservation_package_spec.md
2. Verify all questions have responses (no blanks, no TBD):
   - Section 5.1: Work Identity (4 questions)
   - Section 5.2: Display (4 questions)
   - Section 5.3: Sound (3 questions)
   - Section 5.4: Space (4 questions)
   - Section 5.5: Future Scenarios (5 questions)
3. Cross-reference Essential vs. Migratable tables (Section 1) against questionnaire
4. Export questionnaire as standalone document:
   cp variable-media-questionnaire.md /documentation/
5. Generate SHA-256:
   sha256sum /documentation/variable-media-questionnaire.md >> checksums/documentation.sha256
```

### Step 6 --- Exhibition Technical Rider

Archive the hardware and environmental specifications required for installation.

```
EXHIBITION TECHNICAL RIDER:
1. Verify technical rider document is current:
   - Hardware specs (Section 8 of conservation_package_spec.md)
   - Installation manual (Section 9)
   - Troubleshooting guide
2. Verify all hardware entries are populated (no [version] or [Model] placeholders)
3. Verify redundancy plan is documented (primary + backup for each critical component)
4. Verify environmental requirements:
   - Room dimensions: minimum 6m x 8m x 3.5m
   - Ambient light: < 1.0 lux
   - Acoustic: sub-bass 20-40 Hz at 75-80 dB(C)
5. Export as standalone documents:
   cp installation-manual.md /documentation/
   cp technical-rider.md /documentation/
6. Generate SHA-256:
   sha256sum /documentation/installation-manual.md >> checksums/documentation.sha256
   sha256sum /documentation/technical-rider.md >> checksums/documentation.sha256
```

### Step 7 --- Emulation vs. Migration Decision

Document the preservation strategy for each component. This decision determines
how a conservator approaches the work when dependencies become obsolete.

```
EMULATION vs. MIGRATION DECISION:

For each component, document ONE of:
  - EMULATE: Run original software in a container/VM (preferred for source code)
  - MIGRATE: Rewrite/transcode to contemporary technology (preferred for media)
  - BOTH: Maintain emulation path AND migration path (for critical components)

Component Decisions:
  1. Source code (oco-viz Python pipeline):
     Strategy: EMULATE via Docker image
     Rationale: Docker preserves exact execution environment
     Fallback: MIGRATE if Docker itself becomes obsolete

  2. Rendering output (EXR/ProRes/H.265):
     Strategy: MIGRATE to contemporary codecs as needed
     Rationale: Display technology changes; media must follow
     Constraint: Must preserve 10-bit+ depth, visually lossless

  3. Scientific data (NetCDF/HDF5):
     Strategy: EMULATE (formats are archival-grade, self-describing)
     Rationale: NetCDF/HDF5 are designed for long-term preservation

  4. VDB volume caches:
     Strategy: BOTH — emulate via pyopenvdb, migrate if VDB format evolves
     Rationale: VDB is industry standard but may evolve

  5. Playback hardware (BrightSign):
     Strategy: MIGRATE to equivalent hardware
     Rationale: Hardware has finite lifespan; specification preserves intent

  6. Display technology:
     Strategy: MIGRATE per Variable Media Questionnaire Section 5.2
     Rationale: Display tech evolves; true black + 4:5 + 4K is the requirement

Document in: /documentation/emulation-migration-decisions.md
Generate SHA-256:
  sha256sum /documentation/emulation-migration-decisions.md >> checksums/documentation.sha256
```

---

## Verification

After all 7 steps are complete, run the master verification:

```
CONSERVATION PACKAGE VERIFICATION:
1. Verify archive structure matches plan/conservation_package_spec.md Section 12
2. Verify ALL checksum manifests exist:
   - checksums/source.sha256
   - checksums/data-raw.sha256 (if raw data archived)
   - checksums/data-processed.sha256
   - checksums/media-master.sha256
   - checksums/docker.sha256
   - checksums/documentation.sha256
3. Verify ALL checksums pass:
   for manifest in checksums/*.sha256; do
     sha256sum -c "$manifest" || echo "FAIL: $manifest"
   done
4. Verify git bundle is valid:
   git bundle verify /source/oco-viz-v1.0-exhibition.bundle
5. Verify Docker image boots and runs:
   docker load < /source/docker/oco-viz-exhibition.tar.gz
   docker run oco-viz:exhibition python -c "import oco_viz; print('OK')"
6. Verify Variable Media Questionnaire has no blank responses
7. Verify technical rider has no placeholder values
8. Verify emulation/migration decision documented for all 6 components

RESULT: ALL checks pass → conservation_complete: true
        ANY check fails → conservation_complete: false, list failures
```

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `archive_root` | path | `soot-conservation-package-v1.0/` | Root directory for the conservation archive |
| `exhibition_tag` | string | `v1.0-exhibition` | Git tag for the exhibition commit |
| `checksum_algorithm` | string | SHA-256 | Hash algorithm for integrity verification |
| `docker_image_tag` | string | `oco-viz:exhibition` | Docker image tag for the frozen environment |
| `require_raw_data` | bool | false | Whether to include raw scientific data (large) |

---

## Tier Applicability

| Tier | Conservation Required | Rationale |
|------|----------------------|-----------|
| Scout | No | Pipeline is evolving; archival snapshot would be premature |
| Preview | No | Technical quality validation in progress; not exhibition-ready |
| Exhibition | **Yes** | Conservation is a delivery obligation, not an optional extra |

---

## Anti-Patterns

### 1. Conservation as Afterthought

**Symptom:** Exhibition delivery is approved, media is sent to the venue, and
conservation deliverables are "planned for later." Later never arrives. The
work is exhibited without a preservation package.

**Cause:** Conservation is not in the governance gate chain. It has no blocking
authority. Production pressure deprioritizes it because it does not affect the
current exhibition.

**Fix:** Gate 7 (Conservation) in the governance chain blocks exhibition sign-off
until conservation deliverables are verified. Conservation is not a post-delivery
task --- it is a delivery prerequisite.

### 2. Stale Archive

**Symptom:** The conservation archive was created at an earlier version. Since
then, transfer functions were tuned, configs were updated, and the exhibition
media was re-rendered. The archive no longer matches the exhibited work.

**Cause:** Conservation package was created once and never updated. The pipeline
continued to evolve after the archive was frozen.

**Fix:** The conservation package is generated from the exact commit tagged
`v1.0-exhibition`. If any change is made after tagging, the tag must be moved
and the conservation package regenerated. The git bundle and Docker image must
match the exhibited output.

### 3. Missing Checksums

**Symptom:** Archive files exist but cannot be verified. A conservator discovers
a corrupted VDB file years later with no way to know whether the corruption
occurred during storage or was present at archive time.

**Cause:** Checksum generation was skipped for some file categories. The manifest
is incomplete.

**Fix:** Every file in the archive has a SHA-256 checksum in a category manifest.
The verification procedure checks all manifests. A missing checksum is treated
as a conservation failure, not an oversight.

---

## Validation Checklist

- [ ] Source code archive: git bundle created and verified (Step 1)
- [ ] Source code archive: working tree tar.gz created (Step 1)
- [ ] Source code archive: SHA-256 checksums in checksums/source.sha256
- [ ] Dependency manifest: pixi.lock, pyproject.toml, requirements-frozen.txt archived (Step 2)
- [ ] Dependency manifest: system packages list archived (Step 2)
- [ ] Dependency manifest: Docker image saved, verified, and checksummed (Step 2)
- [ ] Render configs: all YAML configs, TF JSONs, continuity ledger archived (Step 3)
- [ ] Render configs: visual_language.yaml and plan documents archived (Step 3)
- [ ] Assets: VDB caches, gallery PNGs, EXR sequences archived (Step 4)
- [ ] Assets: all checksums generated and verified (Step 4)
- [ ] Artist intent: Variable Media Questionnaire complete, no blanks (Step 5)
- [ ] Technical rider: hardware specs, installation manual, no placeholders (Step 6)
- [ ] Emulation/migration: decision documented for all 6 components (Step 7)
- [ ] Master verification: all checksum manifests pass (Verification)
- [ ] Master verification: git bundle valid, Docker image boots
- [ ] Archive structure matches plan/conservation_package_spec.md Section 12
- [ ] conservation_complete flag set to true
