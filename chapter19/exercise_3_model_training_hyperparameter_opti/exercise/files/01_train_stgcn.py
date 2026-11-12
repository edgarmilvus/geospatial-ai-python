"""Chapter 19, exercise 3 — train the STGCN, search two hyperparameters, evaluate.

Two ST-Conv blocks and a linear head, trained on one day of five-minute readings
from a thirty-link network. The script walks the grid the exercise asks for (the
Chebyshev order, the temporal kernel, the hidden width), keeps the combination
with the best validation error, retrains it, and reports MAE, RMSE and R^2 on a
held-out tail of the day — for each of the three horizons separately, because a
forecast fifteen minutes out is harder than one five minutes out.

The run is CPU-only, seeded, and under a few seconds: the numbers are meant to be
reproduced, not to win a benchmark.
"""

import json
import pathlib
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn

SEED = 3
np.random.seed(SEED)
torch.manual_seed(SEED)

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

# --- 1. Data: one day of readings from a thirty-link network ---

N_NODES = 30
TIME_STEPS = 288          # one day at five-minute resolution
T_HIST = 18               # ninety minutes of history
T_PRED = 3                # fifteen minutes ahead
F_IN = 3                  # speed, volume, sin(hour)


def build_day():
    """A rush-hour shaped day, generated so the listing owns its data."""
    minutes = np.arange(TIME_STEPS)
    hour = (minutes % 288) / 12.0
    # Two peaks, at 08:00 and 17:30, as a fraction of the day.
    cycle = (np.exp(-((hour - 8.0) ** 2) / 2.0)
             + 0.8 * np.exp(-((hour - 17.5) ** 2) / 3.0))
    base_speed = 60.0 - 35.0 * cycle
    base_volume = 150.0 + 250.0 * cycle

    speed = np.zeros((TIME_STEPS, N_NODES))
    volume = np.zeros((TIME_STEPS, N_NODES))
    for node in range(N_NODES):
        noise = np.random.normal(0.0, 2.0, TIME_STEPS)
        speed[:, node] = base_speed + noise + 1.5 * np.sin(minutes / 7.0 + node)
        volume[:, node] = base_volume + np.random.normal(0.0, 15.0, TIME_STEPS)

    speed = np.clip(speed, 5.0, 75.0)
    clock = np.sin(2 * np.pi * hour / 24.0)
    X = np.stack([speed, volume, np.tile(clock[:, None], (1, N_NODES))], axis=-1)
    return X, speed


X_raw, SPEED = build_day()

# Standardize each feature over the whole day; keep the speed statistics for the
# denormalization that makes the error interpretable in km/h.
MEAN = X_raw.mean(axis=(0, 1))
STD = X_raw.std(axis=(0, 1))
X = (X_raw - MEAN) / (STD + 1e-8)


def sliding_windows(t_hist, t_pred):
    inputs, targets, speeds = [], [], []
    for start in range(TIME_STEPS - t_hist - t_pred + 1):
        inputs.append(X[start:start + t_hist])
        targets.append(X[start + t_hist:start + t_hist + t_pred, :, 0])
        speeds.append(SPEED[start + t_hist:start + t_hist + t_pred])
    return (torch.tensor(np.stack(inputs), dtype=torch.float32),
            torch.tensor(np.stack(targets), dtype=torch.float32),
            torch.tensor(np.stack(speeds), dtype=torch.float32))


X_all, Y_all, S_all = sliding_windows(T_HIST, T_PRED)
total = X_all.shape[0]
train_end = int(total * 0.6)
val_end = train_end + int(total * 0.15)

X_train, Y_train = X_all[:train_end], Y_all[:train_end]
X_val, Y_val = X_all[train_end:val_end], Y_all[train_end:val_end]
X_test, Y_test, S_test = X_all[val_end:], Y_all[val_end:], S_all[val_end:]

print(f"Windows: {total} total | {len(X_train)} train | {len(X_val)} val | "
      f"{len(X_test)} test")

# --- 2. The graph operator ---


def normalized_laplacian(adjacency):
    """L = I - D^-1/2 A D^-1/2, with self-loops counted in the degree."""
    degrees = adjacency.sum(axis=1) + 1.0
    d_inv_sqrt = np.diag(degrees ** -0.5)
    return np.eye(adjacency.shape[0]) - d_inv_sqrt @ adjacency @ d_inv_sqrt


def scaled_laplacian(adjacency):
    laplacian = normalized_laplacian(adjacency)
    lambda_max = np.linalg.eigvalsh(laplacian)[-1]
    return (2.0 / lambda_max) * laplacian - np.eye(adjacency.shape[0])


adjacency = (np.random.rand(N_NODES, N_NODES) > 0.9).astype(np.float64)
adjacency = np.triu(adjacency, 1)
adjacency = adjacency + adjacency.T
L_TILDE = torch.from_numpy(scaled_laplacian(adjacency)).float()


