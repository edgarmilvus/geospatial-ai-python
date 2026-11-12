# Exercise 1 — the prompt, and where its solution runs

## What it does

This folder holds the exercise's prompt fence exactly as the book prints it: the
reader's signature, its docstring and the `pass` the student replaces. It is
published as an `exercise` block by the extractor, so it keeps its own folder, but
it is not a program and is not harnessed.

The worked solution sits in the sibling folder `chapter11/exercise_1/`, because the
book's *Solutions and Explanations* heading is a bare `### Exercise 1` and the
extractor gives that heading its own slug.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_1.py` | the exercise's prompt fence, byte-identical to the book |
| `../exercise_1/exercise/files/metadata_deep_dive.py` | the solution: two scenes, the reader, the warning |
| `../exercise_1/exercise/files/run_metadata_deep_dive.py` | the harness: 21 assertions on the properties and branches |

## Run it

```bash
cd chapter11/exercise_1/exercise/files
python3 metadata_deep_dive.py
```

The prompt fence in this folder is a task description, not a program; the worked
solution and its harness live in the sibling folder, and this command runs them. The
harness exits non-zero if a property stops being reported, the one-band warning stops
firing, or a missing file raises instead of returning `None`.

## What it produces

| path | what it is |
| --- | --- |
| `../exercise_1/exercise/output/metadata_scene.tif` | the three-band scene the solution reads |
| `../exercise_1/exercise/output/single_band_scene.tif` | the scene that trips the warning |
| `../exercise_1/exercise/output/metadata_deep_dive.json` | the harness's measured properties |

## Notes

- The sketch is kept byte-identical so the book and the tree stay in step; editing it
  here would detach the block from its heading.
- A real solution to the five requirements is the sibling `metadata_deep_dive.py`,
  including the POLA branch the prompt asks for.
