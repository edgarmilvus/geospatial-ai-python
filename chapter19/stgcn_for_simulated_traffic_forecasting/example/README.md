# Advanced application script — a simplified STGCN forward pass

## What it does

Generates a four-by-four city grid with NetworkX, turns its adjacency into the
normalized operator a graph convolution consumes, and runs one STGCN block over
twelve time steps of speed and volume. The block sweeps time with a 2D convolution,
aggregates across the graph with `torch.einsum`, transforms the result with a
trainable matrix, and ends with a per-intersection forecast.

## The listings

| file | what it is |
| --- | --- |
| `01_stgcn_forward.py` | the listing: the grid, `A_tilde`, `SimplifiedSTGCNLayer`, one forward pass |
| `run_stgcn_forward.py` | the harness: topology, degree sum, operator, output shape, parameter count |

## Run it

```bash
cd chapter19/stgcn_for_simulated_traffic_forecasting/example/files
python3 01_stgcn_forward.py
```

It prints the graph's size, the shape at each stage of the forward pass and one
predicted speed per intersection, then writes the adjacency and the forecasts to
`output/`. `run_stgcn_forward.py` asserts that the grid has 24 street segments and a
degree sum of 48, that the hidden state is `(16, 12, 32)`, and exits non-zero if the
block's 13 569 parameters or its determinism change.

```text
--- Traffic prediction simulation using a simplified STGCN ---
Road network: 16 intersections, 24 street segments
Input feature tensor shape (N, T, F): (16, 12, 2)
Adjacency matrix shape (N, N): (16, 16)
Normalized adjacency matrix shape (N, N): (16, 16)
Hidden state output shape (N, T, Hidden): (16, 12, 32)

Predicted future traffic state (speed) for every intersection:
  Intersection  0:   -0.28 km/h
...
Degree sum over the grid: 48 (= 2 x 24 street segments)
Average degree: 3.00
Parameters in the block and the head: 13569
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/stgcn_forward.json` | adjacency, degrees, shapes, the sixteen forecasts, parameter count |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/stgcn_forward_example.json` | node and edge counts, degree sum, output shape, prediction range |

## Notes

- The first draft indexed the node axis by `permute(3, 2, 1)` on a three-dimensional
  tensor and stopped with `IndexError: Dimension out of range`. The convolution
  output is `(1, F_out, T, N)`; dropping the batch axis leaves `(F_out, T, N)`, and
  the permutation that returns to `(N, T, F_out)` is `(2, 1, 0)`. The book's block
  now carries that order, and the harness pins the resulting shape.
- Layer normalization is declared with `[num_nodes, time_steps, out_features]` so it
  normalizes the layout the tensor actually has. Declared the other way round it
  still runs, and normalizes the wrong axes in silence.
- The forecasts sit near zero because the block is untrained and the layer norm
  re-centres its output. That is the honest output of a forward pass, not a bug;
  exercise 3 is where the weights learn a scale.
