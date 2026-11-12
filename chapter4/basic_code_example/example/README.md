# Basic code example — quantifying an irregular land parcel

## What it does

Builds an L-shaped polygon from seven vertices in a planar coordinate system where one
unit is one metre, then reads the three metrics every feasibility study starts from:
`area` (75 square units), `length` for the boundary a fence must follow (40 units), and
`centroid` as the point a survey drone would visit. Nothing is projected and nothing is
fetched: the exercise is about the geometry itself.

## The listings

| file | what it is |
| --- | --- |
| `01_irregular_parcel_metrics.py` | the listing: the vertex list, the `Polygon`, the three attributes |
| `run_parcel_metrics.py` | the harness: checks the geometry, then the printout |

## Run it

```bash
cd chapter4/basic_code_example/example/files
python3 01_irregular_parcel_metrics.py
```

It builds the ring, prints the WKT, the area, the perimeter and the centroid coordinates.
`run_parcel_metrics.py` asserts that the L is 75 units and not 100, that the boundary is
40 units, that the centroid is at 25/6 on both axes, and that the printout says the same;
it exits non-zero when any of those stops holding.

```text
1. Polygon Definition (WKT): POLYGON ((0 0, 10 0, 10 5, 5 5, 5 10, 0 10, 0 0))
2. Calculated Area (units²): 75.00
3. Calculated Perimeter (units): 40.00
4. Centroid Coordinates (Shapely Point): POINT (4.166666666666667 4.166666666666667)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/parcel_metrics.json` | vertex count, area, perimeter, centroid, validity |

## Notes

- The parcel is deliberately the 10 × 10 square with a 5 × 5 corner removed, so a reader
  who assumes `width × height` gets 100 and the harness fails: 75 is the real answer.
- The centroid is *not* the average of the six corners; it is the area-weighted centre at
  25/6 ≈ 4.1667, which is why the listing prints it rather than the corner mean.
- No CRS is attached anywhere in this listing. That is the point of the exercise: `shapely`
  is a plane, and the units are whatever the reader says they are.
