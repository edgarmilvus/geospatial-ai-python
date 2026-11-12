# Exercise 2 — geodesic versus planar distance at high latitude

## What it does

Measures Svalbard to Reykjavik twice: once as a diagonal through a plane of degrees
(40.1311°), once along the WGS 84 ellipsoid (2 000.05 km), and quantifies the gap. Converting
the planar answer with a single 35.9 km-per-degree factor — 111.32 km × cos(71.18°) — gives
1 441.16 km, so reading degrees as a plane underestimates the route by 27.94 %.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_high_latitude.py` | the task statement: the two stations, and nothing computed |
| `01_high_latitude_distance.py` | the listing: both distances, the conversion, the error |
| `run_high_latitude_distance.py` | the harness: the arithmetic, the real separation, the sign |

## Run it

```bash
cd chapter4/exercise_2_geodesic_vs_planar_distance_in_hig/exercise/files
python3 01_high_latitude_distance.py
```

It prints both coordinates, the planar distance in degrees, its kilometre conversion, the
geodesic distance and the percentage error. `run_high_latitude_distance.py` asserts that the
planar figure is Pythagoras on the two coordinate differences, that the conversion factor is
111.32 × cos(71.18°), that the geodesic distance is 2 000 km and that the planar method
underestimates; it exits non-zero when any of them changes.

```text
1. Planar Distance (Degrees): 40.1311°
   (Approximate Planar Distance in KM using average latitude conversion: 1441.16 km)
2. True Geodesic Distance (KM): 2000.05 km
----------------------------------------
Percentage Error (Planar vs. Geodesic): 27.94%
```

## What it produces

| path | what it is |
| --- | --- |
| `output/high_latitude_distance.json` | both stations, both distances, the error, the factor |

## Notes

- The error is not a rounding artefact; it is 1 − cos(latitude) made visible. At the equator
  the same code is within a few per cent; at 71 °N it is off by more than a quarter.
- Shapely is handed `(lon, lat)`, the order a plane expects. Feeding `(lat, lon)` still
  returns a number — the wrong one — which is why the harness checks the value, not the call.
- A single degree-to-kilometre factor cannot be right for both axes: a degree of longitude is
  35.9 km at this latitude, a degree of latitude is 111.3 km. The listing uses the factor for
  longitude on both and says so.
