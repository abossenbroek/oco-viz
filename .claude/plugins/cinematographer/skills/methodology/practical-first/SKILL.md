---
name: practical-first
user-invocable: false
type: methodology
primary_owner: dp
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Practical-First — Data-Driven Volumetric Rendering

John Nelson supervised 1200+ VFX shots on Blade Runner 2049 with a mandate from Denis
Villeneuve and Roger Deakins: "If you can shoot it, you must." Every synthetic element
had to justify its existence by proving the camera and practical effects could not
achieve the same result. For volumetric plume visualization the equivalent discipline
is: if the data contains the information, you must derive from data. Only when the VDB
density, gradient, and statistical profile are genuinely insufficient may procedural or
synthetic elements be introduced — and even then, they must be bounded to 15% of the
visual contribution.

> "If you can shoot it, you must." — John Nelson, VFX Supervisor, BR2049

---

## Principle

Analyze the VDB first. Extract every useful signal — density statistics, gradient
fields, directional bias, spatial frequency content — before touching a single
configuration parameter. The data is the plate. You are the VFX house. Your job is to
augment reality, not replace it.

The 85/15 rule: at minimum 85% of any rendered frame's visual content must derive
directly from measured or physically-modeled data. The remaining 15% budget covers
procedural turbulence, artistic color grading, and motivated synthetic lighting. If a
render requires more than 15% synthetic contribution to look acceptable, the upstream
data pipeline needs repair, not more VFX.

---

## Procedure

### Step 1 — Plate Analysis (VDB Statistical Profiling)

Before any rendering configuration, extract the data fingerprint:

```
1. Load VDB density field
2. Compute: min, max, mean, std, median, skewness, kurtosis
3. Compute: gradient magnitude field → histogram
4. Compute: directional bias (principal component of gradient vectors)
5. Compute: spatial frequency spectrum (FFT of central slice)
6. Record: voxel count, active voxel ratio (sparsity), bounding box dimensions
```

This profile tells you what the data can and cannot express on its own.

### Step 2 — Data Capability Assessment

Map the plate analysis to rendering requirements:

| Rendering Need | Data Signal | Assessment |
|----------------|-------------|------------|
| Volume structure | Density distribution | Sufficient if std/mean > 0.3 |
| Edge definition | Gradient magnitude | Sufficient if gradient p95 > 2x mean |
| Internal detail | Spatial frequency content | Sufficient if spectrum has energy above Nyquist/4 |
| Directional cues | Gradient PCA | Sufficient if first PC explains > 40% variance |
| Temporal coherence | Frame-to-frame density correlation | Sufficient if r > 0.85 |

### Step 3 — Gap Identification

For each rendering need assessed as insufficient, document the gap:

```
GAP: Edge definition — gradient p95 is only 1.2x mean
     Data lacks sharp density transitions at plume boundary
     BUDGET: procedural edge enhancement, max 5% of 15% synthetic budget
     METHOD: gradient-based opacity boost in transfer function
```

### Step 4 — Synthetic Budget Allocation

Distribute the 15% synthetic budget across identified gaps. Track every allocation:

| Component | Budget % | Justification |
|-----------|----------|---------------|
| Procedural turbulence | 0-5% | Only if spatial frequency analysis shows gaps |
| Transfer function shaping | 0-5% | Artistic interpretation of density-to-color mapping |
| Synthetic lighting | 0-3% | Motivated sources not derivable from data |
| Post-processing | 0-2% | Bloom, tonemap, grain |
| **Total synthetic** | **<= 15%** | **Hard ceiling** |

### Step 5 — Implementation with Provenance

Every configuration value must be traceable to either data or budget allocation:

```yaml
# DATA-DRIVEN: derived from VDB density statistics
density_scale: 1.0        # provenance: mean=0.42, maps to mid-opacity
opacity_center: 0.42      # provenance: density mean from plate analysis

# SYNTHETIC: budget allocation — 3% for edge enhancement
edge_boost_factor: 1.3    # provenance: GAP-001, gradient p95 insufficient
edge_boost_width: 0.05    # provenance: GAP-001, transition zone from gradient histogram
```

---

## Parameters

### Data Analysis Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `min_data_coverage` | float | 0.85 | 0.80 - 1.0 | Minimum fraction of visual content from data |
| `max_synthetic_budget` | float | 0.15 | 0.0 - 0.20 | Maximum synthetic contribution fraction |
| `gradient_sufficiency_ratio` | float | 2.0 | 1.5 - 3.0 | p95/mean gradient ratio for "sufficient edges" |
| `frequency_sufficiency_cutoff` | float | 0.25 | 0.1 - 0.5 | Fraction of Nyquist where energy must exist |
| `variance_explained_threshold` | float | 0.40 | 0.3 - 0.6 | PCA threshold for directional sufficiency |
| `temporal_correlation_min` | float | 0.85 | 0.75 - 0.95 | Minimum frame-to-frame correlation |

