# Print Specification: "Soot" Archival Pigment Prints

**Version**: 1.0
**Status**: Production
**Work Title**: *Soot* (2026)
**Document Purpose**: Complete specification for archival print output — paper, printer, ICC profiling, resolution, rendering, soft-proofing, and edition management.

---

## 1. Paper Selection

### Primary: Hahnemuhle Photo Rag Baryta 315gsm

| Parameter | Specification |
|-----------|---------------|
| **Paper** | Hahnemuhle Photo Rag Baryta 315gsm |
| **Surface** | Semi-gloss baryta coating on 100% cotton rag base |
| **Dmax** | ~2.3 (measured with X-Rite i1Pro3 on profiled printer) |
| **Base White** | Warm white (optical brightener-free — critical for archival permanence) |
| **Archival Rating** | Museum-grade, acid-free, OBA-free, passes ISO 9706 |
| **Weight** | 315 gsm — sufficient rigidity for float-mount presentation |
| **Why This Paper** | Baryta coating delivers the highest Dmax available on a cotton rag base. The semi-gloss surface preserves shadow detail that matte papers absorb. For an achromatic work where black depth IS the aesthetic, Dmax is the primary selection criterion |

### Alternative: Canson Infinity Platine Fibre Rag 310gsm

| Parameter | Specification |
|-----------|---------------|
| **Paper** | Canson Infinity Platine Fibre Rag 310gsm |
| **Surface** | Gloss platine (slightly warmer than Hahnemuhle) |
| **Dmax** | ~2.25 |
| **Use Case** | If Hahnemuhle is unavailable, or if a slightly warmer tonal base is preferred for a specific venue |

### Rejected: Matte Papers

Matte papers (Hahnemuhle Photo Rag, Canson Rag Photographique, etc.) achieve a Dmax of approximately 1.5. For *Soot*, this is unacceptable — the work depends on the black void approaching perceptual absence. At Dmax 1.5, the "void" is a visible dark grey. The baryta coating adds approximately 0.8 stops of additional black depth. This is not a subtle difference; it is the difference between a print that reads as "black" and one that reads as "dark grey."

---

## 2. Printer

### Primary: Epson UltraChrome Pro12

