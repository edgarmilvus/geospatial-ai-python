# Exercise 4 — read one band, refuse the rest

## What it does

Writes a four-band 200 x 150 scene whose bands have deliberately different ranges
(band 2 lives between 200 and 599), then reads a band chosen by the caller. Text is
refused as a format error, a number outside 1-4 is refused with the valid range in
the message, and a run with no terminal reads band 1 and says so instead of blocking
on `input()`.

## The listings

| file | what it is |
| --- | --- |
| `band_selection_reader.py` | the solution: scene writer, `parse_band_choice`, `interactive_band_reader` |
| `run_band_selection.py` | the harness: band 2's values, both errors, the default |
| `prompt_sketch_exercise_4.py` | the exercise's prompt fence, as the book prints it |

## Run it

```bash
cd chapter11/exercise_4_interactive_band_selection_and_err/exercise/files
python3 band_selection_reader.py
```

It writes `output/band_selection_scene.tif` and exercises four answers — `2`,
`"NIR"`, `9`, and no answer at all. `run_band_selection.py` compares band 2 against
the source, checks both error messages and the non-interactive default, and exits
non-zero when a bad answer reads a band or the prompt starts waiting.

```text
--- Wrote band_selection_scene.tif: 200 x 150, 4 bands ---
The dataset has 4 bands (1-indexed).

--- Band Reading Successful ---
Band 2 loaded.
Array Shape (H, W): (150, 200)
Minimum Pixel Value: 200
Maximum Pixel Value: 599

The dataset has 4 bands (1-indexed).
ERROR: Invalid input format. Please enter a whole number (integer).

The dataset has 4 bands (1-indexed).
ERROR: Band number 9 is out of range. Please enter an integer between 1 and 4.

The dataset has 4 bands (1-indexed).
No terminal attached: reading band 1.
```

## What it produces

| path | what it is |
| --- | --- |
| `output/band_selection_scene.tif` | the four-band source with distinct ranges |
| `output/band_selection.json` | the valid read, both errors, both band ranges |

## Notes

- A single band reads as `(height, width)`, not `(1, height, width)`: the band axis
  disappears when the selection is one index. The harness asserts the 2-D shape.
- `parse_band_choice` returns `(index, error)` with exactly one of the two set. That
  keeps validation testable without a terminal and keeps the reader's loop readable.
- The prompt is guarded by `sys.stdin.isatty()`. Under `run_offline.sh` stdin is not
  a terminal, so the reader takes the documented default; a reader at a keyboard
  still gets asked.
