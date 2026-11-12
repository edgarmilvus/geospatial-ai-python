# Example 2 — the Text-to-Map agent

## What it does

Builds the whole pipeline in four pieces: a five-municipality GeoDataFrame with a
computed density column, the schema of that frame as text for the model, one tool
that executes the code the model writes against the frame, and a ReAct loop that
alternates between them until a map exists. The model is the only boundary, which
is why it is the only thing the harness replaces.

## The listings

| file | what it is |
| --- | --- |
| `01_text_to_map_agent.py` | the listing: frame, schema, tool, prompt, executor |
| `run_text_to_map_agent.py` | the harness: drives the loop with a scripted model |

## Run it

```bash
cd chapter18/geopandas_text_to_map_agent/example/files
python3 01_text_to_map_agent.py
```

Without a key it builds the frame, the schema, the prompt and the tool, says so and
exits 0; with `OPENAI_COMPATIBLE_API_KEY` exported it runs the loop and writes
`output/geo_agent_density_map.png`. `run_text_to_map_agent.py` drives the same loop
with a scripted model, asserts that the generated code reached the tool and that the
PNG is a real image, and exits non-zero if the agent answers without drawing.

```text
--- Text-to-Map agent ---
User query: I need a choropleth map showing the population density ...
No OPENAI_COMPATIBLE_API_KEY in the environment, so the loop is not run.
```

## What it produces

Written by the run, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/geo_agent_density_map.png` | the map the model's code drew |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/text_to_map.json` | the frame's columns, the density values, the map size, the answer |

## Notes

- The ReAct template lives in the listing, not in a prompt hub: a demo that needs
  the network to build its prompt cannot run in an offline suite.
- The prompt ends with *stop after the Action Input line*. A model that writes the
  Observation itself breaks the parser, and it does so only against a real endpoint.
- The three variables are the only configuration: `OPENAI_COMPATIBLE_BASE_URL`,
  `OPENAI_COMPATIBLE_MODEL`, `OPENAI_COMPATIBLE_API_KEY`.
