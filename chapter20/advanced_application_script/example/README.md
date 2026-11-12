# Example 2 — the end-to-end damage assessment

## What it does

Runs the capstone pipeline over a pre- and post-disaster scene: it aligns the two
rasters, segments the buildings, classifies each one's damage, summarises the
classes, exports the assessment and answers a question about it. The model is one
boundary among several; the rest is geometry, raster arithmetic and a deterministic
classifier.

## The listings

| file | what it is |
| --- | --- |
| `01_adda_pipeline.py` | the listing: alignment, classification, summary, export, answer |
| `run_adda_pipeline.py` | the harness: twenty buildings, four classes, the exported file |

## Run it

```bash
cd chapter20/advanced_application_script/example/files
python3 01_adda_pipeline.py
```

It writes the aligned scenes and the assessment GeoJSON under `output/`, prints the
per-class summary and the answer. `run_adda_pipeline.py` asserts the building count,
that the areas per class sum to the total, that the export carries EPSG:4326 while
the analysis ran in EPSG:32611, and exits non-zero when the classification stops
matching the scenes it was given.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/assessment_report.geojson` | one feature per building, with its damage class |
| `output/disaster_data/` | the aligned pre- and post-disaster scenes |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/adda_pipeline.json` | the counts, the area per class and the answer |

## Notes

- Twenty buildings, four classes, 4 570 m² of roof in total: small enough to run in
  seconds on a CPU and large enough for the summary to mean something.
- The export is reprojected to EPSG:4326 on the way out; the analysis stays in the
  metric CRS, because an area in degrees is not an area.
