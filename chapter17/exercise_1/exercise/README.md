# Exercise 1 — a point prompt that survives the trip to a GeoPackage

## What it does

Segments one building from a point prompt on a georeferenced 100 x 100 patch, exports the
mask as a GeoPackage polygon using the source image's own transform and CRS, and then checks
that the vector file reports the CRS it started from. An empty mask exports nothing and says
so.

## The listings

| file | what it is |
| --- | --- |
| `georeferenced_export.py` | the solution: scene, point prompt, export, verification |
| `run_georeferenced_export.py` | the harness: 100 m², bounds, CRS match, refusals |

## Run it

```bash
cd chapter17/exercise_1/exercise/files
python3 georeferenced_export.py
```

It writes the scene, segments 100 pixels, writes the GeoPackage, and prints the validation
line and the re-read bounds. `run_georeferenced_export.py` asserts that the polygon is
100 m² at easting 300 045 and northing 4 499 955, that the GeoPackage returns the source CRS,
and that an empty or wrongly sized mask is refused; it exits non-zero when the georeferencing
stops matching.

```text
Wrote mock_satellite_image.tif: 100 x 100 at 1 m, EPSG:32618
[SAM] segment_anything is not installed; using the threshold stand-in.
Segmenter: stand-in
Prompting at pixel (x=50, y=50)
Mask: (100, 100), 100 pixels, score 0.94
Input image CRS: EPSG:32618

[SUCCESS] Exported 1 features to building_footprints.gpkg
[VALIDATION] Output vector CRS: EPSG:32618

[VERIFICATION] Georeferencing Integrity Check PASSED: input CRS matches output CRS.
Re-read building_footprints.gpkg: 1 feature(s), CRS EPSG:32618, area 100 m²
Bounds: (300045.0, 4499945.0, 300055.0, 4499955.0)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/mock_satellite_image.tif` | the 100 x 100 three-band patch, EPSG:32618, 1 m |
| `output/building_footprints.gpkg` | the polygon with `class` and `area_sqm` |
| `output/georeferenced_export.json` | the mask, the area, the bounds and the CRS match |

## Notes

- The draft wrote its "GeoPackage" through a `MockVectorWriter` that printed a path and
  created nothing, and its `MockRaster` returned a transform from a constructor argument, so
  the georeferencing it "verified" was the constant it had passed in. Here the scene is a real
  GeoTIFF and the transform comes from `rasterio.open`.
- The draft imported `fiona.crs.from_epsg` and then never used it; the CRS is `src.crs`, which
  is the same object the file carries.
- The mask is validated against the image's dimensions before any vector is written: a
  64 x 64 mask against a 100 x 100 image raises `ValueError` rather than landing 36 % of the
  scene in the wrong place.
- No SAM package and no weights are needed: the point prompt runs against the threshold
  stand-in, which is declared in the comment above the class. About 0.4 s.
