# Exercise 1 — the arithmetic core of NDVI on a 5×5 window

## What it does

Computes the numerator, the denominator and the index for a 5×5 patch of Red and NIR
digital numbers, with no loop, no library beyond NumPy, and a printed denominator so
a division by zero would be visible before it happened.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise statement, exactly as the book prints it |
| `ndvi_arithmetic_core.py` | the solution: the two arrays, the element-wise arithmetic |
| `run_ndvi_arithmetic.py` | the harness: three pixels by hand, the dtype, the range |

## Run it

```bash
cd chapter12/exercise_1_isolating_the_arithmetic_core_calc/exercise/files
python3 ndvi_arithmetic_core.py
```

It prints the denominator grid, then the dtype, shape, minimum and maximum of the
index and the index itself. `run_ndvi_arithmetic.py` asserts 21 facts — 400/600 at
(0,0), 500/980 at (4,2), 940 at the (2,2) denominator, all 25 pixels vegetated — and
exits non-zero if any of them changes.

```text
--- NDVI Verification ---
NDVI Data Type: float32
NDVI Shape: (5, 5)
NDVI Minimum Value: 0.5102
NDVI Maximum Value: 0.6667
Values inside [-1, 1]: True
Pixels computed: 25 (no explicit loop)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/ndvi_arithmetic.json` | written by the harness: three pixels, the range, the mean |

## Notes

- The exercise asks for `float32` output; `nir_band - red_band` on two float32
  arrays already is, so the cast is a check rather than a conversion.
- Every pixel in this window has NIR above Red, so the whole patch is vegetated and
  the minimum is still positive. A water pixel, with Red above NIR, is the case the
  harness adds to prove the formula's sign.
- The denominator is the array worth printing: the moment a cell of it is zero, the
  index of that cell is undefined and exercise 4 is waiting.
