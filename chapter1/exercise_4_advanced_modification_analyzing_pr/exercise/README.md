# Exercise 4 — analysing projection distortion

## What it does

Puts one 10 km square near the pole in Polar Stereographic, measures it there,
re-projects it to Web Mercator, measures it again, and quantifies the difference.
The parcel never moved: only the coordinate system did.

## The listings

| file | what it is |
| --- | --- |
| `01_distortion.py` | the solution: two areas and the distortion formula |
| `run_distortion.py` | the harness: recomputes the areas and checks the formula |

## Run it

```bash
cd chapter1/exercise_4_advanced_modification_analyzing_pr/exercise/files
python3 01_distortion.py
```

It prints the true area, the distorted one, the absolute difference and the
percentage. `run_distortion.py` asserts the true area is 100 000 000 m² to within a
square metre, checks the formula on three easy cases (50 per cent up, no change, 50
per cent down — it must not return −50), and exits non-zero when the inflation stops
being enormous.

```text
1. True Area (in EPSG:3413 - meters): 100,000,000.00 sq meters
2. Distorted Area (in EPSG:3857 - meters): 7,976,519,555.00 sq meters
...
Percentage Distortion: 7876.52%
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/distortion.json` | both areas and the percentage |

## Notes

- The formula uses the absolute difference, because a projection can shrink an area
  as well as grow it and "distortion" is a magnitude.
- No network and no data files: the polygon is built from metres.
