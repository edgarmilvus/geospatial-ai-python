# Exercise 5 — from a continuous index to four land-cover classes

## What it does

Thresholds a 100×100 index map into four integer classes with `np.select`, counts the
pixels in each with `np.unique(..., return_counts=True)`, prints an interpretation
drawn from the counts, and writes the class map as a single-byte GeoTIFF.

## The listings

| file | what it is |
| --- | --- |
| `classify_ndvi.py` | the solution: the four conditions, the counts, the raster |
| `run_classify_ndvi.py` | the harness: the boundary values, the blocks, the distribution |
| `prompt_sketch_exercise_5.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter12/exercise_5_interactive_challenge_translating/exercise/files
python3 classify_ndvi.py
```

It prints the class map's shape and dtype, the count and percentage of each class and
the interpretation, then writes the raster. `run_classify_ndvi.py` asserts 23 facts —
seven boundary values, the two forced blocks, about a fifth of the scene in class 0 —
and exits non-zero if any of them changes.

```text
Class 0 (Water/Cloud/No Data: Count: 2,100, Percentage: 21.00%)
Class 1 (Bare Soil/Urban: Count: 1,977, Percentage: 19.77%)
Class 2 (Sparse Vegetation: Count: 2,998, Percentage: 29.98%)
Class 3 (Dense Vegetation: Count: 2,925, Percentage: 29.25%)

Interpretation: Class 2 (Sparse Vegetation) dominates the scene, covering 29.98% of the total area.
```

## What it produces

| path | what it is |
| --- | --- |
| `output/vegetation_classes.tif` | the classes: one uint8 band, 255 reserved for unclassified |
| `output/ndvi_classes.json` | written by the harness: counts, percentages, boundaries |

## Notes

- The four conditions tile the whole real line, so `default=0` never fires; that is
  what makes the class counts add up to the pixel count.
- The thresholds are half-open `[low, high)` on purpose: a pixel at exactly 0.2 is
  sparse vegetation, not bare soil, and both readers and models need one answer.
- The conditions are built inside the function from the array it is handed. A version
  that closed over the module's own map would classify that map whatever it was given.
