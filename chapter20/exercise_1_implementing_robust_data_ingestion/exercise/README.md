# Exercise 1 (statement) — robust GeoJSON ingestion

## What it does

Publishes the requirement, not an implementation: validate the input, return an
empty result when nothing matches, raise a named error when the file cannot be
read, and never let a truncated JSON reach the parser.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_geojson_subsetter.py` | the shape the exercise asks for, kept verbatim from the book |

## Run it

```bash
cd chapter20/exercise_1_implementing_robust_data_ingestion/exercise/files
python3 prompt_sketch_geojson_subsetter.py
```

The sketch defines the signature and the docstring and does nothing else; running it
prints the contract it is asking you to implement. The worked answer lives in
`chapter20/exercise_1/exercise/`.

## What it produces

Nothing: this folder is the statement. The solution beside it writes the artefacts.

## Notes

- Kept byte-identical to the book, so the statement and the solution can be read
  side by side without the reader wondering which changed.
