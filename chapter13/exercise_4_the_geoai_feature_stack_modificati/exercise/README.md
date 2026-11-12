# Exercise 4 — adding curvature to the feature stack

## What it does

Derives four layers from a DEM — elevation, slope, aspect and profile curvature — with
a hill and a hollow in the scene, z-scores the three continuous ones, leaves aspect
raw, and stacks them as a four-channel array and a four-band GeoTIFF.

## The listings

| file | what it is |
| --- | --- |
| `feature_stack_curvature.py` | the solution: the curvature stencil, the scaler, the stack |
| `run_feature_stack.py` | the harness: A/σ² on the hill and the hollow, the four channels |
| `prompt_sketch_exercise_4.py` | the prompt sketch the book prints before it |

## Run it

```bash
cd chapter13/exercise_4_the_geoai_feature_stack_modificati/exercise/files
python3 feature_stack_curvature.py
```

It prints the stack shape, the channel order, the raw aspect range and the curvature
range before scaling, then writes the four-band raster. `run_feature_stack.py` asserts
34 facts — +0.0078 per metre on the hill, −0.0111 in the hollow, three channels with
mean 0 and deviation 1, aspect untouched — and exits non-zero if any of them changes.

```text
--- GeoAI Feature Stack Summary ---
Stack Shape: (4, 100, 100)
Feature Index Mapping:
[0]: Normalized Elevation
[1]: Normalized Slope
[2]: Raw Aspect (Degrees)
[3]: Normalized Profile Curvature
Aspect range kept raw: 0.1 to 359.9 degrees
Curvature before scaling: -0.04333 to 0.02080 1/m
```

## What it produces

| path | what it is |
| --- | --- |
| `output/advanced_feature_stack.tif` | four float32 bands, one per channel, 100×100 |
| `output/feature_stack_curvature.json` | written by the harness: signs, means, band order |

## Notes

- **Profile curvature comes from the 3×3 stencil, not richDEM.** The second derivatives
  are read with the Zevenbergen & Thorne kernels, projected onto the direction of
  steepest descent, and divided by (1 + |∇z|²)^1.5. Positive is convex, negative is a
  hollow — the distinction the exercise says a stack of elevation, slope and aspect
  cannot make.
- The analytic answer is available: at the centre of a Gaussian bump the curvature
  along the fall line is A/σ², so the hill reads +50/80² and the hollow −40/60².
- The outer ring of the curvature layer is the stencil's edge: there is no complete
  3×3 neighbourhood there, so those cells are the least trustworthy in the stack.
- Aspect is deliberately not standardized. It is cyclical, and the interactive
  challenge is what turns it into a sine/cosine pair.
