# Advanced application script — urban infrastructure impact assessment

## What it does

Measures one industrial zone twice, on purpose. On the ellipsoid (`pyproj.Geod`) the
diamond beside Los Angeles covers 51.24 square kilometres inside a 28 871 m boundary; in
Web Mercator the same diamond is a planar polygon that can be buffered by 500 m and asked
whether three housing centroids fall inside. The script then reports, per zone, the planar
distance to the boundary that decides the verdict and the geodesic distance between
centres that describes the real separation.

## The listings

| file | what it is |
| --- | --- |
| `01_urban_impact_assessment.py` | the listing: geodesic metrics, the 3857 buffer, the table |
| `run_urban_impact.py` | the harness: ellipsoidal numbers, buffer geometry, verdicts |

## Run it

```bash
cd chapter4/advanced_application_script_urban_infrastruct/example/files
python3 01_urban_impact_assessment.py
```

It prints the centroid, the ellipsoidal area and perimeter, a three-row table of zones with
their planar and geodesic distances, and the verdict for the near zone. `run_urban_impact.py`
asserts the 51.24 km² area, the 500 m buffer that grows the bounding box by 500 m on every
side, the three verdicts and the 1.46× area inflation Web Mercator applies at 34 °N; it
exits non-zero when any of them changes.

```text
IZ Centroid (WGS84): Lat=34.0000, Lon=-118.1500
IZ Calculated Geodesic Area: 51.24 sq km
IZ Perimeter (Geodesic): 28871.25 meters
...
    Res Zone 1 (Near) IMPACTED                     857.29                          2.99
     Res Zone 2 (Far)     SAFE                   26140.11                         26.17
Res Zone 3 (Critical) IMPACTED                    2570.35                          2.22
```

## What it produces

| path | what it is |
| --- | --- |
| `output/urban_impact.json` | area, perimeter, distortion factor, buffer area, three zone rows |

## Notes

- `pyproj.Geod` spells its inverse solution `inv`, not `inverse`; the listing called it
  `inverse` and died with `AttributeError` on pyproj 3.7. One-word fix, comment included.
- Web Mercator is conformal, not equal-area: at 34 °N the projected area of this polygon is
  1.459 times its true area, which is why the buffer's area (92.96 km²) is not the true
  footprint of a 500 m band.
- Zone 3 is impacted *from inside* the zone, 2 570 m from the boundary. "Inside the buffer"
  and "within 500 m of the wall" are different questions, and the listing answers the first.
- Deterministic: fixed coordinates, no random numbers, no files read.
