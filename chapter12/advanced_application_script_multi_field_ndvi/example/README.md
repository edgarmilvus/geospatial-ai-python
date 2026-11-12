# Advanced application script — two fields, from GeoTIFF to index raster

## What it does

Simulates two agricultural scenes as real two-band GeoTIFFs (band 1 Red, band 2 NIR,
uint16 digital numbers), reads them back, computes a masked NDVI, classifies it into
four health bands, and writes one float32 index raster per field.

## The listings

| file | what it is |
| --- | --- |
| `multi_field_ndvi.py` | the listing: scene generator, masked NDVI, classification, rasters |
| `run_multi_field_ndvi.py` | the harness: the mask, the nodata write, the field means |

## Run it

```bash
cd chapter12/advanced_application_script_multi_field_ndvi/example/files
python3 multi_field_ndvi.py
```

It writes two scenes and two index rasters into `output/`, prints each field's mean
index and class percentages, and ends on the comparative report.
`run_multi_field_ndvi.py` asserts 45 facts — the 36 shadow pixels excluded and
written as nodata, healthy corn near 0.75 against stressed wheat near 0.25, the four
class percentages adding to 100, and the seed rebuilding the same scene — and exits
non-zero if any of them changes.

```text
--- Analysis for Field_A_Healthy_Corn ---
Mean NDVI: 0.7507
Valid pixels: 9180 of 9216 (36 nodata)
  Water/Shadow: 0 pixels (0.00%)
  Poor: 0 pixels (0.00%)
  Moderate: 61 pixels (0.66%)
  Healthy: 9119 pixels (99.34%)

--- Analysis for Field_B_Stressed_Wheat ---
Mean NDVI: 0.2551
Valid pixels: 9180 of 9216 (36 nodata)
  Water/Shadow: 351 pixels (3.82%)
  Poor: 3017 pixels (32.86%)
  Moderate: 5313 pixels (57.88%)
  Healthy: 499 pixels (5.44%)

=============================================
SERIES SUMMARY REPORT: VEGETATION HEALTH INDEX
=============================================
```

## What it produces

| path | what it is |
| --- | --- |
| `output/Field_A_Healthy_Corn_scene.tif` | two-band uint16 scene, 96×96 cells of 10 m |
| `output/Field_A_Healthy_Corn_ndvi.tif` | the index: one float32 band, nodata −9999 |
| `output/Field_B_Stressed_Wheat_scene.tif` | the stressed scene, same grid |
| `output/Field_B_Stressed_Wheat_ndvi.tif` | its index raster |
| `output/multi_field_ndvi.json` | written by the harness: means, counts, percentages |

## Notes

- The DN values are 0-10 000, not reflectance; NDVI is a ratio, so no conversion is
  needed before the division — only a cast to float32.
- A pixel whose two bands are both 0 has no signal. Writing an index of 0.0 there
  would claim bare soil, so the writer stores −9999 and the statistics skip it.
- The four classes tile [-1, 1] with the top band closed at 1.0, which is why the
  percentages add up to 100 instead of losing the pixels whose Red band clipped.
