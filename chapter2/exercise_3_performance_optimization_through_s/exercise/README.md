# Exercise 3 — read two columns instead of seven

## What it does

Writes a road layer with seven attributes, then reads it twice: once whole, and
once with `columns=['segment_id', 'road_class']`. The second read hands three columns
to Python — the two requested attributes plus the geometry the driver adds back —
which is the exercise's answer. The skipped five are filtered inside the I/O layer,
so they are never materialised as Python objects at all.

## The listings

| file | what it is |
| --- | --- |
| `01_selective_columns.py` | the solution: write the road file, read it selectively and whole, compare |
| `run_selective_columns.py` | the harness: the three-column result, the eight-column comparison, the rows |
| `prompt_sketch_exercise_3.py` | the exercise's prompt fence, kept exactly as the book prints it |

## Run it

```bash
cd chapter2/exercise_3_performance_optimization_through_s/exercise/files
python3 01_selective_columns.py
```

It writes `output/global_roads.shp`, reads it with and without `columns=`, and prints
the resulting column lists and how many columns were skipped; `run_selective_columns.py`
asserts the three-column result, the five skipped names and the active geometry column,
and exits non-zero if the filter stops being pushed into the read.

## What it produces

| path | what it is |
| --- | --- |
| `output/global_roads.shp` (+ sidecars) | the seven-attribute road layer |
| `output/selective_columns.json` | both column lists, the skipped set, row count, geometry type |

```text
Columns loaded in optimized GeoDataFrame:
['segment_id', 'road_class', 'geometry']

Rows read: 3
Columns read: 3 of 8
Columns skipped: ['admin_code', 'legacy', 'length_km', 'surface', 'traffic']
```

## Notes

- `columns=` is not the same as dropping afterwards: the drop happens after the driver
  has already read, converted and boxed every column. On a wide layer that difference
  is the memory ceiling.
- The geometry column needs no mention; the driver adds it and keeps it active.
- Field names are kept inside the DBF ten-character limit, so the only thing this
  listing demonstrates is the column budget.
