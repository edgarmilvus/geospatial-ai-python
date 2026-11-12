# Exercise 4 — complex feature aggregation and area filtering

## What it does

Aggregates three fragmented land-cover patches into one feature with `union_all()`: two
100-unit squares that overlap in a 25-unit square merge into a 175-unit blob, and the isolated
100-unit patch 200 units away keeps its own ring. The union is therefore a `MultiPolygon` of
275 square units, which clears the 150-unit ecological threshold and is kept.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_feature_aggregation.py` | the task statement: three patches and the area threshold |
| `01_feature_aggregation.py` | the listing: the three patches, the union, the threshold branch |
| `run_feature_aggregation.py` | the harness: parts, overlap, union area, geometry type |

## Run it

```bash
cd chapter4/exercise_4_complex_feature_aggregation_and_ar/exercise/files
python3 01_feature_aggregation.py
```

It prints the aggregated area, the threshold, the verdict and the resulting geometry type.
`run_feature_aggregation.py` asserts the 25-unit overlap, the 175 + 100 decomposition of the
union, that the union is a two-part `MultiPolygon`, and that the threshold branch includes the
feature; it exits non-zero when any of them changes.

```text
--- Feature Aggregation and Filtering ---
Total Area of Aggregated Feature: 275.00 sq units
Minimum Required Area Threshold: 150.00 sq units
STATUS: INCLUDED in Final Analysis Layer.
Final Feature Type: MultiPolygon
```

## What it produces

| path | what it is |
| --- | --- |
| `output/feature_aggregation.json` | patch areas, overlap, union area, parts, threshold, verdict |

## Notes

- The book's first version of this listing labelled the third patch "Area 10" and predicted a
  total of 185. The patch is a 10 × 10 square, so it is 100 units and the total is 275 — the
  code was right and both comments were wrong. The comments are corrected here.
- The union is not `sum(areas)`: 300 − 25 = 275. Aggregation is where a GeoAI pipeline stops
  double-counting overlapping detections, and the arithmetic is the check that it worked.
- The threshold is a domain choice, not a geometric one: 150 units is "big enough to matter
  to the ecological model", which is why it is a named constant.
