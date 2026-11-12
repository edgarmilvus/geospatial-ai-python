# Exercise 4 — three features, four sites, no rows lost

## What it does

Builds an enriched extraction-site layer in three moves: a 100 m buffer around the
sensitive area joined back as a boolean proximity flag, a concession assignment, and
the area of overlap between a 50 m buffer around each site and the sensitive area.
Site 1 is near the park, inside concession C1, and overlaps the park by almost the
whole 7 854 m² circle; site 3 is in concession C2 and nowhere near it; sites 2 and 4
get `NONE` and `0.0`.

## The listings

| file | what it is |
| --- | --- |
| `01_enriched_sites.py` | the solution: three features, aggregated back onto the original index |
| `run_enriched_sites.py` | the harness: the flag vector, the concession map, the overlap vector |
| `prompt_sketch_exercise_4.py` | the exercise's prompt fence, kept exactly as the book prints it |

## Run it

```bash
cd chapter3/exercise_4_advanced_geoai_feature_engineering/exercise/files
python3 01_enriched_sites.py
```

It prints the four sites with all three new columns, then the three counts; the
harness `run_enriched_sites.py` asserts four rows in the original order, the exact
flag and concession vectors and a 7 841–7 854 m² overlap for site 1, and exits non-zero
if a site without a match is dropped or shifted.

## What it produces

| path | what it is |
| --- | --- |
| `output/enriched_sites.json` | all three features per site id, plus the circle's closed-form area |

```text
 site_id extraction_type  is_near_sensitive_area concession_id  max_sensitive_overlap_sqm
       1           Legal                    True            C1                7841.371226
       2         Illegal                   False          NONE                   0.000000
       3           Legal                   False            C2                   0.000000
       4         Illegal                   False          NONE                   0.000000

Sites near the sensitive area: 1 of 4
Sites inside a concession: 2 of 4
```

## Notes

- The union of a 50 m buffer is a polygonised circle, so its area is 7 841.37 m²
  against the ideal π·50² = 7 853.98 m²; the harness accepts the range, not a constant.
- The overlay result is indexed by `site_id`, so it is aggregated and then *mapped*
  onto the original frame. Assigning the aggregate by position is the mistake this
  exercise is built to catch: sites with no overlap would take a neighbour's value.
- `left` joins plus `fillna` are what keep the two sites with no match in the answer,
  as `False`, `NONE` and `0.0` rather than as missing rows.
