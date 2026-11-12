# Exercise 1 — GIS data into a graph, a week into a tensor

## What it does

Takes the two datasets the exercise describes — a road network and a week of
sensor readings — and produces the four artefacts an STGCN expects: a symmetric
adjacency matrix, its normalized Laplacian with self-loops, a feature tensor of
shape (time, nodes, features) with a clock encoded in it, and sliding windows that
never let a future step into the past.

## The listings

| file | what it is |
| --- | --- |
| `01_graph_construction.py` | the solution: the simulator, the Laplacian, the tensor, the windows |
| `run_graph_construction.py` | the harness: topology, normalization, z-scores, split arithmetic |

## Run it

```bash
cd chapter19/exercise_1_gis_data_transformation_and_graph/exercise/files
python3 01_graph_construction.py
```

It prints the graph size, the tensor shape, the feature statistics before
normalization and the 1401/300/301 split of the sliding windows, then writes a
summary to `output/`. `run_graph_construction.py` asserts that `A` is symmetric with
235 road segments, that the Laplacian's eigenvalues stay inside [-1, 1], that the
speed channel is z-scored, and exits non-zero if the target stops being the speed
three steps after the window closes.

```text
Adjacency matrix shape: (50, 50)
Normalized Laplacian shape: (50, 50)
Road segments in the network: 235
Final feature tensor X shape (T, N, F): (2016, 50, 5)
Feature mean before normalization: speed 44.73 km/h, volume 300.44 veh/5min
Feature std before normalization: speed 15.62, volume 115.50

Total samples generated: 2002
Train samples: 1401 | Val samples: 300 | Test samples: 301
Example X_train shape (Batch, T_hist, N, F): (1401, 12, 50, 5)
Example Y_train shape (Batch, T_pred, N): (1401, 3, 50)
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/graph_construction.json` | node and edge counts, Laplacian trace, tensor shape, split sizes |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/graph_construction_exercise.json` | the same counts, re-measured after the import |

## Notes

- The seed is set once at the top. In the first draft it was set *after* the
  adjacency was drawn, so the topology changed from run to run while the readings
  did not — the worst of both worlds: a graph you cannot compare and numbers that
  look stable.
- 2016 steps, not 2017: a week at five-minute resolution is `7 * 24 * 12`. The
  window arithmetic then gives `2016 - 12 - 3 + 1 = 2002` samples, which is what
  the split is computed from.
- The three temporal features are broadcast over the node axis, because the clock
  is the same at every link; they are appended after the z-score so their own scale
  is not distorted by it.
