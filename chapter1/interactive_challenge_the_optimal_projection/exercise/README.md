# Interactive challenge — the optimal projection selector

## What it does

Turns projection choice into a decision table: a measurement goal and a location
go in, an EPSG code and a one-sentence justification come out. Distance asks for the
local UTM zone, area asks for an equal-area projection — Conus Albers inside the
contiguous United States, Equal Earth everywhere else — and mapping always asks for
Web Mercator.

## The listings

| file | what it is |
| --- | --- |
| `01_projection_selector.py` | the solution: `recommend_crs`, the zone helper, two test cases |
| `run_projection_selector.py` | the harness: drives every branch, including the refusals |

## Run it

```bash
cd chapter1/interactive_challenge_the_optimal_projection/exercise/files
python3 01_projection_selector.py
```

It runs two test cases and prints the recommendation and its justification for each.
`run_projection_selector.py` drives all four outcomes plus an unknown goal, checks
that the goal is case-insensitive, and exits non-zero if a branch starts returning a
plausible code instead of refusing.

```text
--- Running Test Case 1: Chicago (Distance) ---
Input Location: (41.88°N, 87.63°W)
Measurement Goal: DISTANCE
Recommended EPSG Code: 32616
...
Recommended EPSG Code: 6933
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/projection_choices.json` | one code per goal, both hemispheres, and the refusal |

## Notes

- The hemisphere letters follow the sign of the coordinate; printing `°N` for a
  negative latitude is the formatting bug this listing first shipped with.
- No network and no data files: the whole table is arithmetic plus three constants.
