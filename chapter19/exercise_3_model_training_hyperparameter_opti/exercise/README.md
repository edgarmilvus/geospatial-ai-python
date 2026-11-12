# Exercise 3 — training, the hyperparameter grid, the metrics

## What it does

Assembles two ST-Conv blocks and a per-node head, runs the grid the exercise asks
for (Chebyshev order, temporal kernel, hidden width), keeps the combination with the
lowest validation error, retrains it and reports MAE, RMSE and R^2 on the held-out
tail of the day — overall and for each of the three horizons separately.

## The listings

| file | what it is |
| --- | --- |
| `01_train_stgcn.py` | the solution: the day, the two blocks, the grid, the training loop, the figure |
| `run_train_stgcn.py` | the harness: the split, the loss curve, the metrics, the artefact |

## Run it

```bash
cd chapter19/exercise_3_model_training_hyperparameter_opti/exercise/files
python3 01_train_stgcn.py
```

It prints the eight grid results, the winning configuration, the loss of every epoch
of the final run, the metrics in km/h and the segmented error, then writes a figure
and a JSON record to `output/`. `run_train_stgcn.py` asserts that the training loss
falls monotonically, that R^2 on the test tail clears 0.5, that the model holds
6 435 parameters, and exits non-zero if any of those stops being true.

```text
Windows: 268 total | 160 train | 40 val | 68 test

Hyperparameter search (validation Huber loss after two epochs):
  K=2 Kt=3 F=8: val 0.7451
...
Best configuration: K=2, Kt=3, F=16 (val 0.5408)

Final training run:
  epoch  1: train 0.4039 | val 0.6640
...
--- Performance on the test tail (denormalized speed, km/h) ---
Overall MAE:  2.40 km/h
Overall RMSE: 3.09 km/h
Overall R2:   0.809

Segmented MAE by horizon:
  T+5 min MAE: 2.25 km/h
  T+10 min MAE: 2.15 km/h
  T+15 min MAE: 2.80 km/h
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/stgcn_training.png` | the loss curve and one link's actual against predicted speed |
| `output/stgcn_training.json` | the grid, the chosen configuration, both loss series, the metrics |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/stgcn_training_exercise.json` | the split, the loss series, MAE / RMSE / R^2, the parameter count |

## Notes

- The first version flattened every node and time step into one dense layer: 51 762
  parameters for 160 training windows. It learned the average speed of the training
  set and scored `R2 = -7.5`. The per-node head — one linear map on the last
  processed time step — is what turned the same blocks into a forecast.
- A layer-norm inside the block erases the speed level, because it normalizes each
  sample on its own; the level is exactly what is being predicted. The block now
  carries no normalization layer, and the inputs are standardized once, outside it.
- With the 70/15/25 split the test tail is the flat evening, where the speed varies
  by two or three km/h and R^2 is a harsh metric. The split here is 60/15/25 so the
  test tail contains the evening rush and the metric has something to explain.
- The validation loss bottoms out around the fifth epoch and then rises; the run
  still trains the full eight, and the harness treats that small gap as expected
  rather than as a failure.
