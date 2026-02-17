---
name: lighting-setups
user-invocable: false
type: instruction
primary_owner: dp
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# Lighting Setups — Motivated Volumetric Rig Templates

Every light has a motivation. The rig serves the emotional read, not the technical
requirement. A light without a physical source is a lie told to the viewer, and the
viewer always detects the lie — even if they cannot articulate it. These templates encode
lighting philosophies as concrete VTK configurations, each traceable to a cinematic
reference and a physical justification.

> "I never use a light I can't justify." — Roger Deakins

---

## Principle

Lighting for volumetric CO2 plumes follows the same discipline as lighting for live
action: every photon must have a plausible origin, every shadow must serve the story, and
ambient fill is the enemy of atmosphere. The templates below are not presets to be
applied blindly — they are starting points that encode a lighting philosophy. The DP must
adapt each template to the specific density field, adjusting intensity and position while
preserving the motivational logic.

Ambient intensity is always 0.0 for Soot-tier work. There is no justification for
omnidirectional illumination inside a particulate cloud. Light enters from sources; it
does not materialize from the void.

---

## Procedure

### Step 1 — Read the Density Field

Before placing any light, analyze the VDB density distribution. Identify:
- Core zones (high density, absorption-dominated)
- Halo zones (moderate density, scattering-dominated)
- Void boundaries (density falls to zero)

The density field dictates where light can penetrate, scatter, and accumulate. The
lighting rig amplifies what the density already suggests.

### Step 2 — Select Rig Template

Choose a template based on the emotional intent of the shot:

| Emotional Intent | Template | Key Characteristic |
|------------------|----------|-------------------|
| Confrontation, exposure | Chiaroscuro | Single key, no fill, maximum void |
| Emergence, revelation | Industrial Furnace | Warm underglow, cool rim scatter |
| Environmental scale | Atmospheric Gradient | Directional key following wind shear |
| Dread, absence | Void Study | Edge light only, maximum darkness |

### Step 3 — Configure VTK Lights

Build the rig in VTK using the template parameters. Each light must be annotated with
its motivation.

### Step 4 — Validate with Scout Render

Render at 128-cubed scout resolution. Evaluate the emotional read before optimizing the
technical quality. If the scout does not communicate the intended emotion, the rig is
wrong — not the resolution.

---

## Rig Templates

### Chiaroscuro

**Reference:** Caravaggio, The Calling of Saint Matthew. A single shaft of light
entering from the upper right, everything else in profound darkness. In cinema: the
Baseline Test interrogation in BR2049 — K's face floating in absolute black.

**Emotional intent:** High-contrast revelation. The plume is either illuminated or it
does not exist. There is no gradient between visible and invisible — only the knife-edge
of the key light's reach.

```yaml
rig_name: chiaroscuro
lights:
  - name: key_single
    type: distant
    color_temp: 3400           # tungsten-warm
    intensity: 0.65
    position: [2.0, 3.0, 1.5] # upper right, slightly forward
    rotation: [-35, -25, 0]    # angled down and left into the volume
    falloff: quadratic
    shadow: true
    motivation: "Single practical source — interrogation lamp, furnace opening, or
                 narrow window. The source is never seen but its direction is
                 unambiguous."
ambient_config:
  ambient_intensity: 0.0      # absolute zero — no unmotivated light
  fog_density: 0.0            # no atmospheric haze in void
render_config:
  key_fill_ratio: 16.0        # effectively infinite — no fill exists
  shadow_density: 0.98        # near-black shadows, not crushed
```

**VTK configuration example:**

```python
key = vtk.vtkLight()
key.SetLightTypeToSceneLight()
key.SetPosition(2.0, 3.0, 1.5)
key.SetFocalPoint(0.0, 0.0, 0.0)
key.SetColor(1.0, 0.88, 0.72)    # 3400K approximation
key.SetIntensity(0.65)
key.SetConeAngle(180)             # distant light
renderer.AddLight(key)
renderer.SetAmbient(0.0, 0.0, 0.0)
```

### Industrial Furnace

**Reference:** Wallace Corporation interiors, BR2049 — amber light bleeding upward
through industrial haze, cool atmospheric scatter from above creating a faint rim on
rising particulate. The furnace scene in Alien: Covenant.

**Emotional intent:** Volume emergence. The plume is born from heat below and rises into
cold air above. The warm-cool contrast tells the story of combustion meeting atmosphere.

