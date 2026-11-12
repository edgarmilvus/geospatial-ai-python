# Basic code example — road network graph initialization

## What it does

Turns six road segments and fifteen sensor readings into the two inputs a graph
neural network needs: a 5x5 adjacency matrix that says which intersections touch,
and a (nodes, time, features) tensor that says how fast the traffic was. It then
does the step the pitfall section insists on and normalizes the matrix with
self-loops, because the raw one is not what a graph convolution consumes.

## The listings

| file | what it is |
| --- | --- |
| `01_road_network_graph.py` | the listing: the edge list, `A`, `X`, `A_norm`, the degree check |
| `run_road_network_graph.py` | the harness: symmetry, degree sum, tensor shape, normalization |

## Run it

```bash
cd chapter19/basic_code_example_road_network_graph_initial/example/files
python3 01_road_network_graph.py
```

It prints both matrices with their intersection labels, the degree of intersection B
and the trace of the normalized matrix, then writes a small JSON copy of the graph.
`run_road_network_graph.py` asserts all of those numbers and exits non-zero if the
matrix stops being symmetric or the normalization stops summing to 1.5.

```text
--- GNN input initialization ---
Total nodes (intersections): 5

[1] Adjacency matrix (A) - spatial topology (N x N):
Shape of A: (5, 5)
                Intersection_A  Intersection_B  Intersection_C  Intersection_D  Intersection_E
Intersection_A               0               1               0               0               1
...
Verification check: intersection B (index 1)
Degree (number of neighbours): 3
Connected to: ['Intersection_A', 'Intersection_C', 'Intersection_D']
Total degree over the graph: 12 (6 undirected road segments)
Symmetric: True
...
Trace of A_norm: 1.5000 (= sum of 1/(degree+1) over the five nodes)
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/road_network_graph.json` | node names, edge list, `A`, `A_norm`, the degree sum |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/road_network_example.json` | edge count, degree sum, degree list, tensor shape |

## Notes

- The first draft of this listing printed a timestamp in its header. Nothing else
  in the run depended on the clock, and a header that changes every second makes a
  printed run impossible to compare, so it is gone.
- `np.fill_diagonal(A, 0)` is not redundant after the edge loop: it is what keeps
  the base matrix describing roads rather than roads plus self-loops. The self-loop
  arrives one step later, inside `normalized_adjacency`.
- The five labelled columns are wider than pandas' default display, so the run sets
  `display.width` before printing; a truncated matrix is the one thing the reader
  cannot check by hand.
