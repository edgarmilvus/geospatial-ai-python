# Exercise 2 — configuration that fails fast

## What it does

Loads the pipeline's settings from the environment and refuses to start when they
are incomplete, naming **every** missing variable in one message. A value that is
present but wrong — a shapefile where a GeoJSON was required — is rejected too.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_config.py` | the task statement: the settings the pipeline reads and the loader it needs |
| `01_agent_configuration.py` | the solution: the required set, the loader, the four cases |
| `run_agent_configuration.py` | the harness: nothing set, one missing, all set, wrong type |

## Run it

```bash
cd chapter20/exercise_2_configuring_the_geoai_agent_pipeli/exercise/files
python3 01_agent_configuration.py
```

It runs the four cases and prints the message each one produces. The harness asserts
that the empty case names all three variables at once, that a wrong extension is
rejected with the value quoted back, and that a complete environment loads; it exits
non-zero when a message starts listing one variable at a time.

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/agent_configuration.json` | the required names and the message for each case |

## Notes

- The variables here are the pipeline's own settings (`GEOAI_API_KEY`,
  `DISASTER_ZONE_AOI`, `SAM_MODEL_PATH`), not the three model variables the two
  agent chapters use — this exercise is about failing fast, not about the gateway.
- Nothing is read from a file: the environment is the only source, which is what
  makes the message list every missing name.
