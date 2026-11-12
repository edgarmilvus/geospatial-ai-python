# Exercise 2 — three hypotheses for one box, and the rule that picks

## What it does

Sends one bounding box at a wetland, receives three masks with different areas and scores,
selects the most confident one that clears an area floor, and closes the one-pixel dropouts
the segmenter left behind. It then shows what a higher floor and an unreachable floor do to
the same three candidates.

## The listings

| file | what it is |
| --- | --- |
| `mask_selection.py` | the solution: patch, three hypotheses, selection, closing |
| `run_mask_selection.py` | the harness: areas, nesting, floors, closing, IoU |

## Run it

```bash
cd chapter17/exercise_2_handling_ambiguity_with_bounding_b/exercise/files
python3 mask_selection.py
```

It prints the three hypotheses, the choice at a 6 000-pixel floor, the pixels closing filled,
the IoU against the land cover, and the two other floors. `run_mask_selection.py` asserts the
three areas, that the hypotheses are nested, that the 12 000 floor switches the winner, and
that closing adds exactly twelve pixels; it exits non-zero when the selection rule or the
refinement changes.

```text
Patch (256, 256, 3), the wetland is 11209 pixels (17.1% of the scene)

--- 3 hypotheses for one box prompt (stand-in) ---
  mask 0: confidence 0.94, area 10537 px
  mask 1: confidence 0.86, area 10881 px
  mask 2: confidence 0.72, area 14061 px

Selection with a 6000-pixel floor:
  eligible: [10537, 10881, 14061] -> picked confidence 0.94, 10537 pixels
Refinement: closing a 3 x 3 element filled 12 pixels (10537 -> 10549), one per dropout
IoU against the land cover truth: 0.9411
```

## What it produces

| path | what it is |
| --- | --- |
| `output/selected_mask.npy` | the refined boolean mask, 256 x 256 |
| `output/mask_selection.json` | the hypotheses, the three floors, the IoU |

## Notes

- The draft's three masks were hard-coded rectangles at 0.95 / 0.88 / 0.75 confidence, so the
  "selection logic" chose between numbers the file had written itself. Here the three masks
  come from the segmenter and are nested — object, margin, filled box — which is the ambiguity
  the exercise describes.
- A 3 x 3 structuring element closes a one-pixel hole and leaves a two-pixel one, so the
  dropouts are single pixels and the count is exact: twelve holes, twelve pixels filled. That
  is also the lesson about `binary_closing`: it is not `binary_fill_holes`.
- The 12 000 floor is where the exercise bites: it disqualifies the tight, most confident mask
  and hands the answer to the box-filling hypothesis at 0.72. A floor nothing reaches falls
  back to confidence with a warning instead of returning `None`.
- No SAM package, no weights, no network. About 0.2 s.
