# Basic code example — NDVI from two reflectance bands

## What it does

Takes a 3×3 window of Red and Near-Infrared reflectance, computes the Normalized
Difference Vegetation Index element-wise, and writes the result as a one-band float32
GeoTIFF in a projected CRS, so the arithmetic ends in a georeferenced product.

## The listings

| file | what it is |
| --- | --- |
| `ndvi_band_math.py` | the listing: the two bands, the arithmetic, the GeoTIFF |
| `run_ndvi_band_math.py` | the harness: checks the index of known pixels, the range, the product |

## Run it

```bash
cd chapter12/basic_code_example_calculating_ndvi_with_nump/example/files
python3 ndvi_band_math.py
```

It prints the numerator, the denominator and the index for all nine pixels, then the
index range and the GeoTIFF profile. `run_ndvi_band_math.py` asserts 25 facts —
0.45/0.65 at the healthy corner, 0.10/0.80 at the mixed pixel, the [-1, 1] range, and
the single float32 band on disk — and exits non-zero if any of them changes.

```text
--- Final NDVI Map (Normalized Difference Vegetation Index) ---
[[0.6923077  0.6        0.6666666 ]
 [0.09090911 0.6883117  0.125     ]
 [0.6507936  0.6111111  0.6060606 ]]

Max NDVI recorded: 0.6923
Min NDVI recorded: 0.0909

--- GeoTIFF written ---
File: output/ndvi_basic.tif
Bands: 1 | dtype: float32 | nodata: -9999.0
CRS: EPSG:32610 | cell size: 10.0 m | grid: 3 x 3 px
```

## What it produces

| path | what it is |
| --- | --- |
| `output/ndvi_basic.tif` | the index: one float32 band, 3×3 cells of 10 m, EPSG:32610 |
| `output/ndvi_band_math.json` | written by the harness: three pixels, the range, the profile |

## Notes

- NDVI is a ratio of two reflectances, so it is scale-invariant: the same formula
  works on 0-1 reflectance and on 0-10 000 digital numbers.
- `float32` is not decoration. Integer division would truncate every value to 0.
- The 3×3 window has no zero denominator, which is why the listing divides directly;
  the robust version is exercise 4.
