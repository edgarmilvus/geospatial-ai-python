# Example 1 — one tool, one schema, one simulated call

## What it does

Wraps a centroid calculation in the two things a language model needs before it
can call anything: a Pydantic model that names and describes the argument, and a
`StructuredTool` that binds that model to the function. The script then plays the
model's part, handing the tool the argument dictionary the schema defines — which
is what the framework does once it has parsed a model's output.

## The listings

| file | what it is |
| --- | --- |
| `01_tool_schema.py` | the listing: schema, function, tool, simulated call |
| `run_tool_schema.py` | the harness: schema/function agreement and the centroid arithmetic |

## Run it

```bash
cd chapter18/basic_code_example/example/files
python3 01_tool_schema.py
```

It prints the tool's name, the length of its description and its schema fields, then
the JSON the call returns. `run_tool_schema.py` asserts that the schema's key is the
function's argument, that the centroid of the test square sits at −74.015 / 40.715,
and that an invalid polygon returns a JSON error instead of raising.

```text
Tool name: calculate_geometry_centroid
Description length: 112 characters
Schema fields: ['wkt_polygon']
...
Centroid X (longitude): -74.015000
Centroid Y (latitude):  40.715000
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/tool_schema.json` | the tool name, its fields, and the centroid it computed |

## Notes

- No model, no key, no network: the call is simulated with the dictionary the
  schema itself defines.
- The error branch returns JSON too, so a caller parses one shape whether the
  polygon was valid or not.
