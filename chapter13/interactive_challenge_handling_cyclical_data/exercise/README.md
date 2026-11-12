# Interactive challenge — aspect as a sine/cosine pair

## What it does

Turns a compass bearing into two continuous features, sin and cos of the aspect in
radians, so that 359° and 1° are close in the feature space instead of 358 apart. The
two new channels replace the single raw aspect channel in the stack.

## The listings

| file | what it is |
| --- | --- |
| `aspect_cyclic.py` | the solution: the transform, the distance demonstration, the stack |
| `run_aspect_cyclic.py` | the harness: the cardinals, the wrap distance, the unit circle |
| `prompt_sketch_challenge.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter13/interactive_challenge_handling_cyclical_data/exercise/files
python3 aspect_cyclic.py
```

It prints the raw aspect range, both transformed ranges, the new stack shape and the
distance between 359° and 1° as degrees against the same distance as points, then
writes the two channels. `run_aspect_cyclic.py` asserts 28 facts — the four cardinal
directions, 2·sin(1°) = 0.0349, the unit circle, no neighbour step above 0.05 — and
exits non-zero if any of them changes.

```text
--- Cyclical Aspect Transformation Summary ---
Original Aspect Range (Degrees): 0.0 to 360.0  (0-360, wrapping at north)
Aspect Sine Range: -0.8660 to 0.8660
Aspect Cosine Range: 0.5000 to 1.0000

New Feature Stack Shape (Channels, H, W): (4, 50, 50)

Distance between 359° and 1°:
  as degrees: 358
  as (sin, cos) pairs: 0.0349
Unit circle preserved: True
```

## What it produces

| path | what it is |
| --- | --- |
| `output/aspect_cyclical.tif` | two float32 bands: sine then cosine of aspect |
| `output/aspect_cyclic.json` | written by the harness: cardinals, wrap distance, ranges |

## Notes

- The pair (sin θ, cos θ) is a point on the unit circle. Two bearings that are close
  on the ground are close on the circle, whichever side of north they fall on.
- cos is the north-south component and sin the east-west one, so a model can recover
  the bearing with `atan2(sin, cos)` should it need the degrees back.
- The stack grows from three channels to four, and the raw aspect channel is gone: it
  is the one feature whose numerical order contradicted its physical order.
