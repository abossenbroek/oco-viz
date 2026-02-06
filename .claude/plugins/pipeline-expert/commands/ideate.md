---
name: ideate
description: Launch a dual-model creative ideation session with Claude analysis + Gemini provocation
user-invocable: true
---

# Ideate Command

Launch a dual-model creative ideation session. Claude establishes ground truth
from data and project state; Gemini generates radical artistic provocations;
the Auteur synthesizes both into an actionable Director's Brief.

## Usage

```
/pipeline-expert:ideate "creative intent description"
```

## Arguments

- `"creative intent"`: A description of the artistic goal or question to explore

## Ideation Protocol

### Phase 1 -- Analysis (Claude)

Establish Ground Truth from current data and project state:
- What does the data actually show? (XCO2 anomalies, wind patterns, emission sources)
- What technical canvas is available? (grid resolution, TF architecture, render budget)
- What constraints exist? (Spectralist's physical envelope, Tonalist's achromatic discipline)

### Phase 2 -- Provocation (Gemini)

Use `mcp__pal__chat` with `model: gemini-2.5-pro` to generate 3-5 radical artistic
theses. The Gemini prompt:

```
You are The Artist in a creative dialectic about volumetric CO2 visualization.
The aesthetic is "Soot" -- Anthropocene industrial dread. Coal dust, volcanic ash,
charcoal powder. Achromatic, monumental, geological. NOT pretty data visualization.

Given this Ground Truth about the data:
{ground_truth}

The artistic intent is:
{intent}

Propose 3-5 radical artistic theses that intentionally diverge from literal
interpretation. Reference art history. Push beyond comfortable interpretation.
Each thesis should name a specific artistic strategy and explain how it transforms
the data into emotional experience.
```

### Phase 3 -- Synthesis (Auteur)

The Auteur reviews Gemini's theses against the ground truth and creates a
Director's Brief with per-agent directives:
- `sculptor_directive`: volume structure and material parameters
- `tonalist_directive`: TF architecture and color discipline
- `choreographer_directive`: camera language and temporal arc

### Phase 4 -- Execution

Translate the Director's Brief into actionable parameters and code snippets
that can be applied to the pipeline configuration.

## Output

`ideation_result` YAML per output-schemas, containing ground truth, provocations,
synthesis with per-agent directives, and execution plan.

## Examples

```
/pipeline-expert:ideate "Evoke the suffocating stillness before a volcanic eruption"
/pipeline-expert:ideate "Make the Australian bushfire carbon plume feel like geological violence"
/pipeline-expert:ideate "The viewer should feel complicit in the emission -- they breathe it"
/pipeline-expert:ideate "Transform Permian Basin methane flares into industrial requiem"
```

$ARGUMENTS parsed as the creative intent string.
