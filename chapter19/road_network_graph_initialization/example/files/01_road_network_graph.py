"""Chapter 19, example 1 — turning a road network into the two GNN inputs.

Five intersections, six road segments, three five-minute intervals of sensor
data. The listing builds the adjacency matrix A that describes the topology and
the feature tensor X that describes the traffic, prints both with their labels,
and then does what the pitfall section insists on: it adds the self-loops and
normalizes A into the operator a graph convolution actually consumes.

Everything it writes lands in the project's own output/ folder, so the run does
not depend on the directory it starts from, and the numbers it prints are the
same on every machine.
"""

import json
import pathlib

import numpy as np
import pandas as pd

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# Five labelled columns do not fit the default terminal width, and a truncated
# matrix is exactly the thing a reader needs to see whole.
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", None)

# --- 1. Define the road network structure (nodes and edges) ---

# Five major intersections. These are the entities we predict traffic for.
NODES = ["Intersection_A", "Intersection_B", "Intersection_C",
         "Intersection_D", "Intersection_E"]
NUM_NODES = len(NODES)

# The physical connections between intersections, as the GIS extract would
# hand them over: a list of (source index, target index) pairs.
ROAD_CONNECTIONS = [
    (0, 1),  # road segment A <-> B
    (1, 2),  # road segment B <-> C
    (2, 3),  # road segment C <-> D
    (3, 4),  # road segment D <-> E
    (4, 0),  # road segment E <-> A (completes the outer loop)
    (1, 3),  # road segment B <-> D (the bypass)
]

# --- 2. Construct the adjacency matrix (A) ---

A = np.zeros((NUM_NODES, NUM_NODES), dtype=np.int32)
for i, j in ROAD_CONNECTIONS:
    # Roads are two-way unless the data says otherwise, so both cells are set.
    A[i, j] = 1
    A[j, i] = 1

# No self-loops in the base matrix: A describes physical connections only.
np.fill_diagonal(A, 0)

# --- 3. Construct the node feature tensor (X) ---

# X is (Nodes, Timesteps, Features): N=5, T=3 five-minute intervals, F=2.
# The raw feed arrives flat, one row per node: speed and volume per interval.
raw_data = np.array([
    [55.0, 10, 50.0, 12, 45.0, 15],  # A
    [30.0, 25, 35.0, 20, 40.0, 18],  # B
    [65.0, 5, 60.0, 7, 55.0, 9],     # C
    [40.0, 15, 45.0, 13, 50.0, 11],  # D
    [50.0, 12, 55.0, 10, 60.0, 8],   # E
])

TIMESTEPS = 3
FEATURES = 2  # speed and volume

# (5, 6) -> (5, 3, 2)
X = raw_data.reshape(NUM_NODES, TIMESTEPS, FEATURES)

# --- 4. The operator the pitfall section builds: normalized A with self-loops ---
# A graph convolution does not consume the raw A. It consumes
#     A_norm = D^-1/2 (A + I) D^-1/2
# so that a node with six neighbours cannot drown out a node with one.


def normalized_adjacency(adjacency):
    """D^-1/2 (A + I) D^-1/2, as a float matrix."""
    a_hat = adjacency.astype(np.float64) + np.eye(adjacency.shape[0])
    degrees = a_hat.sum(axis=1)
    d_inv_sqrt = np.diag(degrees ** -0.5)
    return d_inv_sqrt @ a_hat @ d_inv_sqrt


A_norm = normalized_adjacency(A)

# --- 5. Display results and verification ---

print("--- GNN input initialization ---")
print(f"Total nodes (intersections): {NUM_NODES}")

print("\n[1] Adjacency matrix (A) - spatial topology (N x N):")
print(f"Shape of A: {A.shape}")
# Labelled axes, because a 5x5 grid of 0s and 1s is unreadable without them.
A_df = pd.DataFrame(A, index=NODES, columns=NODES)
print(A_df)

print("\n[2] Node feature tensor (X) - spatio-temporal data (N x T x F):")
print(f"Shape of X: {X.shape} "
      f"(Nodes={NUM_NODES}, Timesteps={TIMESTEPS}, Features={FEATURES})")

print("\nSnapshot: most recent timestep (T=0) features:")
feature_df = pd.DataFrame(
    X[:, 0, :],
    index=NODES,
    columns=["Speed_kph", "Volume_veh/min"],
)
print(feature_df)

print("\nVerification check: intersection B (index 1)")
node_b_index = 1
degree_b = int(np.sum(A[node_b_index, :]))
connected_nodes = [NODES[i] for i in np.where(A[node_b_index, :] == 1)[0]]
print(f"Degree (number of neighbours): {degree_b}")
print(f"Connected to: {connected_nodes}")
print(f"Total degree over the graph: {int(A.sum())} "
      f"({int(A.sum()) // 2} undirected road segments)")
print(f"Symmetric: {bool(np.array_equal(A, A.T))}")

print("\n[3] Normalized adjacency with self-loops (the operator a GCN consumes):")
print(f"Shape of A_norm: {A_norm.shape}")
print(pd.DataFrame(A_norm.round(4), index=NODES, columns=NODES))
print(f"Trace of A_norm: {np.trace(A_norm):.4f} "
      f"(= sum of 1/(degree+1) over the five nodes)")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "road_network_graph.json").write_text(json.dumps({
    "nodes": NODES,
    "edges": ROAD_CONNECTIONS,
    "adjacency": A.tolist(),
    "adjacency_shape": list(A.shape),
    "degree_total": int(A.sum()),
    "degree_of_b": degree_b,
    "feature_shape": list(X.shape),
    "most_recent_speed": X[:, 0, 0].tolist(),
    "a_norm": A_norm.round(6).tolist(),
    "trace_a_norm": round(float(np.trace(A_norm)), 6),
}, indent=2) + "\n", encoding="utf-8")
print(f"\nWrote output/road_network_graph.json")