| Parameter | Specification |
|-----------|---------------|
| **Printer** | Epson SC-P9570 (44" wide-format) |
| **Ink Set** | UltraChrome Pro12 — 12-channel including Violet, Orange, and Green |
| **Black Inks** | Photo Black (PK) for baryta/gloss, Matte Black (MK) for matte |
| **Ink Selection** | Photo Black (PK) — automatically selected for baryta paper |
| **Print Head** | PrecisionCore Micro TFP (2.5" wide, variable droplet) |
| **Max Print Width** | 44" (1118mm) |
| **Why This Printer** | 12-channel ink set delivers the widest gamut on achromatic work — the additional ink channels improve grey neutrality and reduce visible metamerism under different lighting |

### Alternative: Canon imagePROGRAF PRO-6100

| Parameter | Specification |
|-----------|---------------|
| **Printer** | Canon imagePROGRAF PRO-6100 (60" wide-format) |
| **Ink Set** | LUCIA PRO — 12-channel |
| **Use Case** | Larger format (up to 60"), or if Epson is unavailable at the proofing studio |

---

## 3. ICC Profile and Color Management

### Custom Profile Generation

| Step | Specification |
|------|---------------|
| **Instrument** | X-Rite i1Pro3 spectrophotometer |
| **Target** | i1Profiler default target (1500+ patches) |
| **Paper** | Print target on actual production paper (Hahnemuhle Photo Rag Baryta 315gsm) |
| **Drying Time** | Minimum 24 hours before measurement (outgassing affects readings) |
| **Software** | X-Rite i1Profiler |
| **Profile Type** | ICC v4 |
| **Rendering Intent** | Perceptual |
| **Black Point Compensation** | ON |
| **Gamut Mapping** | Perceptual — smooth compression of near-blacks is critical for Soot grey ramp |

### Why Custom Profile (Not Canned)

Canned profiles (manufacturer-provided) are averaged across production batches and do not account for:
- Individual printer head characteristics
- Paper batch variation
- Ink batch variation
- Ambient conditions at proofing studio

For an achromatic work where the entire tonal range lives between #000000 and #c8c8c8, profile accuracy in the shadow regions is the difference between smooth gradation and visible banding. A custom profile, measured on the actual printer/paper combination, is mandatory.

### Color Management Chain

```
EXR (linear, scene-referred)
    → ACES tonemapping (exhibition transfer function)
    → sRGB conversion (Photoshop working space)
    → Custom ICC profile (Perceptual, BPC ON)
    → Printer driver (no additional color management)
```

---

## 4. Resolution

### Print Resolution Matrix

| Print Size | Pixel Resolution | DPI | Source |
|------------|-----------------|-----|--------|
| **40" x 50"** (1016 x 1270mm) | 12000 x 15000 px | 300 | Primary hero print |
| **30" x 37.5"** (762 x 953mm) | 9000 x 11250 px | 300 | Standard edition print |
| **20" x 25"** (508 x 635mm) | 6000 x 7500 px | 300 | Collector/small edition |

### Resolution Notes

- 300 DPI is the target at final print size. This is the minimum for fine art archival printing where viewers approach to < 0.5m
- The print render pass generates at the hero resolution (12000 x 15000 px). Smaller sizes are derived by downsampling from the hero render, not by rendering at lower resolution
- Upscaling from the animation resolution (3840 x 4800 for 4:5 at 24fps) is NOT acceptable. The print render is a separate, dedicated pass at full resolution

---

## 5. Black Void Strategy

### The Paper Black Problem

The digital render produces a pure black void at #000000 (0.0 cd/m2 on OLED, ~0.001 cd/m2 on laser projector). Paper cannot achieve absolute black — the baryta surface reflects ambient light and the ink has a minimum reflectance. The paper's Dmax (~2.3 for Photo Rag Baryta) represents the deepest black achievable.

### Strategy: Embrace Paper Dmax

| Approach | Implementation |
|----------|---------------|
| **Do NOT clip black to absolute** | The print transfer function maps #000000 in the EXR to the paper's Dmax, not to a mathematical zero. Use Photoshop's "Simulate Paper Color" to preview this mapping |
| **Preserve shadow detail** | The lowest 5% of the density range (trace-level wisps) must remain visible on paper. If they disappear into the paper black, the print has failed — the void swallows the edges |
| **Border treatment** | 2" (50mm) paper-white border on all sides. The unprinted baryta base provides a reference white that defines the tonal range. Alternative: float-mount (print trimmed to image edge, mounted with 15mm standoff from backing board — shadow creates the "border") |

### Soft-Proofing Protocol (Photoshop)

1. Open 16-bit EXR in Photoshop (assign sRGB after ACES tonemapping)
2. View > Proof Setup > Custom:
   - Device: [Custom ICC Profile for Hahnemuhle Baryta on SC-P9570]
   - Rendering Intent: Perceptual
   - Black Point Compensation: ON
   - **Simulate Paper Color: ON** (this is the critical step — it shows how the paper's white point and Dmax affect the image)
   - **Simulate Black Ink: ON**
3. Evaluate:
   - Are trace-level wisps (density 0.0-0.1) still visible against the paper black?
   - Does the grey ramp show smooth gradation from void to peak (#c8c8c8)?
   - Is there visible banding in the shadow regions?
4. If trace wisps disappear: adjust the print curves to lift shadows slightly (add +2-5 points at the 3-5% range in Curves)
5. If banding is visible: increase the printer's pass count (from standard to "quality" mode) to improve ink laydown smoothness

---

## 6. Separate Print Render Pass

The print render is NOT a frame grab from the animation. It is a dedicated render pass with different parameters optimized for ink-on-paper.

### Print Render Parameters

| Parameter | Animation Render | Print Render | Rationale |
|-----------|-----------------|-------------|-----------|
| **Motion Blur** | ON (per-frame accumulation) | OFF | Print is a still; motion blur reduces sharpness |
| **Step Size** | 1x (standard ray-march) | 4x (4x samples per ray) | Higher sample count eliminates ray-march banding visible on paper at close viewing distance |
| **VDB Resolution** | 256-512 (per shot) | 1024 (frustum upres) | Maximum volumetric detail for close-range paper viewing |
| **Temporal AA** | ON (accumulated over frame window) | OFF (single-sample) | No temporal information in a still |
| **Noise** | Tuned for display (dark surround) | Tuned for paper ink limit | Paper's lower dynamic range means noise is more visible in shadow regions |
| **Histogram** | Targets display Dmax (~0.0 for OLED, ~0.005 for projector) | Targets paper Dmax (~2.3) | Print histogram must be re-mapped for the paper's reduced contrast range |
| **Output Format** | 16-bit EXR, linear | 16-bit EXR, linear | Same format; different render settings |
| **Resolution** | 3840 x 4800 (4K, 4:5) | 12000 x 15000 (300 DPI at 40" x 50") | Print requires 3x the linear resolution of the animation frame |

### Hero Frame Selection

| Hero Frame | Source Shot | Frame Number | Rationale |
|------------|-----------|--------------|-----------|
| **Hero 1: "The Monolith"** | Shot 01 | Frame 360 (apex of boom-up, breath hold) | Maximum vertical drama; plume as geological column |
| **Hero 2: "The God's Eye"** | Shot 04 | Frame 1230 (nadir hold) | Radial plume structure from above; the satellite's view; Steyerl's "politics of verticality" |

### Target Density for Print

- Peak density: 30-40% of maximum plume concentration
- At 80-100% density, the baryta paper's ink limit is reached and textural detail collapses into flat black
- At 30-40%, the plume's internal geological folding, turbulent structure, and granular soot detail are maximally visible
- The print should feel like looking into a dense but translucent volume, not at a dark shape

---

## 7. Print Production Workflow

### Step-by-Step

1. **Render**: Execute print render pass at 12000 x 15000 px, 4x step_size, no motion blur, 1024 VDB
2. **ACES Tonemap**: Apply ACES tonemapping (same curve as exhibition, adjusted for paper target)
3. **Export**: Save as 16-bit TIFF, sRGB (for Photoshop compatibility)
4. **Soft-Proof**: Open in Photoshop, apply custom ICC profile with Simulate Paper Color ON
5. **Adjust**: Curves adjustment for shadow lift if trace wisps disappear
6. **Proof Print**: 13x19" proof on same paper stock (Photo Rag Baryta)
7. **Evaluate Proof**: Check under exhibition lighting conditions (dim, controlled, similar to gallery)
8. **Final Print**: Full-size print on SC-P9570, Quality mode, Photo Black ink
9. **Dry**: 48-hour drying time in dust-free environment
10. **Inspect**: Check for banding, nozzle dropout, paper defects under raking light
11. **Sign and Number**: Pencil on verso, lower right: title, edition number, date, signature
12. **Document**: Photograph print under controlled lighting for archive record

---

## 8. Edition Management

### Edition Structure

| Category | Quantity | Notes |
|----------|----------|-------|
| **Edition prints** | 7 (numbered 1/7 through 7/7) | Each hero frame is a separate edition |
| **Artist's Proofs** | 2 (marked AP 1/2, AP 2/2) | Retained by artist |
| **Printer's Proof** | 1 (marked PP) | Retained by print studio |
| **Total impressions** | 10 per hero frame | |

### Certificate of Authenticity

Each print ships with a signed Certificate of Authenticity containing:

| Field | Content |
|-------|---------|
| **Title** | *Soot* — [Shot Name] (e.g., "The Monolith") |
| **Date** | 2026 |
| **Medium** | Archival pigment print on Hahnemuhle Photo Rag Baryta 315gsm |
| **Dimensions** | [Print size] (image), [Paper size] (sheet) |
| **Edition** | [Number] of 7, with 2 APs |
| **Printer** | Epson SC-P9570 / UltraChrome Pro12 |
| **Source Data** | NASA OCO-3 L2 Lite v11.1r, ECMWF CAMS Global CO2 Reanalysis |
| **Pipeline** | oco-viz [git commit hash] |
| **Render Settings** | 12000x15000 px, 4x step_size, 1024 VDB, ACES tonemap |
| **SHA-256** | [Hash of source 16-bit EXR file] |
| **Signature** | Artist signature (hand-signed, ink on paper) |
| **Date of Print** | [Exact print date] |

### SHA-256 Provenance

The SHA-256 hash of the source 16-bit EXR file (pre-Photoshop, post-ACES tonemap) is recorded on each certificate. This hash:

- Uniquely identifies the exact render output
- Can be verified against the archived EXR in the conservation package
- Establishes provenance chain from satellite data through render pipeline to physical print
- Is computed using `sha256sum [filename].exr` and recorded as a 64-character hexadecimal string

---

## 9. Framing and Presentation

### Option A: Border Print (Standard)

- 2" (50mm) unprinted paper border on all sides
- Frame: Aluminum, anodized black (e.g., Nielsen Profile 93 or equivalent)
- Glazing: Museum glass (TrueVue Museum Glass or equivalent, UV-filtering, anti-reflective)
- Mat: None (print floats within frame, held by archival corners)
- Backing: Acid-free foam core, sealed

### Option B: Float Mount (Exhibition)

- Print trimmed flush to image edge (no border)
- Mounted on Dibond (3mm aluminum composite) with 15mm standoff spacers
- No glazing (the print surface is exposed — baryta coating is durable)
- Shadow gap between Dibond edge and wall creates a floating effect
- Black-painted gallery wall behind creates visual continuity with the void

### Presentation Recommendation

Float mount is preferred for exhibition contexts. The absence of glass eliminates reflections that compromise the black void. The shadow gap makes the print appear to levitate on the wall — the void continues beyond the image edge. The baryta surface is sufficiently durable for gallery conditions (no touching, controlled humidity).

Border print with museum glass is preferred for collector/institutional contexts where long-term handling protection is prioritized over presentation purity.

---

## 10. Print Archival and Storage

### Storage Conditions

| Parameter | Specification |
|-----------|---------------|
| **Temperature** | 18-22 C (65-72 F) |
| **Relative Humidity** | 35-45% RH |
| **Light** | Dark storage (no light exposure during storage) |
| **Interleaving** | Acid-free tissue between prints |
| **Flat Storage** | Acid-free museum storage box, horizontal, face-up |
| **Do NOT roll** | Baryta coating can crack on tight rolls |

### Display Conditions

| Parameter | Specification |
|-----------|---------------|
| **Illumination** | < 50 lux at print surface (museum standard for works on paper) |
| **UV** | < 75 microwatts per lumen (museum glass or UV-filtered lighting) |
| **Display Duration** | Maximum 6 months continuous, then 12-month rest (Wilhelm Research recommendation for pigment prints) |
