---
name: stage-1-gate
user-invocable: false
---

# Stage 1 Gate -- Ingestion Visual QA

Visual quality assessment for Stage 1 (Data Ingestion) outputs. Reviews
visualizations of ingested data to verify that the raw satellite and
reanalysis data has been correctly loaded and filtered.

---

## What to Check

- **Data coverage map**: Are OCO-2/3 soundings visible at expected lat/lon locations?
- **Quality flag distribution**: Proportion of good vs filtered soundings
- **Temporal coverage**: Time series shows expected observation windows
- **ERA5 overlay**: Wind and pressure fields align spatially with sounding locations

---

## Visual Criteria

| Check | What to Look For | PASS If | CONCERN If | FAIL If |
|-------|-----------------|---------|------------|---------|
| Sounding locations | Points on map at expected lat/lon | Points cluster at expected ROI | Points present but sparse | No points visible or outside ROI |
| Quality filtering | Visible reduction from raw to filtered | Clear reduction, reasonable proportion | Marginal filtering (< 10% removed) | 0% filtered or > 90% filtered |
| Coverage gaps | Distribution across target domain | Uniform-ish distribution | Minor gaps in coverage | Entire sub-region missing data |
| ERA5 alignment | Wind vectors overlay with soundings | Vectors consistent with sounding locations | Minor spatial offset (< 0.5 deg) | Obvious spatial mismatch (> 1 deg) |
| Temporal range | Observations span expected time window | Full expected window covered | Partial window (> 50%) | < 50% of expected window |

---

## Procedure

1. Read the stage output visualization image
2. Run `pixi run image-stats` for quantitative pixel measurements
3. Check each criterion in the table above
4. If the visualization includes a map projection, verify coordinate system is consistent
5. Produce verdict: PASS / CONCERN / FAIL with specific observations

---

## Common Failure Modes

- Empty map (no soundings ingested -- file path or format error)
- All soundings filtered (quality flag field name mismatch)
- ERA5 fields rotated 180 degrees (longitude convention error)
- Soundings clustered at (0,0) -- missing geolocation
