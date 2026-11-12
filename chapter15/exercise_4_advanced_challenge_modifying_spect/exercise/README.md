# Exercise 4 — merging a configuration with `dict.update`

## What it does

Defines a default configuration for a spectral-trajectory model and a second
dictionary of degradation parameters, then merges the second into the first with
`dict.update`. The merge overwrites `stability_threshold_ndvi` (0.15 → 0.075) and
`include_evi_check` (False → True), adds `stat_test_method`, and leaves
`min_observations`, `fit_method` and `p_value_threshold` exactly as they were. The
placeholder model then reports what it was handed.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_4.py` | the exercise's prompt fence: the two dictionaries and the model stub |
| `02_config_merge.py` | the solution: both dictionaries, the merge, the printed result and the model call |
| `run_config_merge.py` | the harness: 16 assertions on the overwrite, the addition and the untouched keys |

## Run it

```bash
cd chapter15/exercise_4_advanced_challenge_modifying_spect/exercise/files
python3 02_config_merge.py
```

It prints the threshold before the merge, the six merged keys and the placeholder
model's view of them; `run_config_merge.py` asserts that the threshold is exactly
half its default, that the EVI flag is on, that the new statistical test is present,
and that the three keys the custom dictionary never mentions survive unchanged.

```text
Initial Default NDVI Threshold: 0.15

--- Final Merged Configuration ---
stability_threshold_ndvi: 0.075
min_observations: 12
fit_method: harmonic_regression
p_value_threshold: 0.05
include_evi_check: True
stat_test_method: t_test_modified

--- GeoChangeModel Execution Simulation ---
Model initialized using fitting method: harmonic_regression
Change detected if NDVI deviation exceeds: 0.075
EVI Check Status: Enabled
```

## What it produces

| path | what it is |
| --- | --- |
| `output/config_merge.json` | both key sets, the union, the threshold before and after, the untouched keys |

## Notes

- `dict.update` mutates and returns `None`, so the merged configuration is
  `default_config` itself; there is no new object to pass around. That is why the
  listing prints the threshold *before* the merge — afterwards the original value is
  gone.
- `include_evi_check` exists in the solution's default as `False`. The prompt's
  sketch omits it entirely, which turns the merge's `True` into an addition rather
  than an overwrite; both readings satisfy "incorporate EVI", and the harness accepts
  the addition by checking the merged key, not the default's key set.
- Merging is shallow. A nested dictionary under a key the custom dictionary also sets
  would be replaced wholesale, not merged key by key — worth knowing before this
  pattern is applied to a deeper model configuration.