### Provenance Tracking

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provenance_required` | bool | true | Every config value must have a provenance tag |
| `budget_tracking_enabled` | bool | true | Track synthetic budget allocation |
| `gap_documentation_required` | bool | true | Each synthetic element needs a GAP reference |

---

## Presets

### Full Practical

Zero synthetic budget. Everything derived from data. Use for validation renders to
see exactly what the data provides before any artistic intervention.

```yaml
min_data_coverage: 1.0
max_synthetic_budget: 0.0
edge_boost_factor: 1.0
procedural_turbulence: 0.0
post_processing: none
```

### Standard Production

Standard 85/15 split with typical budget allocation for well-formed VDB data.

```yaml
min_data_coverage: 0.85
max_synthetic_budget: 0.15
budget_turbulence: 0.04
budget_transfer_function: 0.05
budget_synthetic_light: 0.03
budget_post_processing: 0.02
provenance_required: true
```

### Data Recovery

For datasets with known quality issues (low resolution, sparse sampling). Allows
a wider synthetic budget but requires explicit gap documentation for every percentage
point above 15%.

```yaml
min_data_coverage: 0.80
max_synthetic_budget: 0.20
budget_turbulence: 0.08
budget_transfer_function: 0.06
budget_synthetic_light: 0.03
budget_post_processing: 0.03
gap_documentation_required: true  # mandatory for over-budget allocations
provenance_required: true
```

---

## Anti-Patterns

### 1. The Magic Number

**Symptom:** Configuration files contain hardcoded numerical values with no comment
explaining their origin. Values like `opacity_scale: 0.73` or `turbulence_freq: 4.2`
appear without provenance.

**Cause:** Parameters tuned by trial-and-error in a single render session, then
committed without recording why they work. The next person (or the same person in two
weeks) has no idea whether the value is load-bearing or arbitrary.

**Fix:** Every numerical parameter must have a provenance tag: either a reference to
data statistics (`# density p75 = 0.73`) or a budget allocation (`# SYNTHETIC: 3% edge
enhancement`). If you cannot explain where a number comes from, it is a magic number
and must be re-derived.

**Nelson reference:** On BR2049 every VFX parameter had to trace back to either a
practical plate measurement or an explicit creative decision documented in dailies notes.

### 2. The Fantasy Light

**Symptom:** Beautiful lighting that has no relationship to any physical source in the
scene. Colored rim lights, dramatic backlights, and atmospheric glows that exist purely
for visual appeal.

**Cause:** Lighting designed in isolation from the data, treating the VDB as a canvas
rather than a plate. The artist projected their aesthetic onto the data instead of
discovering what the data suggests.

**Fix:** Return to Step 2. What does the data's directional bias tell you about where
light would naturally come from? If the gradient PCA points predominantly upward, the
natural key direction is from above. Synthetic lighting must follow the data's
directional language.

### 3. The Procedural Crutch

**Symptom:** Heavy procedural turbulence, noise fields, or detail enhancement applied
uniformly across the volume. The render looks rich but the richness is artificial — it
does not match the actual data's spatial characteristics.

**Cause:** Using procedural generation to compensate for upstream data quality issues
instead of fixing the data pipeline. The 15% synthetic budget is consumed by a single
band-aid.

**Fix:** If the data lacks detail, the fix is upstream: higher resolution sampling,
better interpolation, corrected normalization. Procedural detail should add accent, not
structure.

### 4. The Unaudited Render

**Symptom:** A render is approved without anyone checking what percentage of the visual
content derives from data versus synthetic sources. The image looks good, so it ships.

**Cause:** No budget tracking in the pipeline. The 85/15 rule exists in principle but
is never measured.

**Fix:** Implement provenance tracking. Every configuration value tagged with its
source. At render time, compute the synthetic contribution percentage. If it exceeds
budget, the render fails review regardless of visual quality.

---

## Validation Checklist

- [ ] VDB plate analysis completed before any rendering configuration
- [ ] Density statistics extracted: min, max, mean, std, median, skewness, kurtosis
- [ ] Gradient magnitude histogram computed and assessed
- [ ] Directional bias (gradient PCA) computed
- [ ] Data capability assessment completed for all five rendering needs
- [ ] Gaps documented with GAP-NNN identifiers
- [ ] Synthetic budget allocated and totals <= 15% (or <= 20% with explicit override documentation)
- [ ] Every configuration value has a provenance comment (data reference or budget allocation)
- [ ] No magic numbers — all values traceable
- [ ] Full-practical render (0% synthetic) reviewed as baseline before artistic render
- [ ] Budget tracking log committed alongside configuration files
