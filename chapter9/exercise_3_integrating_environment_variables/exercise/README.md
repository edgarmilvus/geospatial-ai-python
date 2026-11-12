# Exercise 3 — the feed comes from the environment, the bandwidth from N

## What it does

Reads the input path from `GEOAI_DATA_PATH`, falls back to a generated default when the
variable is unset, cleans whatever it read, and then sets the KDE bandwidth from the sample
size with Silverman's `h = C · N^(-1/5)`. The bandwidth is not printed and forgotten: it is
what `gaussian_kde` is given, converted into scipy's factor units.

## The listings

| file | what it is |
| --- | --- |
| `bandwidth_from_env.py` | the solution: the environment branch, the heuristic, a real KDE |
| `run_bandwidth_env.py` | the harness: both branches, two sample sizes, two bandwidths |

## Run it

```bash
cd chapter9/exercise_3_integrating_environment_variables/exercise/files
python3 bandwidth_from_env.py
```

The first run warns that the variable is unset and uses `output/default_traffic.csv`, which
it generates if missing; the second reads the named feed. Both print the valid count, the
bandwidth, the factor scipy received and the grid the density was evaluated on.
`run_bandwidth_env.py` drives both branches and checks that the bandwidth follows N (22
assertions); it exits non-zero if a smaller sample stops earning a wider bandwidth.

```text
WARNING: GEOAI_DATA_PATH environment variable not set. Using default path: output/default_traffic.csv

KDE evaluated on a 120x120 grid; peak density 235.72 at 34.0505 N, -118.2394 E.

--- Configuration Summary ---
Final used file path: output/default_traffic.csv
Total valid data points (N): 8000
Calculated Dynamic Bandwidth (h): 0.016572 degrees
Bandwidth applied as bw_method: 0.8260 (sample spread 0.0201 degrees)
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/default_traffic.csv` | the fallback feed, generated once and then reused |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/fixture_traffic.csv` | a 500-row feed with five bad rows, for the configured branch |
| `output/bandwidth_env.json` | both branches: path, N, bandwidth, factor, peak |

## Notes

- The listing reads `GEOAI_DATA_PATH` when it is set and otherwise writes and reads its
  own fixture, printing which path it used. Export the variable to point it at a feed of
  your own; the run above needs neither.

- The book's default path `./data/default_traffic.csv` does not exist and is never created,
  so the "graceful" branch raises `FileNotFoundError` and calls `exit()` — which is the
  `site` helper, and exits with status 0, the code for success.
- `exit()` is replaced by a `SystemExit` with a message. A missing feed somebody named in the
  environment is a deployment error; inventing data for it would hide that. Only the
  *default* feed is generated, because that one is this project's own fixture.
- The heuristic: `h = 0.1 · N^(-1/5)`. For 8 000 pings that is 0.0166 degrees; for 500 it is
  0.0288. Smaller sample, wider bandwidth — the bias-variance trade the chapter argues.
- The book computes `dynamic_h` and then says "for demonstration we simply show the
  calculated value": the KDE never sees it. Here `bw_method = h / spread`, and the factor is
  printed, so the two cannot drift apart.
