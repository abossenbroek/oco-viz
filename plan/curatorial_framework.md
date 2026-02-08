# Curatorial Framework: "Soot"

**Version**: 1.0
**Status**: Production
**Work Title**: *Soot* (2026)
**Medium**: Real-time volumetric simulation, archival pigment prints, multi-channel immersive installation
**Source Data**: NASA OCO-2/OCO-3 satellite observations, ECMWF CAMS global CO2 reanalysis

---

## 1. Artist Statement

Sasol Secunda's coal-to-liquids complex in Mpumalanga, South Africa, emits approximately 57 megatons of carbon dioxide every year — one of the largest single-point sources on Earth. The gas is invisible. It disperses unmarked into the atmosphere, leaving no trace of its presence, no stain, no residue.

*Soot* makes the invisible visible.

Using volumetric data from NASA's OCO-3 satellite and ECMWF atmospheric reanalysis, the work reconstructs the three-dimensional structure of Secunda's CO2 plume and renders it as what it functionally is: industrial soot. Heavy, choking, achromatic particulate matter — charcoal on black void. The visualization strips away the comforting abstractions of scientific color mapping — no rainbow gradients, no reassuring blues — and presents carbon dioxide as material with weight, texture, and presence.

The plume is rendered using the "Soot" visual language: strictly achromatic, internally illuminated, with no external light source. Light is suffocated by density. The volume emerges from pure black void with no ground plane, no horizon, no environmental context. What remains is the emission itself — 57 megatons per year, made tangible, made confrontational, made undeniable.

*Soot* is not a scientific visualization. It is a material encounter with a hyperobject.

*(238 words)*

---

## 2. Wall Text

### Primary Wall Text (Gallery Label)

**Soot** (2026)
Real-time volumetric simulation, multi-channel immersive installation
Duration: 90 seconds (continuous loop)

NASA's OCO-3 satellite, mounted on the International Space Station, measures atmospheric carbon dioxide with sub-kilometer precision. Sasol Secunda, a coal-to-liquids refinery in South Africa's Mpumalanga province, appears in these measurements as one of the most concentrated point sources of CO2 on the planet: 57 megatons per year, roughly equivalent to the total annual emissions of Portugal.

*Soot* transforms this satellite data into a three-dimensional volumetric reconstruction of Secunda's carbon plume. The work renders CO2 not as the invisible, odorless gas of textbook description, but as dense industrial particulate — heavy, granular, and oppressive. The strictly achromatic palette (pure black to dirty grey, never white) rejects the rainbow heatmaps of conventional scientific visualization in favor of a material language borrowed from charcoal drawing and industrial residue.

The six-shot sequence — "Descent of Carbon" — moves from monumental scale through internal immersion to aerial surveillance and dissolution. The camera's motion language is glacial: cubic easing, maximum angular velocity of 0.05 degrees per second, deliberate breath-holds between shots. The plume does not end; it disperses below the threshold of visibility. The loop restarts. 57 megatons. Every year. Without end.

### Extended Wall Text (Catalog / Press)

Tim Morton defines the hyperobject as an entity so massively distributed in time and space that it transcends human comprehension — climate change, the biosphere, the sum total of all nuclear materials. Carbon dioxide is the paradigmatic hyperobject: it is everywhere, in everything, of geological duration, and fundamentally invisible to unaided human perception.

*Soot* is an attempt to make one hyperobject local and tangible. By anchoring the visualization to a single source — Sasol Secunda, coordinates 26.5 S, 29.2 E — and rendering its emissions as material particulate, the work collapses the hyperobject into a confrontable scale. The plume has edges. It has weight. It moves with the wind. It can be seen.

The work sits within a lineage of artists using 3D rendering and simulation to bridge the virtual and the physical — a practice recognized by institutions from MoMA to Castello di Rivoli. Where Ian Cheng's live simulations generate autonomous virtual ecosystems and Ed Atkins' hyper-realistic CGI avatars expose the "cadaverousness" of digital representation, *Soot* applies the same tools to a specifically ecological crisis. The rendering is not a representation of CO2; it is, following Hito Steyerl's formulation, a *rendering* in both senses — a computational process and a political act. In Steyerl's framework, "rendering replaces editing" as the primary artistic operation; *Soot* renders CO2 into visibility, and in doing so, renders visible the industrial systems that produce it.

