# Exercise 3 — the schema goes into the prompt

## What it does

Extracts a frame's columns and types as text and injects them into a chat prompt
with `.partial()`, so a question about *borough names* can be answered against a
column called `BoroName`. The listing renders the prompt and writes it out; the
model never enters the picture.

## The listings

| file | what it is |
| --- | --- |
| `01_contextual_schema.py` | the solution: the frame, the schema string, the partialled prompt |
| `run_contextual_schema.py` | the harness: the rendered prompt holds the real columns |

## Run it

```bash
cd chapter18/exercise_3_the_contextual_schema_challenge/exercise/files
python3 01_contextual_schema.py
```

It prints the schema, then the two rendered messages, and writes them to
`output/rendered_prompt.txt`. `run_contextual_schema.py` asserts that every column
appears in the rendered system message, that the `{gdf_schema}` placeholder is gone
and that the question landed in the user message, and exits non-zero otherwise.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/rendered_prompt.txt` | both messages, roles included, as a model would receive them |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/contextual_schema.json` | the columns, the prompt size, whether the placeholder was filled |

## Notes

- The frame is synthetic — five boroughs with a `BoroName` column — so the run
  needs no dataset download.
- `.partial()` is applied once, at build time: a prompt rebuilt per question pays
  for the schema on every call.
