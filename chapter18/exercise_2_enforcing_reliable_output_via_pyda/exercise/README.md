# Exercise 2 — forcing the summary into a schema

## What it does

Defines the four fields an agent must report after it makes a map, then validates
one complete answer and one broken answer. A validator normalises the colormap name
— models write *the viridis colormap*, the pipeline needs `viridis` — and the
optional classification scheme stays optional.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch.py` | the task statement: the schema and the four fields the agent must report |
| `01_structured_summary.py` | the solution: the model, two validators, a valid and an invalid answer |
| `run_structured_summary.py` | the harness: acceptance, rejection, normalisation |

## Run it

```bash
cd chapter18/exercise_2_enforcing_reliable_output_via_pyda/exercise/files
python3 01_structured_summary.py
```

It prints the accepted summary, the reason the rejected one failed, and the JSON
schema a model would be shown. `run_structured_summary.py` asserts that a blank
column name is rejected, that a missing optional field is accepted, that a missing
required field is not, and exits non-zero when the contract loosens.

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/structured_summary.json` | the fields, the accepted object, the rejection reason |

## Notes

- No model is called: the exercise is about the contract, and the contract is
  checkable without one.
- `langchain_core.pydantic_v1` no longer exists in current LangChain; the listing
  imports Pydantic directly, which is what the shim re-exported anyway.
