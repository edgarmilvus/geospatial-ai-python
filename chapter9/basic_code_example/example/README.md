# Example 1 — 500 drone sightings as a heat layer

## What it does

Turns a list of `[lat, lon]` pairs into a `folium.plugins.HeatMap` of 500 simulated drone
sightings over Los Angeles: 70 per cent clustered tightly around downtown, 30 per cent at a
suburban outpost, so the density actually varies. The map is one HTML file with one layer
and a light basemap.

## The listings

| file | what it is |
| --- | --- |
| `drone_density_heatmap.py` | the listing: 500 seeded sightings, one map, one heat layer |
| `run_drone_heatmap.py` | the harness: the clusters, the coordinate order, the layer's data |

## Run it

```bash
cd chapter9/basic_code_example/example/files
python3 drone_density_heatmap.py
```

It simulates the sightings, prints how many fell in each cluster and the latitude and
longitude spans, and writes `output/basic_drone_density_map.html`.
`run_drone_heatmap.py` reads the `L.heatLayer` dataset back out of that file and checks that
every pair is `[latitude, longitude]` inside Los Angeles (28 assertions); it exits non-zero
if the split stops holding or a pair is written the other way round.

```text
Sightings: 500 around 34.0522 N, -118.2437 E
Downtown cluster: 349 points; suburban outpost: 151 points
Latitude span: 34.0198 to 34.1151
Longitude span: -118.2944 to -118.1859
First three pairs [lat, lon]: [[34.0572, -118.2458], [34.0587, -118.2209], [34.0499, -118.2472]]
```

## What it produces

Written by the listing:

| path | what it is |
| --- | --- |
| `output/basic_drone_density_map.html` | the standalone map: one heat layer over CartoDB Positron |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/drone_heatmap.json` | the cluster counts, the spans, the centre, the zoom, the tile URL |

## Notes

- The data is seeded. `random.random()` and `np.random.normal()` without a seed draw a
  different city on every run, so none of the numbers above would survive a second run.
- The chapter's own pitfall is shown rather than described: a reversed pair puts 34 into the
  longitude slot and produces a heatmap off the coast of Africa. The harness asserts the
  band each coordinate falls in, which is the only way to catch that from a file.
- The HTML needs a browser **and an internet connection to show the tiles**; the file itself
  is generated offline.
