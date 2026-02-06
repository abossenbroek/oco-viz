---
name: data-quality
user-invocable: false
---

# Data Quality -- Stage 1: Ingestion Gate

Scientific integrity of ingested atmospheric data. The foundation upon which
all artistic interpretation rests. Corrupt data produces meaningless art.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| OCO-2/3 quality flags | Only `xco2_quality_flag == 0` retained | Flag distribution count (good vs rejected) |
| Bias correction | Applied against TCCON (bias < 0.3 ppm) | Validation statistics at TCCON station locations |
| Spatial coverage | Sufficient soundings for reconstruction | Sounding density map over target domain |
| Temporal alignment | All sources within +/-1 hour | Timestamp comparison across OCO, ERA5, TROPOMI |
| Missing data flagged | Gaps explicitly marked in confidence grid | Confidence grid inspection (values -> 0 in gaps) |
| ERA5 consistency | Wind/pressure/temperature internally consistent | Divergence check + CF-convention metadata |
| Sounding uniqueness | No duplicate `sounding_id` values | Uniqueness verification |
| Spectral bands | 1.61 um (weak CO2), 2.06 um (strong CO2), 0.76 um (O2 A-band) | Product metadata verification |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | All quality flags applied. Bias correction validated. Spatial coverage sufficient. Temporal alignment verified. Missing data explicitly flagged. ERA5 internally consistent. |
| CONCERN | Quality flags applied but marginal sounding density. Bias correction applied but TCCON comparison shows 0.3-0.5 ppm residual. Minor temporal misalignment. |
| FAIL | Quality flags not applied or wrong flag field used. No bias correction. Insufficient sounding coverage for reconstruction. Missing data not flagged. ERA5 fields inconsistent. |

---

## Agent Responsibility

Primary: Spectralist
