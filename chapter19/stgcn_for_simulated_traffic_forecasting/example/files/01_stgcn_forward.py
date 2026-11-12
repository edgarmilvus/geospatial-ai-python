"""Chapter 19, example 2 — a simplified STGCN block on a generated road network.

The network is not hand-typed: a four-by-four grid of intersections is built with
NetworkX, its adjacency matrix becomes A, and A is normalized into the operator the
graph convolution uses. Twelve time steps of speed and volume are attached to
every intersection, so the tensor is (nodes, time, features) before anything runs.

The block is the chapter's simplified one: a temporal 2D convolution that sweeps
only the time axis, a spatial aggregation with the normalized adjacency, a trainable
feature transform, and layer normalization. The run ends with one prediction per
intersection, so the forward pass can be read as a forecast rather than as a shape
dump. A fixed seed makes the numbers repeat exactly.
"""

import json
import pathlib

import networkx as nx
import numpy as np
import torch
import torch.nn as nn

SEED = 7
np.random.seed(SEED)
torch.manual_seed(SEED)

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data simulation and graph definition (GIS to tensor) ---

# N = road segments (here: intersections of the grid), T = lookback, F = features.
T, F = 12, 2


def build_road_network(rows=4, cols=4):
    """A synthetic city grid: rows x cols intersections, two-way street segments.

    In a real pipeline this comes from an OSM extract, where each road segment
    carries its length and speed limit; here the grid is generated so the listing
    owns its data and every run sees the same topology.
    """
    graph = nx.grid_2d_graph(rows, cols)
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")
    for u, v in graph.edges:
        # A street segment between two neighbours in the grid: 250 m apart.
        graph[u][v]["length_m"] = 250.0
    return graph


G = build_road_network(4, 4)
N = G.number_of_nodes()

# A is the topology, nothing else: 1 where a street segment exists.
A = nx.to_numpy_array(G, nodelist=range(N), weight=None, dtype=np.float32)
# nx.to_numpy_array returns float; keep it explicit and symmetric-friendly.
A = (A > 0).astype(np.float32)
np.fill_diagonal(A, 0.0)

# Historical traffic: 12 five-minute steps of speed and volume per intersection.
X_features = torch.randn(N, T, F) * 10 + 50  # speeds centred around 50 km/h

# --- 2. Graph preprocessing: normalized adjacency (A_tilde) ---


def normalized_adjacency(adjacency):
    """A_tilde = D^-1/2 (A + I) D^-1/2, with the self-loops already added."""
    a_hat = adjacency + np.eye(adjacency.shape[0], dtype=np.float32)
    d_inv_sqrt = np.diag(np.sum(a_hat, axis=1) ** (-0.5))
    return torch.from_numpy(d_inv_sqrt @ a_hat @ d_inv_sqrt)


A_tilde = normalized_adjacency(A)

# --- 3. One simplified STGCN block: temporal convolution, then graph convolution ---


class SimplifiedSTGCNLayer(nn.Module):
    """One block: temporal convolution, spatial aggregation, feature transform."""

    def __init__(self, in_features, out_features, num_nodes, time_steps):
        super().__init__()
        # Temporal component: kernel (1, 3) sweeps the time axis and leaves the
        # node axis alone, so every intersection is filtered independently.
        self.tcn_1 = nn.Conv2d(in_features, out_features,
                               kernel_size=(1, 3), padding=(0, 1))
        # Spatial component: the trainable Theta the aggregation is multiplied by.
        self.theta = nn.Linear(out_features, out_features, bias=False)
        # Layer normalization over every axis of the hidden state, whose layout is
        # (nodes, time, features) once the aggregation has run.
        self.norm = nn.LayerNorm([num_nodes, time_steps, out_features])

    def forward(self, x, a_tilde):
        # x is (N, T, F_in); PyTorch wants (batch, channels, height, width).
        x_in = x.permute(2, 1, 0).unsqueeze(0)          # (1, F_in, T, N)
        h_temp = torch.relu(self.tcn_1(x_in))           # (1, F_out, T, N)
        # Drop the batch axis and put the node axis first again: (N, T, F_out).
        h_spatial_input = h_temp[0].permute(2, 1, 0)

        # 'ij,jtf->itf' multiplies (N,N) by (N,T,F_out) along the node axis: the
        # message passing step, one matrix product for every time step.
        h_aggregated = torch.einsum("ij, jtf -> itf", a_tilde, h_spatial_input)
        h_output = self.theta(h_aggregated)
        return self.norm(h_output)


# --- 4. Model instantiation and forward pass ---

HIDDEN_FEATURES = 32
OUT_FEATURES = 1  # the target: future speed

stgcn_block = SimplifiedSTGCNLayer(
    in_features=F,
    out_features=HIDDEN_FEATURES,
    num_nodes=N,
    time_steps=T,
)
final_predictor = nn.Linear(HIDDEN_FEATURES, OUT_FEATURES)

H_hidden = stgcn_block(X_features, A_tilde)   # (N, T, HIDDEN_FEATURES)
H_hidden = torch.relu(H_hidden)

# The next step is predicted from the most recently processed time step.
final_time_features = H_hidden[:, -1, :]      # (N, HIDDEN_FEATURES)
predicted_traffic = final_predictor(final_time_features)  # (N, 1)

# --- 5. Display results ---

print("--- Traffic prediction simulation using a simplified STGCN ---")
print(f"Road network: {G.number_of_nodes()} intersections, "
      f"{G.number_of_edges()} street segments")
print(f"Input feature tensor shape (N, T, F): {tuple(X_features.shape)}")
print(f"Adjacency matrix shape (N, N): {A.shape}")
print(f"Normalized adjacency matrix shape (N, N): {tuple(A_tilde.shape)}")
print(f"Hidden state output shape (N, T, Hidden): {tuple(H_hidden.shape)}")
print("\nPredicted future traffic state (speed) for every intersection:")
for i, speed in enumerate(predicted_traffic.squeeze().tolist()):
    print(f"  Intersection {i:2d}: {speed:7.2f} km/h")

degree = A.sum(axis=1).astype(int)
print(f"\nDegree sum over the grid: {int(degree.sum())} "
      f"(= 2 x {G.number_of_edges()} street segments)")
print(f"Average degree: {degree.mean():.2f}")

parameter_count = (sum(p.numel() for p in stgcn_block.parameters())
                   + sum(p.numel() for p in final_predictor.parameters()))
print(f"Parameters in the block and the head: {parameter_count}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "stgcn_forward.json").write_text(json.dumps({
    "nodes": int(N),
    "edges": int(G.number_of_edges()),
    "adjacency": A.astype(int).tolist(),
    "degrees": degree.tolist(),
    "degree_sum": int(degree.sum()),
    "feature_shape": list(X_features.shape),
    "hidden_shape": list(H_hidden.shape),
    "predicted_speed": [round(v, 4) for v in predicted_traffic.squeeze().tolist()],
    "parameter_count": parameter_count,
    "trace_a_tilde": round(float(np.trace(A_tilde.numpy())), 6),
}, indent=2) + "\n", encoding="utf-8")
print("Wrote output/stgcn_forward.json")
