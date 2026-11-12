# Exercise 1 — the prompt, and where its solution lives

## What it does

Holds the code block the book prints as the exercise's starting point: two empty
function signatures, one for the new dimensions and one for the resample-and-write.
The task is to load a 1 m DEM, inspect its metadata and resample it to 10 m without
moving its footprint.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the prompt sketch, exactly as the exercise prints it — not a program |
| `../exercise_1/exercise/files/resample_dem.py` | the worked solution, one folder over |

## Run it

```bash
cd chapter13/exercise_1/exercise/files
python3 resample_dem.py
```

The sketch beside this README defines two functions that `pass`, so there is nothing
to run: the runnable version, its harness and the measured numbers live in the
sibling `exercise_1/` project. That harness asserts 31 facts — the new grid, the
preserved extent, the mean on both sides — and exits non-zero if any of them changes.

```text
# Required Python libraries and concepts:
import rasterio
import numpy as np
# Function to calculate new dimensions for resampling
def calculate_new_dims(original_width, original_height, scale_factor):
    # Logic to return new_width and new_height
    pass
```

## What it produces

Nothing. It is a prompt: the output belongs to the solution folder.

## Notes

- The sketch is the statement as printed in the book, kept as it stands so you can
  compare what you were given with the worked answer next door.
- This folder has no harness and no `output/`; `run_resample_dem.py` in the sibling
  folder is the grader.
