# Exercise 1 — robust GeoJSON ingestion

## What it does

A loader that keeps going when the input is wrong: it validates before parsing,
returns an empty result instead of raising when nothing matches, and raises the
exercise's own `DataProcessingError` when the file itself is unusable.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_geojson_subsetter.py` | the exercise statement, exactly as the book prints it |
| `01_geojson_subsetter.py` | the solution: validation, filtering and the error contract |
| `run_geojson_subsetter.py` | the harness: four inputs, three outcomes |

## Run it

```bash
cd chapter20/exercise_1_implementing_robust_data_ingestion/exercise/files
python3 01_geojson_subsetter.py
```

It writes a valid, a corrupt and an empty input under `output/` and reports what the
loader made of each. `run_geojson_subsetter.py` asserts that three of four features
survive the filter, that an empty match returns zero features rather than raising,
and that the corrupt file raises `DataProcessingError`; it exits non-zero if any of
the three changes.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/valid_input.geojson` | four features, three of which match the filter |
| `output/corrupt_input.geojson` | the input that must raise |
| `output/subset.geojson` | the features that matched |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/geojson_subsetter.json` | the counts and the exception type |

## Notes

- "Missing" and "broken" are different answers: an empty match is a result, a
  truncated file is an error, and the loader keeps them apart.
