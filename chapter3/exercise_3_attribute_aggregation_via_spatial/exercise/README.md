# Exercise 3 — residential buildings per neighborhood

## What it does

Joins ten building detections to two neighborhood polygons, filters the joined frame
to `Residential`, and counts per neighborhood. Central comes out at two and North at
five; one detection lies 10 km outside both polygons and is dropped by the inner
join. The whole solution is one `sjoin`, one boolean filter and one `groupby`.

## The listings

| file | what it is |
| --- | --- |
| `01_residential_counts.py` | the solution: join, filter, aggregate, print |
| `run_residential_counts.py` | the harness: Central 2, North 5, and the counts that would be wrong |
| `prompt_sketch_exercise_3.py` | the exercise's prompt fence, kept exactly as the book prints it |

## Run it

```bash
cd chapter3/exercise_3_attribute_aggregation_via_spatial/exercise/files
python3 01_residential_counts.py
```

It prints how many detections joined, how many fell outside, and the count per
neighborhood; `run_residential_counts.py` asserts 2 and 5, that the seven residential
detections are all counted, and that the answer is smaller than the joined row count,
and exits non-zero if either count moves.

## What it produces

| path | what it is |
| --- | --- |
| `output/residential_counts.json` | detections, joined rows, the outside count, the per-hood counts |

```text
Detections loaded: 10
Detections inside a neighborhood: 9
Detections outside every neighborhood: 1

hood_name  residential_building_count
  Central                           2
    North                           5
```

## Notes

- The predicate is read left to right: a *detection* is within a *neighborhood*.
  Passing the polygons on the left and asking for `within` returns zero rows, because
  a polygon is never inside a point.
- Counting `detection_id` rather than rows matters once a point can fall in two
  polygons; here it cannot, and the harness still checks the totals agree.
- The joined frame carries `index_right`; it is dropped by the `agg`, not by a `drop`,
  which keeps the aggregation to one pass.
