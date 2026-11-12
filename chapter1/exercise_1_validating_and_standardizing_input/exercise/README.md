# Exercise 1 — validating and standardising input CRS definitions

## What it does

One function accepts whatever a caller might hand it — an integer code, an `EPSG:`
string, a WKT definition, or nonsense — and either returns an integer EPSG code or
raises the exercise's own `InvalidCRSDefinitionError`. The point is the contract:
callers catch one exception type, not pyproj's three.

## The listings

| file | what it is |
| --- | --- |
| `01_crs_validation.py` | the solution: parser, validator and four test inputs |
| `run_crs_validation.py` | the harness: drives all four inputs and the two refusals |

## Run it

```bash
cd chapter1/exercise_1_validating_and_standardizing_input/exercise/files
python3 01_crs_validation.py
```

It parses four inputs and prints the EPSG code for each one it accepts, then the
message for each one it rejects. `run_crs_validation.py` asserts the accepted codes,
asserts that `None` and `WGS 84 ZONEX` raise the exercise's exception and not a
`TypeError`, and exits non-zero when any of them changes shape.

```text
--- Processing Input: 4326 (int) ---
Standardized EPSG Code: 4326

--- Processing Input: EPSG:3857 (str) ---
Standardized EPSG Code: 3857
...

--- Processing Input: WGS 84 ZONEX (str) ---
Error Caught: Failed to parse CRS input 'WGS 84 ZONEX'. ...
```

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/crs_validation.json` | the three accepted inputs and the two rejected ones |

## Notes

- The WKT input is a whole CRS definition, not a fragment: a truncated one fails to
  parse, and the listing would then be demonstrating the wrong thing.
- No network; `pyproj.CRS.from_user_input` reads the local PROJ database.
- The rejected inputs are part of the exercise, so they print as errors on a run
  that succeeded.
