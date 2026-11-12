# Example 2 — gridded KDE: 5 000 pings, 22 500 cells, one peak

## What it does

Goes past "drop the points and let Leaflet smooth them": it fits a Gaussian kernel density
estimate to 5 000 simulated ride-share pings, evaluates that surface on a 150 by 150 grid
over the city, and hands the grid to `HeatMap` as `[lat, lon, intensity]` triples. The
interesting parts are the two numbers the book glosses over — what a bandwidth of 0.0035
means, and what range the intensities must be in.

## The listings

| file | what it is |
| --- | --- |
| `gridded_kde_traffic.py` | the listing: seeded pings, `gaussian_kde`, a grid, a heat layer |
| `run_gridded_kde.py` | the harness: the bandwidth, the peak, the weights, the layer |

## Run it

```bash
cd chapter9/subsection_3_5_advanced_application_script/example/files
python3 gridded_kde_traffic.py
```

It generates the pings, evaluates the density surface, prints the bandwidth in degrees and
metres, the factor handed to scipy, the peak cell and the number of cells at the colour cap,
then writes `output/advanced_traffic_kde_heatmap.html`. `run_gridded_kde.py` calls the
script's `main()` and reads the heat layer back (39 assertions); it exits non-zero if the
peak drifts off the planted hotspot or an intensity leaves 0..1.

```text
--- GeoAI Advanced Traffic Density Analysis (KDE Grid Method) ---
1. Generated 5000 raw GPS points.
2. KDE calculated over a 150x150 grid.
3. Prepared 22481 weighted grid points for visualization.
   Bandwidth 0.0035 degrees = 390 m of latitude, applied as bw_method=0.1462 (scipy multiplies by the data's 0.0239 degree spread).
   Peak density 4234.468 at 34.0565 N, -118.2512 E; cap 2117.234; 15 cells saturate the colour scale.
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/advanced_traffic_kde_heatmap.html` | the standalone map with the weighted grid |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/gridded_kde.json` | bandwidth, spread, factor, peak, cap, saturated cells, gradient |

## Notes

- `bw_method=0.0035` in the book is not 0.0035 degrees: scipy treats it as a multiplier on
  the sample's covariance, so the smoothing changed with the data. The listing divides the
  bandwidth by the sample's spread and prints both, because a bandwidth you cannot state in
  metres is not a parameter you control.
- Folium 0.19 removed `max_val` from `HeatMap` (it warns and ignores it) and leaflet-heat
  reads intensities in 0..1, so the book's `density * 10000` would paint the whole city at
  the top colour. The weights are normalised against half the peak, which is the cap the
  comment describes, and 15 cells reach it.
- The gradient keys were floats. Folium camel-cases its option keys, so `0.2` raised
  `AttributeError: 'float' object has no attribute 'split'` before the file could be written.
- 19 of the 22 500 cells are missing from the layer because their density underflowed to
  zero: the Gaussian never reaches zero, but in the far corners of the grid the value is
  smaller than a float can represent.
