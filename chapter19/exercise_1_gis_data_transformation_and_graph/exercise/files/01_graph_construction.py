"""Chapter 19, exercise 1 — GIS data into a graph, and a week into a tensor.

The four steps the exercise asks for, in order: simulate a 50-link road network
and one week of sensor readings, normalize the adjacency into the operator the
graph convolution consumes, stack speed, volume and three temporal encodings into
an X of shape (T, N, F), and cut that X into sliding windows that keep time in
order. The seed is set once, at the top, so the topology and the readings are the
same on the next run.
"""

import json
import pathlib

import numpy as np
import pandas as pd

SEED = 42
np.random.seed(SEED)

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- Simulation parameters ---
N_NODES = 50              # road links (nodes)
TIME_STEPS = 7 * 24 * 12  # one week at five-minute intervals: 2016 steps
T_HIST = 12               # input window: one hour
T_PRED = 3                # prediction horizon: fifteen minutes


# --- 1. Simulate GIS data and connectivity ---

def simulate_data():
    """A sparse random road network and one week of speed and volume."""
    # Random sparse connectivity, symmetrized so every road is two-way.
    A = np.random.rand(N_NODES, N_NODES)
    A[A < 0.9] = 0
    np.fill_diagonal(A, 0)
    A = (A + A.T) / 2
    A[A > 0] = 1

    speed = np.random.uniform(20, 70, (TIME_STEPS, N_NODES))
    volume = np.random.uniform(100, 500, (TIME_STEPS, N_NODES))

    # A daily cycle: speeds dip around the rush hours instead of being white noise.
    hourly_index = np.tile(np.arange(TIME_STEPS) % 288, (N_NODES, 1)).T
    rush_hour_factor = np.sin(hourly_index / 288 * 2 * np.pi) * 10
    speed = np.clip(speed - rush_hour_factor, 10, 70)

    time_index = pd.to_datetime(pd.date_range("2023-01-01", periods=TIME_STEPS,
                                              freq="5min"))

    frames = []
    for i in range(N_NODES):
        frames.append(pd.DataFrame({
            "timestamp": time_index,
            "link_id": i,
            "speed": speed[:, i],
            "volume": volume[:, i],
        }))
    return A, pd.concat(frames, ignore_index=True)


A, traffic_df = simulate_data()


# --- 2. Graph generation and the normalized Laplacian ---

def calculate_normalized_laplacian(adjacency):
    """L_hat = D^-1/2 (A + I) D^-1/2, the operator the convolution uses."""
    a_hat = adjacency + np.eye(adjacency.shape[0])  # self-loops
    degrees = np.sum(a_hat, axis=1)
    d_inv_sqrt = np.diag(degrees ** -0.5)
    return d_inv_sqrt @ a_hat @ d_inv_sqrt


L_hat = calculate_normalized_laplacian(A)
print(f"Adjacency matrix shape: {A.shape}")
print(f"Normalized Laplacian shape: {L_hat.shape}")
print(f"Road segments in the network: {int(A.sum()) // 2}")


# --- 3. Feature tensor creation ---

def create_feature_tensor(df, n_nodes):
    """Structures the feed into X (T, N, F): two measurements, three encodings."""
    speed_pivot = df.pivot(index="timestamp", columns="link_id",
                           values="speed").values
    volume_pivot = df.pivot(index="timestamp", columns="link_id",
                            values="volume").values

    X_raw = np.stack([speed_pivot, volume_pivot], axis=-1)  # (T, N, 2)

    # Z-score over every sample of each feature, so speed and volume arrive with
    # the same magnitude and neither dominates the first convolution.
    means = X_raw.mean(axis=(0, 1))
    stds = X_raw.std(axis=(0, 1))
    X_normalized = (X_raw - means) / (stds + 1e-5)

    timestamps = pd.to_datetime(df["timestamp"].unique())
    minutes_of_day = timestamps.hour * 60 + timestamps.minute
    sin_time = np.sin(2 * np.pi * minutes_of_day / (24 * 60))
    cos_time = np.cos(2 * np.pi * minutes_of_day / (24 * 60))
    day_of_week = timestamps.dayofweek / 6.0

    temporal_features = np.stack([sin_time, cos_time, day_of_week], axis=1)

    T, N, _ = X_normalized.shape
    # The clock is the same at every link, so the encoding is broadcast over N.
    temporal_features_tiled = np.tile(temporal_features[:, None, :], (1, N, 1))
    X = np.concatenate([X_normalized, temporal_features_tiled], axis=-1)
    return X, means, stds


X_features, means, stds = create_feature_tensor(traffic_df, N_NODES)
print(f"Final feature tensor X shape (T, N, F): {X_features.shape}")
print(f"Feature mean before normalization: speed {means[0]:.2f} km/h, "
      f"volume {means[1]:.2f} veh/5min")
print(f"Feature std before normalization: speed {stds[0]:.2f}, volume {stds[1]:.2f}")


# --- 4. Data partitioning and sliding window ---

def create_sliding_windows(X, t_hist, t_pred, train_ratio=0.7, val_ratio=0.15):
    """Input/output pairs that never let a future step into the past."""
    T, N, F = X.shape
    data_points = []
    for i in range(T - t_hist - t_pred + 1):
        x_input = X[i:i + t_hist, :, :]
        # The target is the speed channel, t_pred steps after the window ends.
        y_target = X[i + t_hist:i + t_hist + t_pred, :, 0]
        data_points.append((x_input, y_target))

    total_samples = len(data_points)
    train_end = int(total_samples * train_ratio)
    val_end = train_end + int(total_samples * val_ratio)

    train_set = data_points[:train_end]
    val_set = data_points[train_end:val_end]
    test_set = data_points[val_end:]

    X_train = np.stack([x[0] for x in train_set])
    Y_train = np.stack([x[1] for x in train_set])

    print(f"\nTotal samples generated: {total_samples}")
    print(f"Train samples: {len(train_set)} | Val samples: {len(val_set)} | "
          f"Test samples: {len(test_set)}")
    print(f"Example X_train shape (Batch, T_hist, N, F): {X_train.shape}")
    print(f"Example Y_train shape (Batch, T_pred, N): {Y_train.shape}")

    return (train_set, val_set, test_set), (X_train, Y_train)


(train_data, val_data, test_data), (X_train, Y_train) = create_sliding_windows(
    X_features, T_HIST, T_PRED)

print(f"\nTemporal order preserved: window 0 covers steps 0-{T_HIST - 1}, "
      f"window 1 covers steps 1-{T_HIST}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "graph_construction.json").write_text(json.dumps({
    "nodes": N_NODES,
    "edges": int(A.sum()) // 2,
    "degree_sum": int(A.sum()),
    "degree_min": int(A.sum(axis=1).min()),
    "degree_max": int(A.sum(axis=1).max()),
    "adjacency_shape": list(A.shape),
    "laplacian_shape": list(L_hat.shape),
    "laplacian_trace": round(float(np.trace(L_hat)), 6),
    "feature_shape": list(X_features.shape),
    "feature_means": [round(float(v), 6) for v in means],
    "feature_stds": [round(float(v), 6) for v in stds],
    "x_train_shape": list(X_train.shape),
    "y_train_shape": list(Y_train.shape),
    "splits": [len(train_data), len(val_data), len(test_data)],
}, indent=2) + "\n", encoding="utf-8")
print("Wrote output/graph_construction.json")
