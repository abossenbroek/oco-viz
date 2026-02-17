---
name: deakins-method
user-invocable: false
type: methodology
primary_owner: dp
progressive_disclosure:
  L1: lines 1-30
  L2: lines 31-80
  L3: lines 81-end
---

# The Deakins Method — Motivated Volumetric Lighting

Roger Deakins does not light a scene. He discovers the light that already exists in it,
then refines it until every shadow tells the story. For volumetric CO2 plumes the same
discipline applies: the density field IS the lighting design. Every photon must have a
plausible physical origin — a furnace mouth, a scattering sky, an industrial lamp
casting through particulate haze. If you cannot point to the source, the light does not
belong.

> "I don't light films. I try to find the light." — Roger Deakins

---

## Principle

Light must feel alive, organic, and motivated by a plausible physical source. The data
contains the lighting — discover it, do not add it. Sharp geometric light patterns,
pools of illumination, and deep pure blacks are the vocabulary. Fill light is the enemy
of atmosphere; shadow is where the story breathes.

In Blade Runner 2049 Deakins used massive practical rigs — 30-foot LED panels, sodium
vapor banks, single-source setups — to create lighting that the camera could discover
rather than construct. Our VTK volumetric pipeline follows the same ethos: the VDB
density distribution suggests where light would naturally accumulate, scatter, and
attenuate. The DP agent's job is to read that suggestion and amplify it with restraint.

---

## Procedure

### Step 1 — Analyze VDB Density Distribution

Load the density field and extract statistical profile: min, max, mean, standard
deviation, gradient magnitude histogram. Identify where mass concentrates (core),
where it thins (halo), and where it vanishes (void boundary). These three zones define
the lighting topology.

```
core:  density > mean + 1.5 * std   → absorption-dominated, deep shadow
halo:  mean - 0.5 * std < density < mean + 1.5 * std  → scattering-dominated, visible light transport
void:  density < mean - 0.5 * std   → transparency, background shows through
```

### Step 2 — Identify Natural Light Motivation

For each planned light, answer: "Where does this light come from in the physical
scene?" Valid motivations for CO2 plume visualization:

| Motivation | Physical Source | Typical Direction |
|------------|----------------|-------------------|
| Industrial furnace | Combustion at emission source | From below / behind plume base |
| Atmospheric scatter | Rayleigh/Mie from sky dome | From above, cool-biased |
| Ground reflection | Albedo bounce from terrain | From below, warm-shifted |
| Sun / key | Direct solar illumination | Elevation 15-45 degrees |
| Self-illumination | Hot gas thermal emission | Embedded in density core |

### Step 3 — Create Practical-Style Light Rig

Build the VTK light setup as if placing physical fixtures on set. Each light gets a
motivation tag, color temperature, falloff profile, and shadow behavior.

| Parameter | Range | Notes |
|-----------|-------|-------|
| Key-to-fill ratio | 4:1 minimum, 8:1 preferred | Never use fill for Soot tier |
| Color temperature | 2700K - 5600K | Match motivation source |
| Falloff | Inverse-square or steeper | Never constant / linear |
| Shadow density | 0.85 - 0.98 | Deep but not crushed |
| Ambient contribution | 0.0 - 0.02 | Near-zero; motivated only |

### Step 4 — Test in Scout Tier (128 cubed)

