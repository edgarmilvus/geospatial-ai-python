# Exercise 1 — geometric properties of a proposed land parcel

## What it does

Takes the pentagon the exercise hands the reader — (10, 20), (35, 5), (50, 30), (40, 60),
(20, 50) — builds it as a `shapely.Polygon`, guards the construction with the exercise's own
`InvalidGeoFeatureError`, and prints the three metrics a planner needs before any projection
work starts: 1 325 square units of land, 143.92 units of boundary, and a centroid at
(30.9119, 32.0440) for the first utility hookup.

## The listings

| file | what it is |
| --- | --- |
| `01_parcel_metrics_starter.py` | the task statement: the pentagon's vertices and the error class |
| `05_parcel_metrics_solution.py` | the solution to exercise 1 |
| `run_parcel_analysis.py` | the harness: the solution's metrics, and that the starter is still a starter |

## Run it

```bash
cd chapter4/exercise_1_parcel_geometry_validation_area_pe/exercise/files
python3 05_parcel_metrics_solution.py
```

It validates the pentagon and prints area, perimeter and centroid to the precision the
exercise asks for. `run_parcel_analysis.py` asserts the shoelace area of 1 325, the 143.92
boundary, the centroid to four decimals, that the centroid really lies inside the ring, and
that the starter still defines its inputs and no answer; it exits non-zero when any of them
changes.

```text
--- Urban Planning Feature Analysis ---
Feature Validation: SUCCESS (Geometry is valid)
Total Parcel Area (sq units): 1325.00
Parcel Perimeter (units): 143.92
Geometric Centroid (X, Y): (30.9119, 32.0440)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/parcel_analysis.json` | vertex count, area, perimeter, centroid, validity, starter list |

## Notes

- The four starter blocks are tasks, not answers: they define coordinates and constants and
  stop. The harness asserts exactly that, so a future edit that pastes a solution into a
  starter fails instead of quietly turning an exercise into a listing.
- `05_parcel_metrics_solution.py` prints "SUCCESS (Geometry is valid)" from a check that
  would raise `InvalidGeoFeatureError` on a self-intersecting ring; the listing's own
  message is the only place the reader sees the branch it never took.
- Planar units only. The exercise exists to show what a metric means before a CRS is chosen.
