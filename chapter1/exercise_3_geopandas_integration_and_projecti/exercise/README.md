# Exercise 3 — GeoPandas integration and projection mismatch resolution

## What it does

Builds two frames that cannot be compared — one in Web Mercator metres, one in WGS
84 degrees — moves both under a single equal-area target, and proves the fix by
performing the overlay that would have failed before it.

## The listings

| file | what it is |
| --- | --- |
| `01_crs_alignment.py` | the solution: `unify_crs`, the overlay, the verification |
| `run_crs_alignment.py` | the harness: checks the unification and the overlay geometry |

## Run it

```bash
cd chapter1/exercise_3_geopandas_integration_and_projecti/exercise/files
python3 01_crs_alignment.py
```

It transforms both frames to EPSG:5070, prints each source and target code, and runs
the intersection. `run_crs_alignment.py` asserts that both targets compare equal,
that the intersection has a non-zero area, and — the trap — that neither source
frame was mutated by the helper; it exits non-zero when any of those changes.

```text
--- Unifying CRSs to EPSG:5070 ---
DataFrame 1: Transformed from EPSG:3857 to EPSG:5070
DataFrame 2: Transformed from EPSG:4326 to EPSG:5070
...
CRS Match Confirmed: True
Spatial operation (Intersection) successful. Resulting features: 1
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/crs_alignment.json` | both source codes, the target, the feature count and area |

## Notes

- EPSG:5070 is the equal-area projection over the contiguous United States; the
  overlay is only meaningful because both frames are in it.
- `to_crs` returns a new frame, so the helper must not assume its argument changed.