The visual language draws from Lev Manovich's concept of transcoding — the mutual influence between computational logic and cultural practice. Scientific data (OCO-3 XCO2 column averages, CAMS reanalysis fields) is transcoded through VTK volumetric rendering into a material that speaks the language of charcoal, soot, and industrial residue. The transfer function — the mathematical mapping from data value to visual property — becomes the site of artistic decision. Where scientific visualization uses color to maximize information density, *Soot* uses achromatic density to maximize emotional and material impact.

Gilles Deleuze's crystal-image, from *Cinema 2: The Time-Image*, describes a state where the actual and the virtual become indiscernible. In *Soot*, the satellite measurement (actual) and the volumetric reconstruction (virtual) coalesce: the plume is simultaneously real data and artistic construction, a scientific object and a material encounter. The viewer cannot separate the measured from the rendered. This indiscernibility is not a failure of clarity but the work's central proposition — that CO2 occupies exactly this liminal space, real and invisible, measured and unfelt, until someone renders it into presence.

---

## 3. Data Pedigree Document

*For scientifically literate audiences, data transparency panels, and academic contexts.*

### Source Data Chain

```
OCO-3 L2 Lite (v11.1r)     NASA Earthdata
    Column-integrated XCO2       Single value per footprint (~1.3 km x 2.3 km)
    SAM/target mode observations over Sasol Secunda
    Independent validation (not assimilated into CAMS)
        |
OCO-2 L2 Lite (v11.1r)     NASA Earthdata
    Column-integrated XCO2       Sun-synchronous, predictable repeats
    Fused with OCO-3 for temporal coverage
        |
        v
CAMS Global CO2 Reanalysis  Copernicus CDS / ECMWF
    3D atmospheric CO2 fields    9 km horizontal, 137 model levels
    Provides vertical profile structure
    Does NOT assimilate OCO-2/OCO-3 (uses GOSAT)
        |
ERA5 Reanalysis Winds       Copernicus CDS / ECMWF
    U/V/W wind components        31 km, 137 levels
    Meteorological forcing for plume advection
        |
        v
    [oco-viz Pipeline]
    Layered architecture:
        CAMS background (large-scale 3D field)
      + Gaussian plume model (Secunda source term)
      + Multi-octave turbulent noise (geological folding)
        |
        v
    VTK Volumetric Grid         xr.Dataset -> VTI/VDB
    Transfer function:          Soot achromatic (see visual_language.yaml)
    Rendering:                  VTK GPU volume rendering
    Post-processing:            ACES tonemapping (exhibition tier)
```

### Key Methodological Notes

1. **OCO-3 measures column-integrated XCO2** — a single value per footprint representing the total CO2 in the atmospheric column. It cannot distinguish altitude. The 3D vertical structure comes entirely from CAMS reanalysis.

2. **CAMS does not assimilate OCO-2/OCO-3** — it uses GOSAT. This means OCO observations remain independent and serve as validation, not input, to the 3D reconstruction.

3. **The Gaussian plume component** is parametric, not a direct transport simulation. It provides physically plausible plume structure (dispersion, advection) but is not a HYSPLIT trajectory calculation. The visualization is physically informed, not physically exact.

4. **The "Soot" rendering is an artistic interpretation.** CO2 is colorless and invisible. The achromatic material language is a deliberate artistic choice to represent concentration as industrial particulate. The transfer function mapping (PPM to density/opacity) is documented in `plan/visual_language.yaml`.

### Validation

Modeled column XCO2 is compared against OCO-2/OCO-3 observed enhancements. Target agreement: within 20% of observed plume enhancement above background (study tier). This validates bulk plume behavior, not fine-scale structure.

---

## 4. Press Materials

### Project Description (300 words)

*Soot* is a volumetric data artwork that renders the invisible CO2 emissions of Sasol Secunda — one of the largest single-point carbon sources on Earth — as heavy, choking industrial particulate against a black void. Using satellite observations from NASA's OCO-3 and atmospheric reanalysis from ECMWF, the work reconstructs the three-dimensional structure of Secunda's 57-megaton annual CO2 plume and presents it as material with weight, texture, and oppressive presence.

