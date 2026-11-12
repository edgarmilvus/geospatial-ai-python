# Exercise 5 — a batch that keeps each tile's own georeference

## What it does

Processes three 100 x 100 tiles with one box prompt each, writes every mask back as a
GeoTIFF carrying *that tile's* transform and CRS, and merges the three into one mosaic. A
fourth tile in the batch does not exist, and the loop skips it with a message instead of
ending the run.

## The listings

| file | what it is |
| --- | --- |
| `batch_mosaic.py` | the solution: tiles, batch loop, per-tile mask, merge |
| `run_batch_mosaic.py` | the harness: per-mask origins, mosaic grid, skip |

## Run it

```bash
cd chapter17/exercise_5_batch_processing_and_metadata_alig/exercise/files
python3 batch_mosaic.py
```

It writes the tiles, segments and georeferences each one, skips the missing tile, and merges
into `output/mosaic.tif`, printing each tile's origin and the mosaic's size. `run_batch_mosaic.py`
asserts that the second mask carries easting 300 100 and the third northing 4 500 100, that
the mosaic is 200 x 200 with 3 600 building pixels, and that the skip is announced; it exits
non-zero when a mask inherits another tile's transform.

```text
Processing tile 1: tile_01.tif
  Metadata: CRS=EPSG:32618, origin=(300000, 4500200)
  Predicted 1200 pixels at score 0.93
  Wrote mask_tile_01.tif
...
Processing tile 4: tile_404.tif
  FATAL ERROR: cannot read tile_404.tif; skipping (RasterioIOError).

==================================================
Batch complete: 3 masks, 1 tile(s) skipped
Merged 3 masks into mosaic.tif: 200 x 200, 3600 building pixels
Mosaic origin: (300000, 4500200), pixel 1 m
```

## What it produces

| path | what it is |
| --- | --- |
| `output/tiles/tile_0{1,2,3}.tif` | the three 100 x 100 three-band input tiles |
| `output/processed_masks/mask_tile_0{1,2,3}.tif` | one uint8 mask per tile, each with its tile's metadata |
| `output/mosaic.tif` | the merged 200 x 200 mask, EPSG:32618 |
| `output/batch_mosaic.json` | the per-mask pixel counts and the mosaic's grid |

## Notes

- The draft's "stitching preparation" was three `print` statements; nothing was merged, so a
  wrong transform in any mask would never have shown. Here `rasterio.merge` runs, and the
  mosaic's 200 x 200 extent is the proof that the three tiles were placed on one grid.
- The tiles are laid out on exact 100 m boundaries — (300 000, 4 500 200), (300 100, 4 500 200),
  (300 000, 4 500 100) — because a merge of tiles offset by 500 m at 1 m pixels would still
  succeed and still be unreadable.
- The error branch catches `RasterioIOError`, prints the file name and the exception class,
  and continues. Rasterio's own message repeats the absolute path, so it is not printed: a
  book's terminal output should not carry the reader's home directory.
- The masks directory is cleared at the start of every run; a stale `mask_tile_04.tif` from an
  older batch would otherwise merge into the mosaic.
- Needs `rasterio` and `scipy`; no SAM package, no weights, no network. About 0.2 s.