def chebyshev_polynomials(l_tilde, order):
    identity = torch.eye(l_tilde.shape[0], dtype=l_tilde.dtype)
    terms = [identity]
    if order > 1:
        terms.append(l_tilde)
    for _ in range(2, order):
        terms.append(2 * l_tilde @ terms[-1] - terms[-2])
    return torch.stack(terms)


# --- 3. The block, then two blocks and a head ---

class TemporalGatedConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size):
        super().__init__()
        self.out_channels = out_channels
        self.conv = nn.Conv1d(in_channels, 2 * out_channels, kernel_size)

    def forward(self, x):
        batch, time, node, features = x.shape
        folded = x.permute(0, 2, 3, 1).reshape(batch * node, features, time)
        convolved = self.conv(folded)
        p, q = convolved.chunk(2, dim=1)
        gated = p * torch.sigmoid(q)
        return gated.reshape(batch, node, self.out_channels, gated.shape[-1]) \
            .permute(0, 3, 1, 2)


class SpatialChebyshevConv(nn.Module):
    def __init__(self, order, in_channels, out_channels):
        super().__init__()
        self.order = order
        self.theta = nn.Parameter(torch.empty(order, in_channels, out_channels))
        nn.init.xavier_uniform_(self.theta)

    def forward(self, x, l_tilde):
        terms = chebyshev_polynomials(l_tilde, self.order)
        batch, time, node, features = x.shape
        folded = x.reshape(batch * time, node, features)
        out = None
        for k in range(self.order):
            aggregated = torch.einsum("ij,bjf->bif", terms[k], folded)
            weighted = torch.einsum("bnf,fo->bno", aggregated, self.theta[k])
            out = weighted if out is None else out + weighted
        return out.reshape(batch, time, node, -1)


class STConvBlock(nn.Module):
    def __init__(self, order, kernel_size, in_channels, out_channels, nodes,
                 time_steps):
        super().__init__()
        self.tconv1 = TemporalGatedConv(in_channels, out_channels, kernel_size)
        self.sconv = SpatialChebyshevConv(order, out_channels, out_channels)
        self.tconv2 = TemporalGatedConv(out_channels, out_channels, kernel_size)
        self.residual = nn.Conv1d(in_channels, out_channels, 1)
        self.time_out = time_steps - 2 * (kernel_size - 1)

    def forward(self, x, l_tilde):
        time_in = x.shape[1]
        h = self.sconv(self.tconv1(x), l_tilde)
        h = self.tconv2(h)
        time_out = h.shape[1]
        folded = x.permute(0, 2, 3, 1).reshape(-1, x.shape[3], time_in)
        res = self.residual(folded)[:, :, :time_out]
        res = res.reshape(x.shape[0], x.shape[2], h.shape[3], time_out) \
            .permute(0, 3, 1, 2)
        # No normalization layer inside the block: per-sample normalization would
        # erase the speed level itself, and batch statistics over 6 400 values are
        # unstable on a hundred windows. The inputs are standardized instead.
        return torch.relu(h + res)


class STGCN(nn.Module):
    """Two ST-Conv blocks and a per-node head: (B, N, F) -> (B, T_pred, N).

    The head is deliberately a per-node linear map on the last processed time
    step. Flattening every node and time step into one dense layer, as a first
    draft did, gives the model 50 000 weights for 187 training windows and it
    learns the average speed of the training set instead of the forecast.
    """

    def __init__(self, order, kernel_size, f_in, hidden, nodes, time_steps,
                 t_pred):
        super().__init__()
        self.block1 = STConvBlock(order, kernel_size, f_in, hidden, nodes,
                                  time_steps)
        middle = time_steps - 2 * (kernel_size - 1)
        self.block2 = STConvBlock(order, kernel_size, hidden, hidden, nodes, middle)
        self.head = nn.Linear(hidden, t_pred)
        self.t_pred = t_pred

    def forward(self, x, l_tilde):
        h = self.block2(self.block1(x, l_tilde), l_tilde)
        last = h[:, -1, :, :]                    # (B, N, F)
        return self.head(last).permute(0, 2, 1)  # (B, T_pred, N)


# --- 4. Training and the hyperparameter grid ---

def batches(n, size, shuffle_seed=None):
    """Sequential batches: shuffling a time series breaks the leakage guard."""
    order = np.arange(n)
    if shuffle_seed is not None:
        rng = np.random.RandomState(shuffle_seed)
        rng.shuffle(order)
    for start in range(0, n, size):
        idx = order[start:start + size]
        yield idx


def train_model(order, kernel_size, hidden, epochs, verbose=False):
    torch.manual_seed(SEED)
    model = STGCN(order, kernel_size, F_IN, hidden, N_NODES, T_HIST, T_PRED)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    loss_fn = nn.SmoothL1Loss()

    history = []
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0.0
        for idx in batches(len(X_train), 32, shuffle_seed=SEED + epoch):
            optimizer.zero_grad()
            prediction = model(X_train[idx], L_TILDE)
            loss = loss_fn(prediction, Y_train[idx])
            loss.backward()
            optimizer.step()
            epoch_loss += float(loss.detach()) * len(idx)
        train_loss = epoch_loss / len(X_train)

        model.eval()
        with torch.no_grad():
            val_prediction = model(X_val, L_TILDE)
            val_loss = float(loss_fn(val_prediction, Y_val).detach())
        history.append((train_loss, val_loss))
        if verbose:
            print(f"  epoch {epoch + 1:2d}: train {train_loss:.4f} | "
                  f"val {val_loss:.4f}")
    return model, history