```yaml
rig_name: industrial_furnace
lights:
  - name: key_furnace
    type: rect
    color_temp: 3200           # warm combustion source
    intensity: 0.75
    position: [0.0, -1.0, 0.0]  # below the volume
    rotation: [90, 0, 0]        # pointing straight up
    falloff: quadratic
    shadow: true
    motivation: "Combustion source at plume base — furnace mouth, smokestack
                 opening, or ground-level burn. Warm light rising into density."

  - name: rim_atmospheric
    type: dome
    color_temp: 5600           # cool daylight scatter
    intensity: 0.12
    position: [0.0, 5.0, 0.0] # above the volume
    falloff: quadratic
    shadow: false
    motivation: "High-altitude atmospheric Rayleigh scatter — cool blue photons
                 scattered by upper atmosphere reaching the plume top."
ambient_config:
  ambient_intensity: 0.0
  fog_density: 0.02           # faint atmospheric haze
  fog_color: [0.05, 0.05, 0.06]  # cool-shifted near-black
render_config:
  key_fill_ratio: 6.0
  shadow_density: 0.92
```

**VTK configuration example:**

```python
furnace = vtk.vtkLight()
furnace.SetLightTypeToSceneLight()
furnace.SetPosition(0.0, -1.0, 0.0)
furnace.SetFocalPoint(0.0, 1.0, 0.0)
furnace.SetColor(1.0, 0.85, 0.65)   # 3200K approximation
furnace.SetIntensity(0.75)
renderer.AddLight(furnace)

rim = vtk.vtkLight()
rim.SetLightTypeToSceneLight()
rim.SetPosition(0.0, 5.0, 0.0)
rim.SetFocalPoint(0.0, 0.0, 0.0)
rim.SetColor(0.82, 0.87, 1.0)       # 5600K approximation
rim.SetIntensity(0.12)
renderer.AddLight(rim)
```

### Atmospheric Gradient

**Reference:** The sandstorm approach in Dune (2021) — light direction follows the
environmental gradient, creating a sense of massive scale and physical force. The Dust
Bowl sequences in Interstellar.

**Emotional intent:** Environmental context. The light source is the environment itself
— sun at a specific elevation filtered through atmospheric particulate. The plume is
embedded in a world, not floating in a void.

```yaml
rig_name: atmospheric_gradient
lights:
  - name: key_directional
    type: distant
    color_temp: 4200           # filtered sunlight through particulate
    intensity: 0.55
    position: [3.0, 2.0, -1.0]  # following wind shear direction
    rotation: [-20, -40, 0]     # low elevation, matching atmospheric gradient
    falloff: quadratic
    shadow: true
    motivation: "Direct solar illumination filtered through atmospheric
                 particulate layer. Direction follows prevailing wind shear
                 to reinforce environmental narrative."

  - name: scatter_fill
    type: dome
    color_temp: 6500           # Rayleigh sky scatter
    intensity: 0.08
    position: [0.0, 4.0, 0.0]
    falloff: quadratic
    shadow: false
    motivation: "Hemispheric sky scatter — blue-shifted atmospheric fill
                 from all upper directions. Weak but physically motivated."
ambient_config:
  ambient_intensity: 0.0
  fog_density: 0.05           # visible atmospheric haze
  fog_color: [0.08, 0.07, 0.06]  # warm-shifted dust haze
render_config:
  key_fill_ratio: 7.0
  shadow_density: 0.88
```

### Void Study

**Reference:** The Sea Wall scene in BR2049 — K standing at the edge of nothingness,
defined only by the faintest edge of scattered light. Under the Skin (2013) — forms
emerging from absolute darkness with no visible light source.

**Emotional intent:** Dread, absence, confrontation with void. The plume barely exists
visually. It is defined not by illumination but by the faintest scattering at its edges.
The viewer must lean in to perceive the form.

```yaml
rig_name: void_study
lights:
  - name: edge_only
    type: distant
    color_temp: 4800           # neutral — no emotional warming
    intensity: 0.25            # extremely low — barely perceptible
    position: [-3.0, 0.5, 2.0]  # side/behind the volume
    rotation: [0, 60, 0]        # grazing angle for edge definition
    falloff: quadratic
    shadow: true
    motivation: "Distant environmental light at extreme grazing angle.
                 Only the thinnest edges of the density field catch enough
                 photons to register. Core remains in total darkness."
ambient_config:
  ambient_intensity: 0.0
  fog_density: 0.0            # no atmospheric scatter — pure void
render_config:
  key_fill_ratio: 16.0        # no fill exists
  shadow_density: 0.99        # shadows indistinguishable from background
```

---

## Parameters