Render a scout-resolution pass. Evaluate:
- Does the key light reveal plume structure without flattening it?
- Are shadows deep enough to feel like void, not just darker plume?
- Does the halo zone glow with scattered light, suggesting atmosphere?
- Is the background pure black (#000000) or near-black where no plume exists?

### Step 5 — Refine with Motivated Adjustments Only

Adjust only what the scout revealed as deficient. Every adjustment must reference a
motivation. Log each change:

```
ADJUST: key intensity 0.8 → 0.65  MOTIVATION: furnace glow was overpowering core detail
ADJUST: rim temp 4200K → 4800K    MOTIVATION: atmospheric scatter should read cooler at altitude
```

---

## Parameters

### Primary Lighting Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `key_fill_ratio` | float | 6.0 | 4.0 - 16.0 | Ratio of key to fill intensity |
| `key_color_temp` | int | 3200 | 2700 - 5600 | Key light color temperature in Kelvin |
| `key_intensity` | float | 0.7 | 0.1 - 1.0 | Normalized key light intensity |
| `fill_enabled` | bool | false | — | Whether fill light is active (always false for Soot) |
| `fill_color_temp` | int | 4800 | 3800 - 6500 | Fill light color temperature in Kelvin |
| `fill_intensity` | float | 0.12 | 0.0 - 0.25 | Normalized fill intensity |
| `ambient_intensity` | float | 0.01 | 0.0 - 0.02 | Global ambient contribution |
| `shadow_density` | float | 0.92 | 0.85 - 0.98 | Shadow opacity (1.0 = pure black) |
| `background_color` | hex | #000000 | — | Background must be pure black |

### Falloff and Attenuation

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `falloff_exponent` | float | 2.0 | 1.5 - 3.0 | Light falloff power (2.0 = inverse square) |
| `attenuation_density_mult` | float | 1.0 | 0.5 - 2.0 | Volume density multiplier for light absorption |
| `scatter_anisotropy` | float | 0.3 | -0.5 - 0.8 | Henyey-Greenstein phase function g parameter |
| `scatter_albedo` | float | 0.6 | 0.1 - 0.9 | Single-scatter albedo of volume |

---

## Presets

### Industrial Furnace

Warm key from below the plume base, simulating combustion source illumination. Deep
shadows above, hot glow in the density core. Evokes the Wallace Corporation interiors
from BR2049 — amber light bleeding through industrial haze.

```yaml
key_color_temp: 2800
key_intensity: 0.75
key_elevation: -15  # below horizontal
key_fill_ratio: 8.0
fill_enabled: false
ambient_intensity: 0.005
shadow_density: 0.95
scatter_anisotropy: 0.4  # forward-biased from below
```

### Atmospheric Scatter

Cool rim light from the upper edge of the plume, simulating high-altitude Rayleigh
scatter. The plume reads as a dark mass against faintly illuminated haze. Evokes the
Joi hologram rain sequence — cool light defining edges against deep void.

```yaml
key_color_temp: 5200
key_intensity: 0.5
key_elevation: 60  # high rim
key_fill_ratio: 12.0
fill_enabled: false
ambient_intensity: 0.01
shadow_density: 0.90
scatter_anisotropy: -0.2  # backscatter emphasis
```

### Chiaroscuro

Single motivated key with no fill and no ambient. Maximum contrast. The plume either
catches the light or vanishes into the void — there is no middle ground. Evokes the
Baseline Test interrogation scene — a face (or plume) floating in absolute darkness.

```yaml
key_color_temp: 3400
key_intensity: 0.65
key_elevation: 25
key_fill_ratio: 16.0  # effectively infinite — no fill
fill_enabled: false
ambient_intensity: 0.0
shadow_density: 0.98
scatter_anisotropy: 0.5  # strong forward scatter from single key
```

---

## Anti-Patterns

### 1. The Ambient Flood

**Symptom:** Shadows appear gray instead of black. Volume looks uniformly lit from all
directions. No sense of depth or direction.

**Cause:** Ambient intensity set too high (> 0.03) or fill light used without motivation.

**Fix:** Set ambient to 0.0-0.01. Remove all fill lights. Rebuild lighting from a
single motivated key. Let the void be void.

**Deakins reference:** In BR2049 the Wallace Corporation scenes have enormous pools of
pure black surrounding razor-thin shafts of golden light. The ambient is effectively
zero — light exists only where it has reason to exist.

### 2. The Pretty Render

**Symptom:** The image looks technically impressive — good detail, nice color — but
evokes no emotion. It could be any volume rendering from any project.

**Cause:** Lighting designed for visual appeal rather than emotional storytelling. The
DP optimized for "looking good" instead of "feeling right."

**Fix:** Start over from the emotional intent. What should the viewer feel? Oppression
demands top-down light and crushed shadows. Revelation demands a single key cutting
through darkness. Beauty is a consequence of emotional honesty, never a goal.

### 3. The Unmotivated Rim

**Symptom:** A bright rim light outlines the plume edge, making it pop from the
background, but there is no physical source for this light.

**Cause:** Rim light added for visual separation without asking "where does this light
come from?" This is the most common VFX cheat and the one Deakins rejects most
forcefully.

**Fix:** Either find a physical motivation for the rim (atmospheric scatter from a
bright sky, reflected light from terrain) or remove it entirely. If the plume lacks
edge definition without a cheat light, the density falloff needs work, not the lighting.

### 4. The Symmetric Setup

**Symptom:** Key and fill are positioned at equal-and-opposite angles, creating a
balanced, broadcast-television look. The volume reads as a demonstration rather than a
story.

**Cause:** Defaulting to three-point lighting conventions that serve facial photography
but destroy volumetric atmosphere.

**Fix:** Use a single key. If a second light is needed, motivate it from the scene and
place it asymmetrically. Deakins almost never uses symmetric setups — asymmetry creates
tension, and tension creates engagement.

### 5. The Overworked Rig

**Symptom:** Six or more lights in the scene, each adding a "touch" of something.
Complexity without purpose. Impossible to debug or art-direct.

**Cause:** Incremental addition of lights to fix problems that should be solved at the
density or transfer function level.

**Fix:** Strip to one light. Does the single key tell the story? If not, the problem is
upstream (density field, transfer function, camera position). Add lights only after the
single-key image is emotionally correct but physically incomplete.

---

## Validation Checklist

- [ ] Every light in the scene has a `motivation` comment explaining its physical source
- [ ] Background color is exactly `#000000` (pure black)
- [ ] Shadow regions measure below `#050505` in rendered output
- [ ] Key-to-fill ratio is 4:1 or higher (infinite for Soot tier)
- [ ] Ambient intensity is 0.02 or below
- [ ] No fill light is enabled for Soot tier renders
- [ ] Scout tier (128 cubed) was rendered and reviewed before preview tier
- [ ] Every lighting adjustment logged with motivation reference
- [ ] Halo zone shows visible scattering (not flat opacity)
- [ ] Core zone shows absorption-dominated deep shadow
- [ ] No light uses constant or linear falloff
- [ ] Color temperatures are within 2700K-5600K range
- [ ] Single-key render was evaluated before adding any secondary lights
