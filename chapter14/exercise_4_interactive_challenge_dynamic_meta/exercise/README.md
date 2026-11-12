# Exercise 4 — filtering a raster profile with one comprehension

## What it does

The exercise publishes a clipping profile and the six keys a GeoAI pipeline needs,
and asks for one dictionary comprehension that keeps those keys and casts `width`
and `height` to `int`. The solution's input deliberately stores both dimensions as
floats — `1024.0` — so the cast is visible in the output, and four other keys
(`driver`, `nodata`, `is_tiled`, `interleave`) are dropped on the way through.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_4.py` | the exercise's own fence: the input profile and the expected structure |
| `02_clean_profile.py` | the solution: the target list, the comprehension, the printed result |
| `run_clean_profile.py` | the harness: 28 assertions on the six keys, both casts and the match with the prompt |

## Run it

```bash
cd chapter14/exercise_4_interactive_challenge_dynamic_meta/exercise/files
python3 02_clean_profile.py
```

It prints the filtered profile, with `width` and `height` as integers and no trace of
the four dropped keys; `run_clean_profile.py` asserts the key set, the `int` types,
the four untouched values, and that the dictionary equals the structure the
exercise's own fence publishes.

```text
{'count': 4,
 'crs': 'EPSG:32617',
 'dtype': 'uint16',
 'height': 1024,
 'transform': (10.0, 0.0, 500000.0, 0.0, -10.0, 100000.0),
 'width': 1024}
```

## What it produces

| path | what it is |
| --- | --- |
| `output/clean_profile.json` | the six keys, both types, the four dropped keys and the values |

## Notes

- Two fences, one folder: the extractor gives the exercise heading and the solution
  heading the same slug, so both blocks land here. The prompt fence is kept
  byte-identical and named `prompt_sketch_*`; it is a task description, not a
  program, and it is not harnessed.
- The comprehension runs over `input_profile.items()`, so the surviving keys keep
  the input order — `dtype` first, `transform` last — not the order of
  `TARGET_KEYS`. Both orders are correct; the harness compares sets, not sequences.
- `int(v)` on a float that is already integral is exact here. A profile carrying
  `1024.5` would be truncated rather than rounded, which is worth knowing before
  reusing this expression on a resampled raster.