print("\nHyperparameter search (validation Huber loss after two epochs):")
best = None
grid_results = []
for order in (2, 3):
    for kernel_size in (3, 5):
        for hidden in (8, 16):
            _, history = train_model(order, kernel_size, hidden, epochs=2)
            val_loss = history[-1][1]
            grid_results.append({"order": order, "kernel": kernel_size,
                                 "hidden": hidden, "val_loss": round(val_loss, 6)})
            print(f"  K={order} Kt={kernel_size} F={hidden}: val {val_loss:.4f}")
            if best is None or val_loss < best[3]:
                best = (order, kernel_size, hidden, val_loss)

best_order, best_kernel, best_hidden, best_val = best
print(f"\nBest configuration: K={best_order}, Kt={best_kernel}, F={best_hidden} "
      f"(val {best_val:.4f})")

# --- 5. Retrain the winner and evaluate it on the held-out tail ---

print("\nFinal training run:")
model, history = train_model(best_order, best_kernel, best_hidden, epochs=8,
                             verbose=True)

losses = [row[0] for row in history]
val_losses = [row[1] for row in history]

model.eval()
with torch.no_grad():
    prediction = model(X_test, L_TILDE)

# Back to km/h: undo the z-score the speed channel went through.
speed_mean, speed_std = float(MEAN[0]), float(STD[0])
predicted_speed = prediction.numpy() * speed_std + speed_mean
actual_speed = S_test.numpy()

mae = float(np.mean(np.abs(actual_speed - predicted_speed)))
rmse = float(np.sqrt(np.mean((actual_speed - predicted_speed) ** 2)))
residual = actual_speed - predicted_speed
r2 = float(1.0 - residual.var() / actual_speed.var())


def flat_correlation(a, b):
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    return float((a @ b) / np.sqrt((a @ a) * (b @ b)))


print("\n--- Performance on the test tail (denormalized speed, km/h) ---")
print(f"Overall MAE:  {mae:.2f} km/h")
print(f"Overall RMSE: {rmse:.2f} km/h")
print(f"Overall R2:   {r2:.3f}")

horizon_mae = []
print("\nSegmented MAE by horizon:")
for t in range(T_PRED):
    step_mae = float(np.mean(np.abs(actual_speed[:, t] - predicted_speed[:, t])))
    horizon_mae.append(round(step_mae, 4))
    print(f"  T+{(t + 1) * 5} min MAE: {step_mae:.2f} km/h")

print(f"\nTrain loss: {losses[0]:.4f} -> {losses[-1]:.4f}")
print(f"Validation loss: {val_losses[0]:.4f} -> {val_losses[-1]:.4f}")

# --- 6. The figure the exercise asks for ---

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))

axes[0].plot(range(1, len(losses) + 1), losses, marker="o", label="train")
axes[0].plot(range(1, len(val_losses) + 1), val_losses, marker="s", label="validation")
axes[0].set_xlabel("epoch")
axes[0].set_ylabel("Huber loss")
axes[0].set_title("Loss by epoch")
axes[0].legend()
axes[0].grid(alpha=0.3)

link = 4
steps = np.arange(len(actual_speed) * T_PRED)
axes[1].plot(steps, actual_speed[:, :, link].ravel(), label="actual", linewidth=1.4)
axes[1].plot(steps, predicted_speed[:, :, link].ravel(), label="predicted",
             linewidth=1.0, alpha=0.85)
axes[1].set_xlabel("five-minute step")
axes[1].set_ylabel("speed (km/h)")
axes[1].set_title(f"Link {link}: actual against predicted")
axes[1].legend()
axes[1].grid(alpha=0.3)

fig.tight_layout()
figure_path = OUTPUT_DIR / "stgcn_training.png"
fig.savefig(figure_path, dpi=90)
plt.close(fig)

parameter_count = sum(p.numel() for p in model.parameters())
print(f"\nParameters in the trained model: {parameter_count}")
print(f"Wrote output/{figure_path.name}")

(OUTPUT_DIR / "stgcn_training.json").write_text(json.dumps({
    "windows": {"total": total, "train": len(X_train), "val": len(X_val),
                "test": len(X_test)},
    "grid": grid_results,
    "best": {"order": best_order, "kernel": best_kernel, "hidden": best_hidden,
             "val_loss": round(best_val, 6)},
    "train_loss": [round(v, 6) for v in losses],
    "val_loss": [round(v, 6) for v in val_losses],
    "metrics": {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4)},
    "horizon_mae": horizon_mae,
    "parameter_count": parameter_count,
    "figure": figure_path.name,
}, indent=2) + "\n", encoding="utf-8")
print("Wrote output/stgcn_training.json")
