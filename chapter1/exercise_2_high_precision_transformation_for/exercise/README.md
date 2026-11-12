# Exercise 2 — high-precision transformation for area calculation

## What it does

Takes a four-corner region of interest in longitude/latitude, derives the UTM zone
from the coordinates instead of hard-coding it, moves all four points in a single
bulk call, and then verifies the result by measuring the top edge in metres.

## The listings

| file | what it is |
| --- | --- |
| `01_precision_transform.py` | the solution: zone helper, bulk transform, distance check |
| `run_precision_transform.py` | the harness: checks the zone, the ranges and the edge length |

## Run it

```bash
cd chapter1/exercise_2_high_precision_transformation_for/exercise/files
python3 01_precision_transform.py
```

It prints the zone it chose and the four transformed corners, then the measured
distance along the top edge. `run_precision_transform.py` asserts that the helper
returns 32610 for this longitude and 32723 south of the equator, that the eastings
and northings land in the ranges zone 10N implies, and exits non-zero when the edge
length leaves the 870–890 m window.

```text
Target UTM EPSG: 32610
Transformed Coordinates (Easting, Northing in meters):
  Point 1: (551962.02, 4180460.41)
  Point 2: (552842.74, 4180466.013)
  ...
  Calculated Distance: 880.738 meters
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/utm_transform.json` | the zone, the four corners and the measured edge |

## Notes

- `always_xy=True` is what makes the input `(longitude, latitude)`; without it the
  transformer reads the pair in the axis order of the CRS and the corners invert.
- No network: the transformation runs against the local PROJ database.
