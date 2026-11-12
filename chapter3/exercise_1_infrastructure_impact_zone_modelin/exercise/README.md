# Exercise 1 — the corridor that clips farmland

## What it does

Buffers a 10 km pipeline by 500 m, intersects that corridor with three parcels,
computes each overlap's area, joins the parcels' original areas back and reports the
percentage of each parcel the corridor consumes. Parcel 101 lies wholly inside the
corridor (100 %), parcel 102 loses half its height (1 000 000 of 4 000 000 m², 25 %),
and parcel 103 is 20 km away and must not appear at all.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise statement, exactly as the book prints it |
| `01_pipeline_corridor_impact.py` | the solution: buffer, overlay, area, merge, percentage |
| `run_pipeline_corridor.py` | the harness: parcel ids, both areas, both percentages |

## Run it

```bash
cd chapter3/exercise_1_infrastructure_impact_zone_modelin/exercise/files
python3 01_pipeline_corridor_impact.py
```

It prints the corridor, the clipped parcel ids and the final table of parcel,
impacted area, original area and percentage; `run_pipeline_corridor.py` asserts
101 at 100 %, 102 at 25 % and 103 absent, and exits non-zero if the original areas
are taken from the clipped geometry instead of the input layer.

## What it produces

| path | what it is |
| --- | --- |
| `output/pipeline_impact.json` | affected and unaffected parcels, both areas, both percentages |

```text
1. Corridor: 10,784,137 m2 around a 10,000 m pipeline
3. Parcels clipped by the corridor: [101, 102]

 parcel_id crop_type  impacted_area_sqm  total_area_sqm_original  impact_percent
       101     Wheat          3000000.0                3000000.0           100.0
       102      Corn          1000000.0                4000000.0            25.0

Parcels untouched by the corridor: [103]
```

## Notes

- The corridor's area is the line buffered by 500 m, not the line's length: the two
  ends are half-discs, the sides are rectangles.
- The percentage divides by `total_area_sqm_original`, merged back from the input
  frame. Dividing by the clipped geometry's own area gives 100 % for everything.
- `union_all()` replaces the deprecated `unary_union` attribute for collapsing a
  buffered geometry series into one shape.
