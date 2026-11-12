# Exercise 2 — two slope estimators, compared

## What it does

Computes slope twice on the same 500×500 DEM: once with NumPy's central difference,
once with Horn's 3×3 kernel. Times both, compares them statistically with an RMSE, and
counts the cells where they disagree by more than a degree.

## The listings

| file | what it is |
| --- | --- |
| `slope_methods.py` | the solution: both estimators, the timing, the comparison |
| `run_slope_methods.py` | the harness: the planes where both are exact, the disagreement |
| `prompt_sketch_exercise_2.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter13/exercise_2_comparative_analysis_of_slope_calc/exercise/files
python3 slope_methods.py
```

It prints both wall-clock times, both mean slopes and standard deviations, the RMSE
between the methods and how many cells differ by more than 1° and 5°.
`run_slope_methods.py` asserts 23 facts — 45° on a grade-1 plane from both, agreement
to the last decimal in the interior, the central difference the noisier of the two —
and exits non-zero if any of them changes.

```text
--- Performance Comparison (Grid Size: (500, 500)) ---
NumPy Slope Time: 0.0028 seconds
Horn Slope Time: 0.0045 seconds
NumPy/Horn Time Ratio: 0.6x

--- Statistical Comparison (Slope in Degrees) ---
NumPy Mean Slope: 3.95, Std Dev: 1.87
Horn Mean Slope: 3.25, Std Dev: 1.31
Root Mean Square Error (RMSE) between methods: 1.4418
Maximum absolute difference: 10.1309
```

## What it produces

| path | what it is |
| --- | --- |
| `output/slope_methods.json` | written by the harness: both distributions, the RMSE, the timings |

## Notes

- **The richDEM column is Horn's kernel.** richDEM has no installable wheel here, so
  the second estimator is the algorithm it applies — eight weighted neighbours over
  eight cell widths — computed with `scipy.ndimage.correlate`. The comparison the
  exercise asks for survives; the claim that a library is faster does not.
- On this machine the two are the same order of magnitude, and the smooth estimator
  is the slower of the two. Wall-clock is machine-dependent, so it is recorded in the
  artefact and never asserted.
- On a plane both are exact, so any difference on the noisy DEM is the noise. The
  central difference reads one row of neighbours and passes noise through; Horn
  averages three rows and damps it. That is why its slope standard deviation is lower.
