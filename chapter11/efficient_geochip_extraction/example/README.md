# Example 2 — one 256-pixel chip from a 1024-pixel scene

## What it does

Writes a four-band 1024 x 1024 scene in UTM zone 17N at 10 m resolution, opens it,
computes the window that centres a 256-pixel chip, derives that window's own affine
transform, and reads three bands through it. The scene is deterministic, so the
chip's mean is the same on every run.

## The listings

| file | what it is |
| --- | --- |
| `geochip_extraction.py` | the listing: scene generator, windowed read, verification |
| `run_geochip.py` | the harness: window offsets, chip transform, exact pixel equality |

## Run it

```bash
cd chapter11/efficient_geochip_extraction/example/files
python3 geochip_extraction.py
```

It writes `output/large_satellite_scene.tif` on the first run and reuses it after,
reads the centred chip and prints its shape, its mean and its transform.
`run_geochip.py` re-reads the same window and compares the pixels exactly, checks
the chip's origin is the scene's origin moved by 384 x 10 m, and exits non-zero when
the window, the band order or the transform moves.

```text
Creating dummy file: large_satellite_scene.tif...
Dummy file created successfully at large_satellite_scene.tif.

--- Starting GeoChip Extraction Process ---
Source Dimensions: W=1024, H=1024
Coordinate Reference System (CRS): EPSG:32617
Affine Transform (Top-Left Corner, Resolution): | 10.00, 0.00, 500000.00|
| 0.00,-10.00, 4500000.00|
| 0.00, 0.00, 1.00|
Number of Bands: 4
Data Type: uint16

Defined Extraction Window: Window(col_off=384, row_off=384, width=256, height=256)

Extraction successful. Chip Shape: (3, 256, 256)
Mean Pixel Value (Validation): 1001.18

--- Final Output Verification ---
Final Chip Data Shape (Bands, H, W): (3, 256, 256)
Chip's Affine Transform: | 10.00, 0.00, 503840.00|
| 0.00,-10.00, 4496160.00|
| 0.00, 0.00, 1.00|
Verification successful: Chip shape matches expected dimensions.
```

## What it produces

| path | what it is |
| --- | --- |
| `output/large_satellite_scene.tif` | the 1024 x 1024 x 4 scene, 8 MB |
| `output/geochip.json` | window, chip shape, per-band means, chip transform |

## Notes

- The scene is 1024 rather than 4096: the exercise is about the windowed read, and a
  4096 x 4096 x 4 file is 134 MB of random pixels that takes longer to write than
  the chapter takes to read. The window arithmetic and the transform are identical.
- Each band is drawn from its own seeded generator (`100 + band`), so a second run
  of the file skips creation and still produces the same chip. The unseeded version
  changed the mean on every run.
- `DatasetReader` has `dtypes[0]`, not `dtype`. The book's line `src.dtype` raises
  `AttributeError` on rasterio 1.4 and stopped the read before the window was
  reached; both references now use `dtypes[0]`.
- The chip's transform is `src.window_transform(window)`, not the scene's
  transform: the origin moves to `(503840, 4496160)` while the pixel size and the
  CRS stay put.
