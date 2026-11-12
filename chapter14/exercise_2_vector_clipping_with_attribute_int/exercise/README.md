# Exercise 2 — vector clipping without losing the attributes

## What it does

Builds four 10 × 10 degree counties (Alpha to Delta, 50 000 to 120 000 people),
clips them with a 10 × 10 degree ROI that overlaps the first two, and then checks
the result the way the exercise asks: it picks a clipped feature, finds the original
row with the same `County_Name`, and compares the non-spatial columns. The two
counties that reach the ROI keep 25 of their 100 square degrees and their original
populations; Gamma and Delta do not appear at all.

## The listings

| file | what it is |
| --- | --- |
| `01_vector_clip_attribute_integrity.py` | the listing: mock counties, the clip, the validation block, the GeoJSON |
| `run_attribute_integrity.py` | the harness: 25 assertions on the feature set, both areas, both populations and the file |

## Run it

```bash
cd chapter14/exercise_2_vector_clipping_with_attribute_int/exercise/files
python3 01_vector_clip_attribute_integrity.py
```

It prints the feature counts, the sampled feature's name and population, both
attribute checks and the name of the file it wrote; `run_attribute_integrity.py`
asserts that Alpha and Beta survive at 25 square degrees each, that Gamma and Delta
are absent, that the populations are the originals, and that the GeoJSON on disk
still holds both columns.

```text
--- Validation Check ---
Clipped features: 2 of 4
Clipped Feature Name: Alpha
Clipped Population: 50000
Attribute Integrity Check (Name): True
Attribute Integrity Check (Population): True
Validation Successful: Attributes were preserved during clipping.

Clipped GeoDataFrame saved to clipped_boundaries.geojson
```

## What it produces

| path | what it is |
| --- | --- |
| `output/clipped_boundaries.geojson` | the two clipped counties with both attribute columns |
| `output/attribute_integrity.json` | the kept and dropped names, both areas, both populations, the bounds |

## Notes

- `gpd.clip` intersects, so the geometry is replaced and the attributes are copied.
  The clipped area is 25 square degrees, not 100: measuring the clipped geometry
  gives the part inside the ROI, which is why the exercise insists on validating
  against the original row instead of re-deriving the attributes.
- The listing passes the ROI as a `GeoDataFrame`; `gpd.clip` accepts either that or
  a single geometry, and a one-row frame is the shape a reader will have after
  loading a GeoJSON.
- The GeoJSON is written to `output/`; the first version of this listing wrote
  `clipped_boundaries.geojson` into whatever directory it was started from.
