# Interactive challenge — the optimal geo-fence (task statement)

## What it does

This folder holds the challenge, not its answer: a six-vertex building covering exactly
50 000 m², two utility access points at 400/150 and 50/450, and the two buffer distances the
design must honour — 50 m around the building, 20 m around each point. The harness checks that
the inputs are the documented ones, that the starter has buffered nothing yet, and computes the
numbers a correct answer has to reach: 102 669.71 m² inside a 1 369.91 m boundary.

## The listings

| file | what it is |
| --- | --- |
| `01_geofence_spec.py` | the starter block: three features, two distances, no answer |
| `run_geofence_spec.py` | the harness: the inputs, and the target metrics to grade against |

## Run it

```bash
cd chapter4/interactive_challenge_the_optimal_geo_fence_d/exercise/files
python3 run_geofence_spec.py
```

The starter defines its geometry and prints nothing, so the harness is the thing to run: it
checks the six vertices, the 50 000 m² area, both access points and both buffer distances, then
derives the target area and perimeter from them. It exits non-zero when an input changes or
when the target no longer matches the solution printed in the chapter.

```text
ok      interactive challenge (geo-fence, task statement) — 19 assertions passed
```

## What it produces

| path | what it is |
| --- | --- |
| `output/geofence_spec.json` | vertices, building area, both buffers, target area/perimeter/type |

## Notes

- The fence lands on two parts, not three: access point 1 stands 67.08 m from the wall and the
  two buffers add up to 70 m, so that disc merges with the building fence. A grading rule that
  expected three rings would fail a correct answer.
- Containment is tested by area — unioning the fence with each buffer must add nothing —
  because a buffer that was used to build the union shares its boundary and `contains` returns
  `False` for it even though every square metre is inside.
- The answer to this challenge is published in
  `chapter4/exercise_5_interactive_challenge_the_optimal/exercise/`; the two harnesses agree on
  102 669.71 m² and 1 369.91 m, which is what makes the challenge gradeable.
