# Basic code example — slope in degrees from a DEM

## What it does

Builds a 100×100 synthetic DEM — a gentle 4.09° ramp with a Gaussian hill near the
centre — takes the gradient in metres per metre, combines the two partial derivatives
into a tangent, and converts it to degrees. The slope is then written as a one-band
float32 GeoTIFF in a projected CRS.

## The listings

| file | what it is |
| --- | --- |
| `slope_from_dem.py` | the listing: the DEM, the gradient, the degrees, the raster |
| `run_slope_from_dem.py` | the harness: known surfaces, the cell-size pitfall, the product |

## Run it

```bash
cd chapter13/basic_code_example_calculating_terrain_slope/example/files
python3 slope_from_dem.py
```

It prints the grid, the resolution, the elevation range, the steepest and mean slope
and the ramp's own slope, then writes the raster and reports its profile.
`run_slope_from_dem.py` asserts 30 facts — a grade-1 plane is 45°, a cone of height
equal to its radius is 45° on its flanks, dropping the cell size inflates every
tangent tenfold — and exits non-zero if any of them changes.

```text
--- Digital Elevation Model (DEM) Analysis ---
Input Grid Shape: (100, 100)
Resolution (Meters/Pixel): 10.0
---------------------------------------------
Maximum Elevation: 100.00 m
Minimum Elevation: 0.00 m
---------------------------------------------
Maximum Calculated Slope: 34.82° (Found at the peak)
Average Calculated Slope: 4.26°
Slope on the flat ramp: 4.09°
---------------------------------------------
Slope written to: output/slope_degrees.tif
Product: 1 band | float32 | nodata -9999 | crs EPSG:32610 | cell 10.0 m
```

## What it produces

| path | what it is |
| --- | --- |
| `output/slope_degrees.tif` | the slope: one float32 band, 100×100 cells of 10 m, EPSG:32610 |
| `output/slope_from_dem.json` | written by the harness: known-surface answers, the pitfall ratio |

## Notes

- The ramp rises 50 m across 99 cells of 10 m, which is 0.0505 m per metre on each
  axis and 4.09° in combination — not the 45° a reader might expect from "a ramp".
  The harness computes that number from the construction, not from the run.
- `np.gradient(DEM, CELL_SIZE)` is the whole chapter in one argument: without it the
  derivative is per pixel index, and on a 10 m grid every tangent is ten times too
  big.
- The CRS is EPSG:32610, not EPSG:4326: a 10 m cell is a linear unit, and a 10
  *degree* cell would make the slope meaningless.
