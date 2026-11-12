# Example 2 — the same parcel measured twice

## What it does

Builds one small parcel near San Francisco in WGS 84, measures it where it stands
(square degrees, a number with no unit), transforms it into the local UTM zone,
measures it again, and exports the projected frame. The listing is the chapter's
argument in one run: until the geometry is projected, the area is not an area.

## The listings

| file | what it is |
| --- | --- |
| `01_parcel_area.py` | the listing: one polygon, two measurements, one export |
| `run_parcel_area.py` | the harness: checks both numbers and the exported file |

## Run it

```bash
cd chapter1/advanced_application_script/example/files
python3 01_parcel_area.py
```

It prints the area in square degrees, transforms to EPSG:26910, prints the metric
area and exports the frame to `output/`. `run_parcel_area.py` recomputes both areas
independently and exits non-zero if the export loses its CRS or the two numbers stop
differing by five orders of magnitude.

```text
2. Area calculated in EPSG:4326 (WGS 84): 0.0001 square degrees.
   (NOTE: This value is mathematically invalid for metric measurement.)
...
4. Accurate Area Calculation (in Projected CRS):
   Area in Square Meters: 1,343,382.14 m²
   Area in Hectares:     134.3382 ha
...
6. Data successfully exported to output/parcel_verification.gpkg with CRS EPSG:26910.
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/parcel_verification.gpkg` | the projected parcel, with its CRS in the file |

## Notes

- The area warning on the geographic frame is the lesson, not a defect: GeoPandas
  says the result is likely incorrect because it is.
- The listing writes through `pathlib.Path(__file__).resolve().parent.parent`, so
  the export lands in the project's `output/` from any working directory.
