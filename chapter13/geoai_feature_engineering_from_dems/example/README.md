# Advanced application script — a standardized terrain feature stack

## What it does

Derives slope, aspect and profile curvature from a DEM, standardizes each one with
`StandardScaler`, stacks the three into a channel-first array, writes a three-band
GeoTIFF for a model and a hillshade plus a PNG for a reader.

## The listings

| file | what it is |
| --- | --- |
| `terrain_feature_stack.py` | the listing: Horn's gradient, the curvature stencil, the stack |
| `run_terrain_feature_stack.py` | the harness: the estimators on known surfaces, the stack |

## Run it

```bash
cd chapter13/geoai_feature_engineering_from_dems/example/files
python3 terrain_feature_stack.py
```

It writes the DEM, reads it back, computes the three layers, standardizes them,
writes the stack, the hillshade and the overview figure, and prints the stack shape
and the range of each layer. `run_terrain_feature_stack.py` asserts 46 facts — the
compass convention of aspect on five planes, curvature sign on a dome and a bowl, the
analytic 15.31° bound on this surface — and exits non-zero if any of them changes.

```text
3. Calculating Slope, Aspect, and Profile Curvature...
4. Standardizing features using StandardScaler...
   -> Standardized slope. Shape: (128, 128)
   -> Standardized aspect. Shape: (128, 128)
   -> Standardized p_curvature. Shape: (128, 128)
5. Writing multi-band feature stack to terrain_feature_stack.tif...

Process Complete. The GeoAI feature stack is ready.
Output Feature Stack: terrain_feature_stack.tif | Bands: 3
Stack shape (channels, rows, cols): (3, 128, 128)

--- Terrain Summary ---
Elevation: 59.1 m to 169.8 m
Slope: 0.10° to 11.36° (mean 7.09°)
Aspect: 0.0° to 360.0°
Profile curvature: -0.01842 to 0.01809 (1/m)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/terrain_feature_stack.tif` | three float32 bands: standardized slope, aspect, curvature |
| `output/hillshade.tif` | the relief check: one band, azimuth 315, altitude 45 |
| `output/terrain_overview.png` | hillshade, slope and curvature side by side |
| `output/terrain_feature_stack.json` | written by the harness: bounds, means, signs |

## Notes

- **This listing replaces richDEM.** richDEM has no installable wheel on current
  Python, so slope and aspect come from Horn's 3×3 kernel and profile curvature from
  the Zevenbergen & Thorne 3×3 stencil — the estimators richDEM applies. The
  algorithms the chapter teaches are now visible in the file.
- Aspect is a compass bearing: 0° north, 90° east, clockwise. It is not standardized
  here because it is cyclical; the interactive challenge turns it into a sine/cosine
  pair instead.
- Profile curvature is positive on convex ground and negative in hollows, in units of
  1/metre — a much smaller number than slope, which is exactly why the standardization
  step exists.
