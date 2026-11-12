# Exercise 3 — two windows, one difference, one binary map

## What it does

Takes an alert date and builds the two windows around it with `timedelta`: an
eighteen-month baseline that ends the day before the alert, and a six-month
monitoring window that starts on it. Both windows slice the same daily NDVI stack
with `.sel(time=slice(...))`, `.mean(dim='time')` reduces each to a 2D map, and the
difference of the two maps is thresholded at 0.3 to produce the boolean
deforestation map.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_3.py` | the exercise's prompt fence: the two signatures and the four steps |
| `02_baseline_monitoring.py` | the solution: the date arithmetic, both subsets, the difference and the threshold |
| `run_baseline_monitoring.py` | the harness: 20 assertions on the four dates, both spans and the pixel count |

## Run it

```bash
cd chapter15/exercise_3_defining_baseline_and_monitoring_p/exercise/files
python3 02_baseline_monitoring.py
```

It prints both windows and then the mean difference and the number of flagged
pixels; `run_baseline_monitoring.py` asserts that the two windows are contiguous,
that the baseline reaches back 18 months to 2021-05-02, that the monitoring slice
holds only the 61 days the record covers, and that all hundred pixels exceed the
threshold.

```text
Baseline: 2021-05-02 to 2022-10-31
Monitoring: 2022-11-01 to 2023-05-02

Delta NDVI Mean: 0.3615
Number of Deforestation Pixels: 100
```

## What it produces

| path | what it is |
| --- | --- |
| `output/time_windows.json` | both windows, their day counts and observation counts, the difference statistics |

## Notes

- The monitoring window is asked for six months, which ends on 2023-05-02, but the
  simulated record stops on 2022-12-31. The subset therefore holds 61 daily
  observations, not 183, and the difference is computed from what exists. A real
  pipeline would either extend the record or shorten the window; the harness asserts
  the 61 so the truncation cannot pass unnoticed.
- `timedelta` has no month unit, so the durations are `18 * 30.4375` and
  `6 * 30.4375` days — the average month. Subtracting from a `date` counts whole days
  only (547), so the baseline starts on 2 May, not on the calendar's 30 April;
  eighteen calendar months and 547 days are not the same window.
- The simulated drop is a multiplication by 0.4, which puts the cleared pixels at
  0.20–0.32 against a healthy 0.50–0.80. With the published 0.5 the difference lands
  at 0.30 and the 0.3 threshold becomes a coin toss; the harness asserts a saturated
  map, so the constant has to leave some margin.
