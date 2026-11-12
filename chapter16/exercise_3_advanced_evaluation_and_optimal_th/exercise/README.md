# Exercise 3 — the threshold that maximises F1, found by sweeping

## What it does

Scores one probability map at seventeen thresholds from 0.10 to 0.90, counting true and
false positives by hand, and returns the threshold with the best F1. The map is simulated
around two different means with wide overlap, so no threshold is free and the answer is not
0.50.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_3.py` | the book's required structure, bodies left as `pass` |
| `threshold_optimization.py` | the solution: simulator, metrics, sweep, table |
| `run_threshold_optimization.py` | the harness: counts, curves, sklearn cross-check |

## Run it

```bash
cd chapter16/exercise_3_advanced_evaluation_and_optimal_th/exercise/files
python3 threshold_optimization.py
```

It prints the seventeen-row table, the F1 at the default threshold, the optimum and its
counts, then the same F1 from sklearn. `run_threshold_optimization.py` asserts the counts
behind every number, that precision only rises and recall only falls as the threshold
grows, and that the peak is interior; it exits non-zero when the sweep or the arithmetic
changes.

```text
threshold  precision  recall      f1       tp      fp      fn
     0.50      0.521   0.884   0.656    1750    1606     229
     0.55      0.714   0.771   0.741    1525     610     454
     0.60      0.850   0.597   0.701    1181     208     798
...
F1 at the default 0.50: 0.656 (precision 0.521, recall 0.884)
Optimal Threshold: 0.55
Max F1 Score: 0.741
At the optimum: precision 0.714, recall 0.771, 1525 TP / 610 FP / 454 FN
sklearn f1_score at the optimum: 0.741
```

## What it produces

| path | what it is |
| --- | --- |
| `output/threshold_optimization.json` | the three curves, the optimum and its counts |

## Notes

- The draft simulated `np.random.rand` predictions against `np.random.randint` targets, so
  the "expected output" of 0.65 and 0.891 in the book was a comment, not a result. Here the
  probability map has a signal: 1 979 roof pixels of 16 384, drawn from a normal around
  0.62 on roofs and 0.38 elsewhere.
- The sweep finds 0.55, not 0.50: the default costs 0.085 F1. That is the lesson, and it
  only holds because the two distributions overlap.
- `calculate_metrics` returns TP, FP and FN as well as the three scores, and the harness
  checks them against sklearn. A utility that agrees with the library on F1 but not on the
  counts is measuring something else.
- Seeded (`np.random.default_rng(11)`), no torch, under a second.
