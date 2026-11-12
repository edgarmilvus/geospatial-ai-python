# Example 1 — the distance tool the agent calls first

## What it does

Wraps one calculation a disaster agent needs immediately — how far apart two
points are — as a tool with a schema, a unit and a return value a model can read.
The listing then plays the model's part, calling the tool with the argument
dictionary the schema defines.

## The listings

| file | what it is |
| --- | --- |
| `01_geo_distance_tool.py` | the listing: the function, its schema, the tool, a simulated call |
| `run_geo_distance_tool.py` | the harness: the arithmetic, the schema and the answer |

## Run it

```bash
cd chapter20/basic_code_example/example/files
python3 01_geo_distance_tool.py
```

It prints the tool's name and then the JSON for a two-point call. The harness
asserts the Euclidean distance of a 0.1 x 0.1 degree step ($\sqrt{0.02}$), that the
schema names the arguments the function takes, and that the answer states the unit;
it exits non-zero when any of the three drifts.

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/geo_distance_tool.json` | the tool name, its arguments, the distance and the answer |

## Notes

- The distance is in degrees, and the listing says so rather than pretending it is
  metres: converting needs a CRS, which is the next chapter's subject, not this one's.
- No model and no network: the call is simulated with the dictionary the schema defines.