The installation comprises a 90-second continuous loop — "Descent of Carbon" — presented as a multi-channel immersive projection or high-density LED display in a light-controlled gallery environment. Six shots move from the monumental scale of the full plume through internal immersion, aerial surveillance, dissolution, and fade to black. The camera's motion language is glacial: cubic easing, sub-degree angular velocities, deliberate breath-holds between shots. The loop restarts without interruption. The emissions never stop.

The work's visual language — "Soot" — is strictly achromatic: pure black background, dirty grey-scale palette (never clean white), internal smoldering illumination with no external light sources. This is a deliberate rejection of the rainbow heatmaps of scientific visualization. The work borrows its material language from charcoal drawing and industrial residue, insisting that CO2 be encountered as material substance, not as data abstraction.

*Soot* is produced using an open-source Python pipeline (oco-viz) that processes satellite data through VTK volumetric rendering and OpenVDB export. The work can be presented as immersive projection, LED installation, or archival pigment print. Hero frames are printed on Hahnemuhle Photo Rag Baryta 315gsm at 40 x 50 inches, delivering a peak black density (Dmax ~2.3) that approaches the pure void of the digital render.

### Key Technical Specifications

| Parameter | Value |
|-----------|-------|
| Source Data | NASA OCO-2/OCO-3, ECMWF CAMS, ERA5 |
| Pipeline | oco-viz (Python, open-source) |
| Rendering | VTK GPU volume rendering |
| Aspect Ratio | 4:5 (primary), 1:1, 9:16, 32:9 (derived) |
| Duration | 90 seconds, continuous loop |
| Frame Rate | 24 fps |
| Output Formats | 16-bit EXR (master), ProRes 4444 (exhibition), H.265 (archival) |
| Print | Hahnemuhle Photo Rag Baryta 315gsm, Epson UltraChrome Pro12 |

### Key Images

1. **Shot 01 "The Monolith"** — vertical plume column, boom-up apex frame
2. **Shot 04 "The God's Eye"** — nadir view, radial plume structure
3. **Installation view** — gallery context with viewer silhouette for scale

### Artist Bio Template

[Artist Name] works at the intersection of satellite remote sensing and volumetric visualization, using computational tools to make planetary-scale environmental processes tangible. Their practice draws on OCO-2/OCO-3 atmospheric carbon dioxide measurements and ECMWF atmospheric reanalysis to reconstruct three-dimensional representations of industrial emissions. The work is situated within a lineage of post-internet artistic practice that treats rendering as both a computational process and a political act. [Artist Name] holds [credentials] and has [exhibitions/recognition].

---

## 5. The Achromatic Manifesto

### Against the Rainbow

Scientific visualization has a color problem.

The rainbow colormap — jet, turbo, viridis and their descendants — is the default language of quantitative imaging. It maps low values to blue, high values to red, and distributes the visible spectrum across the data range. It is designed to maximize information density, to make every datum distinguishable from its neighbors, to serve the eye of the analyst.

It is also a lie.

The rainbow colormap aestheticizes data. It makes pollution beautiful. It transforms a choking industrial plume into a decorative gradient — a sunset of nitrogen dioxide, a watercolor of particulate matter. The viewer looks at a heatmap of CO2 concentration and sees a pleasing composition of blues and oranges. The affective response is aesthetic appreciation, not confrontation. The data is legible. The crisis is invisible.

*Soot* refuses the rainbow.

### Principles

**1. Achromatic fidelity.** All channels equal: R = G = B at every density level. There is no hue, no saturation, no chromatic information. The only variables are luminance and opacity. This is not a limitation but a discipline — the discipline of charcoal, of graphite, of soot itself.

**2. Dirty white, never clean.** Peak density renders as #c8c8c8 — a contaminated near-white that never reaches purity. Clean white (#ffffff) implies resolution, clarity, innocence. Dirty white implies contamination, residue, the impossibility of clean air. The brightest point in the visualization is already compromised.

**3. Pure black void.** The background is #000000 — no gradient, no sky, no ground plane, no atmospheric haze (exhibition tier). The plume exists in a perceptual vacuum. There is no context to domesticate it, no landscape to naturalize it, no horizon line to orient the viewer. The void forces confrontation: there is only the emission and the darkness.

