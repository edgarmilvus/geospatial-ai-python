# Exercise 3 — GeoAI proximity agent, dynamic facility assignment

## What it does

Puts one incident at 500000/4500000 in UTM zone 10N and five service centres around it,
finds the nearest with the vectorised `GeoSeries.distance`, and turns the pair into a search
radius: the nearest centre is 141.42 m away, its segment's centroid is at
(500050, 4500050), and the smallest circle centred there that holds both points has a radius
of 70.71 m.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_proximity_agent.py` | the task statement: the incident and the five points of interest |
| `01_proximity_assignment.py` | the listing: the GeoSeries, `idxmin`, the segment, the radius |
| `run_proximity_assignment.py` | the harness: nearest centre, midpoint, and the circle itself |

## Run it

```bash
cd chapter4/exercise_3_geoai_proximity_agent_dynamic_faci/exercise/files
python3 01_proximity_assignment.py
```

It prints the incident, the nearest POI's index and coordinates, the distance, the zone centre
and the radius. `run_proximity_assignment.py` asserts that the nearest centre is POI 1 at
√2 × 100 m, that the centre is the midpoint of the segment and the radius half its length,
and that both points sit exactly on that circle; it exits non-zero when any of them changes.

```text
Closest POI Found (Index 0): (500100, 4500100) m
Distance to Closest POI: 141.42 meters
----------------------------------------
Center of Critical Proximity Zone (Centroid): (500050.00, 4500050.00) m
Minimum Required Proximity Radius: 70.71 meters
```

## What it produces

| path | what it is |
| --- | --- |
| `output/proximity_assignment.json` | CRS, incident, closest POI, distance, centre, radius |

## Notes

- The exercise calls the distance the *diameter*: a circle centred between the two points has
  to reach both, so the radius is half. The harness proves the reading by measuring from the
  centre to each point and getting 70.71 m twice.
- UTM zone 10N (EPSG:26910) is what makes the numbers metres. The same code on EPSG:4326
  would return 0.0013 degrees for the same pair, a quantity with no unit.
- Five points is small enough to read, large enough that `idxmin` has to choose: POI 2 is
  1 118.03 m away, POI 4 is 1 414.21 m, so the answer is not the first row by accident.
