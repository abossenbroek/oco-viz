---
name: standing-on-shoulders
user-invocable: false
---

# Standing on Shoulders — Art-Historical Reference Compendium

A comprehensive art-historical reference covering five core contemporary artists who
bridge virtual and physical reality through 3D rendering, digital simulation, and
immersive installation. Includes predecessor genealogy, theoretical frameworks,
curatorial strategies, conservation approaches, ethical frameworks, and actionable
design heuristics derived from MoMA / Castello di Rivoli-grade practice.

**Source file:** `plan/artist_references.yaml` (LFS-tracked, ~13 000 lines)

> The file is too large to load wholesale. Use the Section Index below to load only
> the YAML key-paths relevant to your domain.

---

## Section Index (YAML key paths)

| Key Path | Content | Lines |
|----------|---------|-------|
| `output.critical_overview` | High-level art-historical summary of post-internet simulation art | 3 |
| `output.artist_profiles` | Five in-depth artist profiles (Cheng, Atkins, Miao, Evans, Steyerl) | 4–34 |
| `output.historical_and_theoretical_genealogy` | Predecessor artists, key theories (Deleuze, Manovich, Bridle), evolution of virtual-physical bridging | 35–51 |
| `output.comparative_conceptual_map` | Comparison axes (Authorship vs Autonomy, Representation vs Simulation, Critique vs Immersion), artist positioning, strategic trade-offs, 6 design heuristics | 52–89 |
| `output.evolution_of_critical_discourse` | Discourse phases 2010-2026, key critics & publications, major concepts & debates | 90–127 |
| `output.technical_production_pipelines` | Pipeline stages, toolchain comparison (Unity/Unreal vs offline), production considerations | 128–156 |
| `output.storyboarding_and_process_models` | Pre-production methodologies: Cheng systems-first vs Atkins writing-first vs Evans assemblage | 157–166 |
| `output.curatorial_and_installation_strategies` | Room layout, projection/screen, VR, sound, visitor flow, institutional constraints | 167–171 |
| `output.institutional_framing_and_recognition` | Exhibitions, acquisitions, awards at MoMA, Castello di Rivoli, Venice Biennale | 172–176 |
| `output.engineering_audience_affect_and_embodiment` | Scale, sound, tactility, participatory agency, evaluation methods, 6 design heuristics for prototyping | 177–181 |
| `output.ethical_and_political_frameworks` | Surveillance (Steyerl), censorship (Miao), synthetic bodies (Atkins), digital labor (Evans), ethics checklist | 182–242 |
| `output.conservation_and_preservation_strategies` | Obsolescence risks, emulation vs migration, documentation checklist | 243–283 |
| `output.adjacent_contemporary_practitioners` | Lawrence Lek, Lu Yang, Sondra Perry, Danielle Brathwaite-Shirley et al. | 284–324 |
| `output.practical_guide_for_emerging_artists` | Artist statements, storyboarding guidance, production planning, securing institutional interest | 325–end |

---

## Agent-Specific Loading Guide

### Auteur / Art Director
Load these sections for conceptual positioning, storyboarding models, and gallery-context precedents:
- `output.artist_profiles` — artistic voice, conceptual frameworks, key works
- `output.comparative_conceptual_map` — positioning axes and strategic trade-offs
- `output.storyboarding_and_process_models` — pre-production methodologies
- `output.institutional_framing_and_recognition` — curatorial language and reception

### Sculptor
Load these sections for material pipeline precedents and technical production strategies:
- `output.artist_profiles` — technical pipeline and material process per artist
- `output.technical_production_pipelines` — toolchain comparison and pipeline stages
- `output.engineering_audience_affect_and_embodiment` — design heuristics for physical presence

### Tonalist
Load these sections for critical discourse on color, perception, and the critique-vs-immersion axis:
- `output.evolution_of_critical_discourse` — discourse phases and key debates
- `output.comparative_conceptual_map` — critique axis, immersion vs critical distance
- `output.engineering_audience_affect_and_embodiment` — affective strategies and evaluation

