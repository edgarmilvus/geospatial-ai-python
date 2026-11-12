# Exercise 4 — the zero denominator, and why nodata is not 0.0

## What it does

Builds a 256×256 scene with a 10×10 block of no signal, computes the index twice —
once with `np.where` on a denominator mask, once with `errstate` plus `nan_to_num` —
and writes the masked result with −9999 as its nodata value.

## The listings

| file | what it is |
| --- | --- |
| `robust_ndvi.py` | the solution: both methods and the masked raster |
| `run_robust_ndvi.py` | the harness: the block, the NaN count, the agreement |
| `prompt_sketch_exercise_4.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter12/exercise_4_advanced_challenge_robustness_and/exercise/files
python3 robust_ndvi.py
```

It prints the index at the forced zero-sum pixel under both methods, the number of
pixels assigned nodata, whether the two agree, and the statistics of the valid cells.
`run_robust_ndvi.py` asserts 25 facts — 100 nodata pixels, no NaN, no Inf, identical
arrays — and exits non-zero if any of them changes.

```text
--- Robust NDVI Calculation (np.where) ---
NDVI value at forced zero sum area [105, 105]: -9999.0
Pixels assigned NODATA: 100
NaN values left in the map: 0
Inf values left in the map: 0

--- Alternative Method (Warning Suppression + nan_to_num) ---
Alternative NDVI value at forced zero sum area [105, 105]: -9999.0
Both methods agree pixel for pixel: True

--- Index Summary ---
Valid pixels: 65436 of 65536
NDVI Min: -0.8663
NDVI Max: 0.9260
NDVI Mean: 0.0719
```

## What it produces

| path | what it is |
| --- | --- |
| `output/ndvi_robust.tif` | the masked index: one float32 band, nodata −9999 |
| `output/robust_ndvi.json` | written by the harness: counts, range, agreement |

## Notes

- `0/0` is NaN and `X/0` is Inf; both propagate silently through every later
  statistic and turn a mean into NaN.
- The `np.where` version is the one to keep: it says which pixels are invalid, where
  `nan_to_num` only repairs the damage.
- The two blocks are not the same thing: the 100 forced pixels have no signal, while
  the other 65 436 have a real index — some negative, which is water, not error.
