---
name: constraint-derivation
user-invocable: false
---

# Constraint Derivation -- Physical Boundaries for Artistic Agents

Derives physical boundaries from the atmospheric state that govern all artistic
interpretations. The bridge between scientific data and creative freedom. The
Spectralist produces these constraints; Sculptor, Tonalist, and Choreographer
consume them.

---

## Constraint Grids Produced

| Constraint | Type | Derivation | Used By |
|------------|------|------------|---------|
| `transport_vectors` | Vec3fGrid | ERA5 wind field at density-weighted center altitude | Sculptor (turbulence direction), Choreographer (camera follow) |
| `max_kinetic_energy` | FloatGrid | 0.5 * rho * v^2 per voxel from wind + temperature | Sculptor (limits procedural turbulence amplitude) |
| `source_sink_mask` | FloatGrid | Divergence of XCO2 flux: positive = source, negative = sink | Sculptor (emission regions), Tonalist (density anchoring) |
| `shear_tensor` | FloatGrid | Gradient of wind velocity field (symmetric part of velocity gradient) | Sculptor (turbulence anisotropy direction) |
| `boundary_layer_height` | FloatGrid | ERA5 BLH field interpolated to target grid | Sculptor (vertical extent limit), Choreographer (camera ceiling) |

---

## Verifiable Artistic License Protocol

Any artistic parameter that modifies the physical field MUST stay within the
constraint envelope. Five rules:

1. **Turbulence amplitude**: At any voxel, procedural noise amplitude <= `max_kinetic_energy` at that voxel. Energy cannot appear from nowhere.
2. **Transport alignment**: Bulk transport direction of the plume must align with `transport_vectors` within +/- 30 degrees. Artistic rotation beyond this violates wind physics.
3. **Source coincidence**: Emission regions must coincide with positive `source_sink_mask` regions. CO2 does not appear where there is no source.
4. **Vertical extent**: Artistic volume must not exceed 2x `boundary_layer_height`. Above the boundary layer, free-atmospheric mixing dilutes concentration below visibility.
5. **Anisotropy direction**: Turbulence stretching axis must align with `shear_tensor` eigenvectors. Wind shear determines how turbulence deforms, not aesthetic preference.

Violation of any rule is a blocking CONCERN. Violation of rules 1-3 is a blocking FAIL.

---

## Constraint Derivation Workflow

```
ERA5 wind field (u, v, w)
  -> transport_vectors (density-weighted altitude selection)
  -> shear_tensor (velocity gradient computation)
  -> max_kinetic_energy (0.5 * rho * |v|^2)

ERA5 BLH field
  -> boundary_layer_height (interpolated to target grid)

Assimilated XCO2 + wind field
  -> XCO2 flux = XCO2 * wind_velocity
  -> source_sink_mask = divergence(XCO2 flux)
```

---

## Scientific Integrity Overlay

When requested, the Spectralist generates a validation visualization:

- Raw OCO-2/3 sounding locations as bright markers over artistic volume
- Transport vector arrows from ERA5 wind field
- data_confidence contours showing observation density
- Constraint envelope boundaries (boundary layer ceiling, source regions)

Purpose: "This is the data. This is the interpretation. The interpretation does not violate the physics."

---

## Constraint Grid Quality

- `transport_vectors` must be non-zero in plume regions (zero vectors = no transport data)
- `max_kinetic_energy` must be positive-definite (negative KE is nonphysical)
- `source_sink_mask` must contain both positive and negative regions (pure source or pure sink indicates assimilation failure)
- `shear_tensor` eigenvalues should show anisotropy ratio > 1.5 in sheared regions
- `boundary_layer_height` must vary spatially (uniform BLH indicates missing ERA5 data)
- All constraint grids share voxel size and world origin with the atmospheric state grids
