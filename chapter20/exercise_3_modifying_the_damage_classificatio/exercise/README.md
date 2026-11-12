# Exercise 3 — multi-temporal damage classification

## What it does

Extends the classifier from one pair of scenes to a time series: it computes NDVI
before and after, takes the change, and assigns each building a damage class from
the change and from whether the structure is still there. The NDVI numbers are the
argument, so the listing prints them.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_multitemporal.py` | the task statement: the multi-temporal change the classifier must handle |
| `01_multitemporal_damage.py` | the solution: the scenes, the index, the change, the classes |
| `run_multitemporal_damage.py` | the harness: the index values and the class counts |

## Run it

```bash
cd chapter20/exercise_3_modifying_the_damage_classificatio/exercise/files
python3 01_multitemporal_damage.py
```

It writes the two scenes and the results, printing the NDVI before, the NDVI after
for a damaged and an intact pixel, and the class summary. The harness asserts those
values — 0.600 before, −0.304 after on the damaged pixel against 0.500 on the intact
one, a change of 0.904 against 0.100 — and exits non-zero when a class boundary
moves.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/pre_disaster_scene.tif` | the before scene |
| `output/post_disaster_scene.tif` | the after scene |
| `output/multitemporal_results.txt` | the class summary as printed |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/multitemporal_damage.json` | both NDVI values, the changes and the counts |

## Notes

- The index is computed from the same two bands in both scenes, so the change is a
  change in the ground and not in the data.
- A negative post-disaster NDVI is not an error: water and rubble both return less
  near-infrared than vegetation did.
