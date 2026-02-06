---
name: reconstruction-fidelity
user-invocable: false
---

# Reconstruction Fidelity -- Stage 2: Reconstruction Gate

4D field accuracy. The assimilated atmospheric state must be physically
coherent, temporally smooth, and spatially consistent with observations.

---

## Criteria

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| TCCON validation | RMSE < 1.5 ppm against ground truth | Cross-validation statistics at station locations |
| Spatial coherence | No discontinuities in reconstructed field | Gradient magnitude analysis (no delta-function spikes) |
| Temporal coherence | Smooth evolution (no frame-to-frame jumps) | Temporal difference between consecutive time steps |
| Confidence calibration | High near soundings, low in gaps | Confidence map spatial structure (not uniform) |
| Mass conservation | Within 5% over domain lifetime | Flux balance: inflow + sources = outflow + sinks +/- 5% |
| Resolution adequacy | >= 96x96x64 (exhibition), >= 48x48x32 (study) | Grid dimensions check |
| Assimilation method | Choice justified (4D-Var / EnKF / hybrid) | Method documentation with rationale |
| Background covariance | Spatial structure present (not diagonal) | B-matrix inspection or ensemble spread |

---

## Assessment

| Level | Description |
|-------|-------------|
| PASS | TCCON RMSE < 1.5 ppm. Spatial and temporal coherence verified. Confidence shows expected spatial structure. Mass conserved within 5%. Resolution meets tier requirement. |
| CONCERN | TCCON RMSE 1.5-2.0 ppm. Minor spatial discontinuities at domain boundaries. Confidence structure present but noisy. Mass conservation 5-10%. |
| FAIL | TCCON RMSE > 2.0 ppm. Spatial discontinuities or temporal jumps in field. Uniform confidence (assimilation failure). Mass conservation > 10%. Resolution below tier minimum. |

---

## Agent Responsibility

Primary: Spectralist
