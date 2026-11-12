# Exercise 4 — every sparse prompt dictionary, and no KeyError

## What it does

Turns a user dictionary of optional prompt types into keyword arguments for `predict`,
reading each key with `dict.get` so a missing one is an omission and not an exception. It
runs all eight subsets of the three keys, unpacks each result into a real predictor call, and
refuses a box or a point that is the wrong shape.

## The listings

| file | what it is |
| --- | --- |
| `prompt_router.py` | the solution: extraction, stand-in, four demo cases |
| `run_prompt_router.py` | the harness: all eight subsets, labels, refusals, masks |

## Run it

```bash
cd chapter17/exercise_4_interactive_challenge_robust_promp/exercise/files
python3 prompt_router.py
```

It prints the raw dictionary and the structured arguments for four cases, then the mask area
each one produced, then the refusal for a three-number box. `run_prompt_router.py` asserts
that every subset yields exactly the arguments it has data for, that positives come before
negatives in the label vector, and that malformed values raise; it exits non-zero when a
missing key becomes an exception.

```text
=== Test case: full ===
Raw input dict: {'positive_points': [(85, 45)], 'bounding_box': [60, 20, 110, 70], 'negative_points': [(10, 10)]}
Structured SAM args: {'point_coords': [[85.0, 45.0], [10.0, 10.0]], 'point_labels': [1, 0], 'box': [60.0, 20.0, 110.0, 70.0]}
mask area: 900 pixels, score 0.95
...
[REFUSED] a box needs four numbers, got [10, 10, 200]

Keys accepted by the four cases:
  full           ['box', 'point_coords', 'point_labels']
  sparse         ['point_coords', 'point_labels']
  negative_only  ['point_coords', 'point_labels']
  empty          []
```

## What it produces

| path | what it is |
| --- | --- |
| `output/prompt_router.json` | the four cases, their keys, areas and the refusals |

## Notes

- The draft concatenated `positive_points + negative_points` and built labels in the same
  order, which is right — but it did it with lists, so a caller passing a tuple or a NumPy
  array got a `TypeError` before the `KeyError` it was defending against. The listing
  converts both to lists first.
- A box of three numbers was silently dropped by the draft (`len(bounding_box) == 4` guarded
  the append). A dialog that sends a half-dragged box would then get an unprompted
  "everything" segmentation and no diagnostic; here it raises.
- The empty dictionary is the interesting case: it produces `{}`, which unpacks into
  `predict()` and returns the whole bright region. That is the stand-in's "everything mode",
  and it is why the harness only asserts that the call succeeds with no arguments.
- All eight subsets are exercised, including the three single-key ones. About 0.2 s.
