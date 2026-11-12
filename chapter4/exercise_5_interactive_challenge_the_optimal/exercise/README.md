# Exercise 5 — the optimal geo-fence design

## What it does

Combines three proximity rules into one monitored boundary: a 50 m security buffer around a
50 000 m² six-sided building, plus a 20 m margin around each of two utility access points,
merged with `union_all()`. Because one access point stands 67.08 m from the nearest wall and
50 + 20 = 70 m of buffer, that disc merges with the building fence; the far point keeps its own
island. The result is a two-part `MultiPolygon` covering 102 669.71 m² inside a 1 369.91 m
boundary.

## The listings

| file | what it is |
| --- | --- |
| `01_geofence_design.py` | the listing: three buffers, the union, area and perimeter |
| `run_geofence_design.py` | the harness: each buffer, the merge, the union's metrics |

## Run it

```bash
cd chapter4/exercise_5_interactive_challenge_the_optimal/exercise/files
python3 01_geofence_design.py
```

It prints the two buffer distances, the resulting geometry type, the monitored area and the
fence perimeter. `run_geofence_design.py` asserts each buffer against the Steiner formula, the
67.08 m wall distance that makes two of the three rings merge, the 102 669.71 m² area and the
1 369.91 m perimeter; it exits non-zero when any of them changes.

```text
Resulting Geo-Fence Type: MultiPolygon
----------------------------------------
Total Monitored Area (sq meters): 102669.71
Total Geo-Fence Perimeter (meters): 1369.91
```

## What it produces

| path | what it is |
| --- | --- |
| `output/geofence_design.json` | building area, both buffer distances, fence area/perimeter/type/parts |

## Notes

- The trap is the part count. Buffering does not stay three separate shapes: the 20 m disc at
  400/150 overlaps the 50 m building fence, so the union has two parts, and an agent that
  assumed "three rules, three polygons" would index the wrong ring.
- The fence's area is not the sum of three discs and a rectangle — a polygon grown by r gains
  `perimeter × r + πr²`, which is the Steiner term the harness checks.
- Units are metres by assumption: these coordinates are a projected plane, and the listing says
  so in its first comment. In WGS 84 the two buffer distances would mean nothing.
