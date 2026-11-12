# Exercise 3 — the clip behind a command line

## What it does

Turns the clipping logic into a utility with three positional paths on `sys.argv`.
`parse_cli_args` counts the arguments, prints a usage line and exits 1 when the
count is wrong; the `FileNotFoundError` branches exit 1 with the missing path named;
`core_clip_logic` does the mask and reports the window it produced. Started with no
arguments at all, the same file builds a demo raster and mask under `output/` and
runs the utility on them, so the error paths and the working path are both
executable.

## The listings

| file | what it is |
| --- | --- |
| `01_cli_preprocessor.py` | the listing: argument parsing, the clip, the error branches, the demo pair |
| `run_cli_preprocessor.py` | the harness: 21 assertions across no arguments, two arguments and a missing file |

## Run it

```bash
cd chapter14/exercise_3_advanced_modification_challenge_co/exercise/files
python3 01_cli_preprocessor.py
```

With no arguments it writes a 200 × 200 px raster and a GeoJSON mask, then clips;
`run_cli_preprocessor.py` also runs it with two arguments (exit 1, usage message)
and with a path that does not exist (exit 1, `FATAL ERROR: Input file missing.`),
and asserts the 80 × 80 pixel output sits on the 2..6 degree mask.

```text
No arguments given; running the utility on the demo pair under output/.
Processing utility_input.tif using mask utility_mask.geojson...
SUCCESS: Raster clipped and saved to utility_clipped.tif
  200 x 200 px -> 80 x 80 px
  bounds (2.0, 2.0, 6.0, 6.0)
```

## What it produces

| path | what it is |
| --- | --- |
| `output/utility_input.tif` | the demo raster, 200 × 200 px over 0..10 degrees |
| `output/utility_mask.geojson` | the demo mask, the 2..6 degree square |
| `output/utility_clipped.tif` | the 80 × 80 px clip |
| `output/cli_preprocessor.json` | the three exit codes and the output window |

## Notes

- The zero-argument branch is what makes the listing runnable at all: the MATLAB-style
  contract in the book demands a use message for the wrong count, and a reader who
  runs the file bare should still see the clip work.
- Paths are printed as names. The utility echoes what the operator typed, but the
  demo writes into its own `output/`, and a README that quotes an absolute path
  prints this machine's username into the book.
- `nodata=src.nodata` carries the source's −9999 through the profile; a source with
  no NoData would raise here, which is the failure the `try/except`
  `rasterio.RasterioIOError` branch is there for.