**4. Opacity never reaches 1.0.** The volume is always partially transparent. The viewer can always see into and through the plume. This is not a rendering convenience but an epistemological statement: CO2 is not a solid wall. It is a density field — a gradient of contamination that has no hard boundary. Opacity caps at 0.45 (exhibition tier), ensuring that the plume's internal geological structure remains visible even at peak concentration.

**5. Internal illumination only.** Light does not fall on the plume from outside. The soot is its own dim, oppressive light source — smoldering from within, suffocated by its own density. Deep interiors glow brighter than surfaces. This inverts the convention of external lighting in scientific visualization, where volumes are illuminated like objects on a table. In *Soot*, the emission illuminates itself. Nothing else does.

### Precedent

The achromatic discipline draws from:

- **William Kentridge**: charcoal on black paper, the weight and erasure of industrial residue
- **Gerhard Richter**: grey paintings (*Grau*, 1970s) — the refusal of chromatic seduction as an ethical position
- **Ad Reinhardt**: black paintings — the progressive elimination of compositional elements toward pure presence
- **Ansel Adams**: Zone System — the mastery of tonal range within a monochrome discipline, where the print is evaluated by the richness of its blacks and the subtlety of its greys, not by color

### Practical Consequence

Every rendering decision in *Soot* — transfer function design, lighting model selection, post-processing chain — is evaluated against this manifesto. If a parameter introduces color, visible hue shift, or chromatic artifact, it is rejected. If a parameter pushes peak white toward #ffffff, it is rejected. If a background shows grey above #000000 in exhibition tier, it is a bug.

The achromatic constraint is not aesthetic preference. It is the work's ethical foundation. The rainbow makes pollution beautiful. Soot makes it heavy.

---

## 6. Critical Positioning

### Within Post-Internet Discourse

*Soot* operates within what Hito Steyerl identifies as the shift from editing to rendering as the primary artistic act. The work does not edit satellite data — it renders it. The computational process of volumetric rendering (ray marching through a density field, evaluating a transfer function at each sample point, accumulating color and opacity along each ray) is both the technical method and the conceptual operation. The work renders CO2 into visibility.

This positions *Soot* at the intersection of several active threads in contemporary discourse:

**Steyerl's "politics of verticality"**: Shot 04 ("The God's Eye") directly engages Steyerl's analysis of the replacement of the stable horizon with the aerial gaze of surveillance and measurement. The nadir camera position is the satellite's view — the same view that produces the OCO-3 measurement. The shift from immersive side-view (Shots 01-03) to overhead surveillance (Shot 04) enacts the violence of abstraction: the choking plume becomes a data point, a column-average XCO2 value.

**Morton's hyperobjects**: CO2 is the canonical hyperobject — massively distributed, temporally vast, imperceptible to human senses. *Soot* proposes that rendering is a valid strategy for encountering hyperobjects: not representing them (which implies mastery) but rendering them into a material presence that can be confronted.

**Manovich's transcoding**: The data pathway from satellite sensor to gallery wall is a transcoding operation. OCO-3 photon counts become XCO2 column averages become xarray datasets become VTK volume grids become pixel values become photons from a projector lamp become retinal stimulation. At each stage, the data is re-encoded in a new medium. *Soot* makes this transcoding chain visible and treats each stage as a site of artistic decision.

**Deleuze's crystal-image**: The indiscernibility of the actual (satellite measurement) and the virtual (volumetric reconstruction) is the work's central formal operation. The viewer cannot determine where data ends and interpretation begins. This is not a failure of transparency but the proposition that CO2 itself occupies this liminal space — real and invisible, measured and unfelt.

### Distinction from Scientific Visualization

*Soot* is not a scientific visualization and does not claim to be. The distinction is methodological and ethical:

| Dimension | Scientific Visualization | *Soot* |
|-----------|------------------------|--------|
| **Purpose** | Information communication | Material encounter |
| **Color** | Maximizes discriminability | Maximizes material presence |
| **Accuracy** | Quantitative precision | Physical plausibility |
| **Viewer** | Analyst | Witness |
| **Affect** | Comprehension | Confrontation |
| **Medium** | Screen, paper | Immersive installation, archival print |

The work uses real data and physically plausible reconstruction methods. It is not fabricated or invented. But its purpose is not to communicate quantitative information — it is to make an invisible industrial reality tangible and confrontational.