### Global Lighting Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `ambient_intensity` | float | 0.0 | 0.0 - 0.0 | Always zero for Soot tier |
| `key_fill_ratio` | float | 8.0 | 4.0 - 16.0 | Ratio of key to fill intensity |
| `shadow_density` | float | 0.92 | 0.85 - 0.99 | Shadow opacity (1.0 = pure black) |
| `background_color` | hex | #000000 | -- | Background must be pure black |

### Per-Light Parameters

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `color_temp` | int | 2700 - 6500 | Color temperature in Kelvin |
| `intensity` | float | 0.0 - 1.0 | Normalized light intensity |
| `position` | [float, float, float] | -- | World-space position in meters |
| `rotation` | [float, float, float] | -- | Euler angles in degrees |
| `falloff` | string | quadratic | Always quadratic or steeper |
| `shadow` | bool | true | Whether light casts shadows |
| `motivation` | string | required | Physical source justification |

### Fog / Atmosphere Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `fog_density` | float | 0.0 | 0.0 - 0.1 | Atmospheric fog density |
| `fog_color` | [float, float, float] | [0, 0, 0] | -- | Fog color in linear RGB |

---

## Anti-Patterns

### 1. The Three-Point Setup

**Symptom:** Key, fill, and rim placed at textbook broadcast angles — 45 degrees key,
opposite-side fill, backlight for separation. The volume looks like a product shot, not a
narrative frame.

**Cause:** Defaulting to portrait/product photography conventions that were designed for
facial key-to-fill ratios, not volumetric atmosphere.

**Fix:** Start with a single key. If the single key communicates the emotion, stop. Add
lights only when the single-key image is emotionally correct but physically incomplete
(e.g., atmospheric scatter that should exist based on the environment).

### 2. The Ambient Fill

**Symptom:** Shadows appear gray. The void between plume structures reads as a lighter
gray rather than pure black. Depth collapses. The volume looks flat.

**Cause:** Ambient intensity set above 0.0 to "help the viewer see the shape." This
destroys the void that gives volumetric rendering its power.

**Fix:** Set ambient to exactly 0.0. Let the void be void. If the viewer cannot perceive
the plume structure with zero ambient, the density field or transfer function needs work,
not the lighting.

### 3. The Unmotivated Rim

**Symptom:** A bright rim light outlines the volume edge, providing clean separation from
the background. But there is no physical source for this light — it exists purely for
visual readability.

**Cause:** Adding lights to solve compositional problems rather than narrative problems.
The rim light is a crutch that prevents the DP from discovering the correct density
falloff or camera angle.

**Fix:** Remove the rim. If edge definition is lost, adjust the transfer function to
create a more gradual density falloff at the plume boundary. If atmospheric scatter
exists in the physical environment, add it as a properly motivated dome light at
physically correct intensity (0.05-0.12, never 0.5+).

### 4. The Color Bath

**Symptom:** The entire volume is washed in a single strong color — deep blue, vivid
orange — creating a monochrome emotional effect that overwhelms the material response.

**Cause:** Using color temperature as an emotion shorthand instead of a physical
specification. A 2800K light from a furnace is warm because furnaces emit warm light,
not because the DP wanted warmth.

**Fix:** Every color temperature must map to a physical source (see motivation field).
If the source is sunlight, use 4200-5600K. If the source is incandescent, use 2700-3200K.
The emotion emerges from the physical truth, not from a color choice.

### 5. The Overlit Volume

**Symptom:** The plume is uniformly well-lit from all angles. Internal structure is
visible everywhere. There is no mystery, no hidden depth, no negative space within the
volume.

**Cause:** Optimizing for maximum information display rather than emotional storytelling.
The DP treated the volume as data to be revealed rather than a character to be lit.

**Fix:** Reduce total light count to one. Ask: where is the single most important zone
of this plume? Light that zone. Let the rest fall into shadow. Structure that must be
discovered by the viewer is more powerful than structure served on a plate.

---

## Validation Checklist

- [ ] Every light has a `motivation` field with a physical source description
- [ ] Ambient intensity is exactly 0.0 for Soot tier
- [ ] Background color is `#000000` (pure black)
- [ ] Key-to-fill ratio is 4:1 or higher
- [ ] No light uses constant or linear falloff (quadratic minimum)
- [ ] Color temperatures are within 2700K-6500K range
- [ ] Color temperature matches the stated physical motivation source
- [ ] Scout render (128-cubed) evaluated before proceeding to preview tier
- [ ] Emotional intent of the shot stated before rig selection
- [ ] Single-key render evaluated before adding any secondary lights
- [ ] Shadow regions measure below #050505 in rendered output
- [ ] VTK light configuration matches the template specification
- [ ] Rig conforms to `lighting_rig_delivery` schema from output-schemas