### Choreographer
Load these sections for storyboarding models and curatorial visitor-flow strategies:
- `output.storyboarding_and_process_models` — narrative vs emergent structures
- `output.curatorial_and_installation_strategies` — visitor flow and spatial pacing
- `output.artist_profiles` — artistic process and storyboarding per artist

### Installer
Load these sections for curatorial installation strategies, conservation, and institutional framing:
- `output.curatorial_and_installation_strategies` — room layout, projection, sound, constraints
- `output.conservation_and_preservation_strategies` — obsolescence risks, documentation
- `output.institutional_framing_and_recognition` — curatorial framing and reception

---

## Core Design Heuristics

Six actionable design heuristics distilled from the comparative conceptual map:

### 1. Friction Heuristic (Atkins)
Introduce deliberate seams, glitches, or moments of artifice to prevent seamless immersion
from becoming complicit with spectacle. HD clarity should expose, not conceal.

### 2. Shepherd Heuristic (Cheng / Miao)
Release enough authorial control for emergent behavior to surprise the system's creator,
but embed guardrails (Cheng's "Emissary," Miao's satirical frame) to keep the work
within conceptual bounds.

### 3. Transcoding Heuristic (Evans)
Make invisible labor and production infrastructure visible as formal elements. The
Skype chats, invoices, and freelance credits ARE the artwork — not peripheral to it.

### 4. Poor Image Heuristic (Steyerl)
Resist resolution fetishism. Low-res, degraded, circulated images reveal the political
life of networks. Quality is not fidelity — quality is criticality.

### 5. Ambient Heuristic (Cheng)
Design systems that sustain engagement over "inhuman time scales." The work should
reward both the 30-second passerby and the 30-minute sitter without privileging either.

### 6. Counterfeit Heuristic (Miao)
Parody official aesthetics (corporate branding, state ideology, institutional language)
by deploying them at full fidelity for insubstantial or absurd content. Sincerity of
form + emptiness of content = critical exposure.

---

## Five Artists — Quick Reference

### Ian Cheng
- **Voice:** World-builder, systems architect, "neurological gym"
- **Key Concept:** Worlding — live simulations as open-ended ecosystems
- **Key Work:** *Emissary* trilogy (MoMA permanent collection)
- **Pipeline:** Unity, motion capture, AI agents, real-time rendering
- **Heuristics:** Shepherd, Ambient

### Ed Atkins
- **Voice:** Critic of HD realism, "conspicuous artifice," Uncanny Valley
- **Key Concept:** HD imagery as "deathlike" — perfect clarity shatters belief
- **Key Work:** *Old Food* (Castello di Rivoli), *Us Dead Talk Love* (MoMA PS1)
- **Pipeline:** Xbox Kinect + Faceshift mocap, Final Cut Pro, Logic Studio, Realflow
- **Heuristics:** Friction

### Miao Ying
- **Voice:** Satirical, lo-fi "Shanzhai" aesthetic, Chinternet cartographer
- **Key Concept:** Chinternet — censorship as productive negative space (*liu bai*)
- **Key Work:** *Chinternet Plus* (New Museum / Rhizome), *Pilgrimage into Walden XII*
- **Pipeline:** Browser-native, Unity/Unreal VR, ML simulations, hybrid installations
- **Heuristics:** Shepherd, Counterfeit

### Cecile B. Evans
- **Voice:** Poetic, transparent, hybrid digital-physical ecosystems
- **Key Concept:** Artificial affectivity — emotional transference between humans and machines
- **Key Work:** *What the Heart Wants* (MoMA), *AGNES* (Serpentine digital commission)
- **Pipeline:** CGI + 3D printing + Raspberry Pi + FogScreen, asset reuse across projects
- **Heuristics:** Transcoding

### Hito Steyerl
- **Voice:** Artist-theorist, essay documentary, "slapstick" critical humor
- **Key Concept:** Poor image, circulationism, politics of verticality
- **Key Work:** *Factory of the Sun* (Venice Biennale 2015), *How Not to Be Seen*
- **Pipeline:** After Effects, game engines, multi-channel video, architectural installations
- **Heuristics:** Poor Image
