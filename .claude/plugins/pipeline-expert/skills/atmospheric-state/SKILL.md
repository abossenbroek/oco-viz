---
name: atmospheric-state
user-invocable: false
---

# Atmospheric State -- Multi-Sensor Assimilation to 4D Field

Multi-sensor data assimilation producing a multi-layered volumetric data substrate.
The Spectralist uses this skill to ingest, fuse, and validate atmospheric observations
into a coherent 4D field suitable for artistic interpretation.

---

## Input Sources

| Source | Product | Spatial | Temporal | Key Variables |
|--------|---------|---------|----------|---------------|
| OCO-2/3 | L2 Lite v11.2r | ~1.3 x 2.25 km footprint | ~16-day repeat | XCO2, xco2_uncertainty, quality_flag, sounding_id |
| ERA5 | Reanalysis | 0.25 deg x 0.25 deg | Hourly | u/v/w wind, T, P, BLH, specific humidity |
| CALIOP | L2 aerosol/cloud | 333 m horizontal | ~16-day | Backscatter profile, extinction, depolarization ratio |
| MODIS | L1B radiance + L2 | 250 m - 1 km | ~daily | True color context, cloud mask, AOD |
| TROPOMI | L2 NO2 | 3.5 x 7 km | ~daily | NO2 column (co-emission tracer) |

**Data access**: NASA EarthData Search, OPeNDAP APIs, ECMWF Climate Data Store (CDS).
Formats: NetCDF4/HDF5, accessed via `xarray` with `netCDF4` or `h5netcdf` backends.
Large-scale processing: `dask` for parallel, out-of-core computation.

---

## Preprocessing

1. **OCO-2/3**: Filter `xco2_quality_flag == 0`. Apply bias-corrected field `xco2_bias_corrected`. Validate `sounding_id` uniqueness. Apply averaging kernels for vertical profile derivation.
2. **ERA5**: Retrieve via CDS API. Regrid to target domain if needed. Verify CF-convention metadata.
3. **CALIOP**: Regrid vertical profiles to common altitude grid. Apply cloud/aerosol classification.
4. **MODIS**: Cloud screening. AOD retrieval with AERONET cross-validation.
5. **TROPOMI**: NO2 column extraction. Co-locate with OCO-2/3 soundings for co-emission analysis.

---

## Assimilation Methods

| Method | Use Case | Strengths | Weakness |
|--------|----------|-----------|----------|
| **4D-Var** | Optimal trajectory reconstruction | Dynamically consistent, uses full model adjoint, broad spatial impact | Computationally expensive, requires adjoint model |
| **EnKF** | Ensemble-based uncertainty | Flow-dependent error covariances, natural uncertainty quantification | Ensemble size limits, requires careful tuning |
| **4D-LETKF** | Efficient ensemble | Highly parallelizable, no adjoint needed, comparable to 4D-Var in observed regions | Localized influence in sparse-data areas |
| **Hybrid** | Combine climatological + flow-dependent | Robust in sparse-data regions, balances accuracy and cost | Tuning of hybrid weights required |

**Key components**: Background error covariance (B matrix), observation error covariance (R matrix), observation operators (averaging kernels for OCO-2/3).

---

## Output VDB Layers

| Grid Name | Type | Content |
|-----------|------|---------|
| `co2_density` | FloatGrid | Assimilated XCO2 field, normalized 0-1 |
| `wind_velocity` | Vec3fGrid | u, v, w components (m/s) |
| `temperature` | FloatGrid | Air temperature (K) |
| `pressure` | FloatGrid | Atmospheric pressure (Pa) |
| `data_confidence` | FloatGrid | Assimilation confidence 0-1 (high near soundings, low in gaps) |

All grids share the same `voxelSize` and `worldOrigin` via `pyopenvdb.createLinearTransform`.
Metadata embedded: source attribution, timestamp, data range, voxel size, CRS.

---

## Quality Gates

- XCO2 validated against TCCON: bias < 0.3 ppm, RMSE < 1.5 ppm
- Wind fields validated against radiosonde profiles
- data_confidence grid must show spatial structure (not uniform) -- decay away from sounding locations
- Missing data regions explicitly flagged (confidence -> 0)
- CRS consistency verified across all input sources
- Round-trip numerical integrity: source -> assimilation -> output within float32 tolerance
- Metadata CF-convention compliance at every stage
