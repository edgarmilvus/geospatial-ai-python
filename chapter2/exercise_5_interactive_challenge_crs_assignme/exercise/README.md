# Exercise 5 — repair a layer that has no CRS

## What it does

Reads three boundary points, shows a frame with no CRS, assigns WGS 84 with
`set_crs('EPSG:4326')` and proves the repair by reprojecting to Web Mercator. The
listing is also honest about where a missing CRS comes from: a GeoJSON read always
reports EPSG:4326, because RFC 7946 fixes it, so the undefined state is reproduced
explicitly — the way a Shapefile that lost its `.prj`, or a CSV of coordinates,
really arrives.

## The listings

| file | what it is |
| --- | --- |
| `01_assign_crs.py` | the solution: load, diagnose, `set_crs`, verify, reproject |
| `run_crs_assignment.py` | the harness: CRS before and after, coordinates, Web Mercator metres |

## Run it

```bash
cd chapter2/exercise_5_interactive_challenge_crs_assignme/exercise/files
python3 01_assign_crs.py
```

It writes `output/boundary_points.geojson`, reads it, prints the CRS before and after
the assignment and the first point in both systems; `run_crs_assignment.py` asserts
that the frame ends in EPSG:4326 at longitude -118.25 and projects to about
-13 163 530 m, and exits non-zero if the assignment or the reprojection stops working.

## What it produces

| path | what it is |
| --- | --- |
| `output/boundary_points.geojson` | the three points the listing reads |
| `output/crs_assignment.json` | CRS before and after, the first point in degrees and in metres |

```text
2. Initial CRS: None
   Diagnostic: CRS is undefined. Manual assignment is required.

3. Assigning CRS: EPSG:4326...
4. Final Assigned CRS: EPSG:4326
   Verification: CRS successfully assigned and data is ready.
```

## Notes

- `set_crs` labels coordinates; `to_crs` moves them. Assigning the wrong CRS and then
  reprojecting shifts the data without any error, which is why the diagnostic step
  comes first.
- Storing the projection and moving the file separately is how a Shapefile loses its
  `.prj`; treat the sidecars as one dataset.
- The Web Mercator figure is a property of the coordinate pair, not of the machine:
  the projection puts one degree of longitude at 111 319.49 m, so -118.25° lands at
  -13 163 530 m.
