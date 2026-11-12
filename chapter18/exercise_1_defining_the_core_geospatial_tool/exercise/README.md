# Exercise 1 — the executor tool

## What it does

Defines the one tool a Text-to-Map agent is allowed to call. The tool decides which
names the generated code can see (`gdf`, `plt`, `gpd`), refuses a run that draws
nothing, and answers a failure with the traceback the model needs for its next
attempt.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch.py` | the task statement: the executor's signature and its docstring |
| `01_executor_tool.py` | the solution: a synthetic frame, the tool, one demonstration call |
| `run_executor_tool.py` | the harness: success, refusal and failure paths |

## Run it

```bash
cd chapter18/exercise_1_defining_the_core_geospatial_tool/exercise/files
python3 01_executor_tool.py
```

It prints the frame's shape, sends one plotting snippet through the tool and prints
what came back. `run_executor_tool.py` asserts the three outcomes — a map written,
a snippet with no figure refused, a bad column returned with its traceback — and
exits non-zero if any of them changes.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/exercise_1_districts.png` | the map the executed snippet drew |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/executor_tool.json` | the frame's columns, the map size, whether the silent run was refused |

## Notes

- The frame is built in the listing: the `naturalearth_lowres` dataset the first
  draft read no longer ships with GeoPandas 1.x.
- No network and no key: the snippet is written in the listing, not by a model.
