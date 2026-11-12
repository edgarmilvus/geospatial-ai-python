"""Chapter 19, exercise 2 — one ST-Conv block, built in PyTorch.

The block is three operations in a fixed order: a gated temporal convolution, a
spatial convolution in the Chebyshev basis of the scaled Laplacian, and a second
gated temporal convolution, with a residual path that matches the shortened time
axis. Everything is written against tensors of shape (batch, time, node, feature),
so the two convolutions stay orthogonal: one moves along time, the other along
the graph and never across a road it cannot see.

The batch below is the 50-link network from exercise 1: 32 nodes-wide windows would
be expensive, so the demonstration uses a batch of 4 windows of 12 steps.
"""

import json
import pathlib

import numpy as np
import torch
import torch.nn as nn

SEED = 11
np.random.seed(SEED)
torch.manual_seed(SEED)

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"

N_NODES = 50
T_IN = 12
F_IN = 5     # speed, volume, sin(hour), cos(hour), day of week
BATCH = 4


# --- 1. The graph operators the spatial layer needs ---

def normalized_laplacian(adjacency):
    """L = I - D^-1/2 A D^-1/2, the symmetric normalized graph Laplacian.

    The degrees include the self-loops, so an isolated link (degree zero, which a
    sparsity cut can produce) cannot divide by zero.
    """
    degrees = adjacency.sum(axis=1) + 1.0
    d_inv_sqrt = np.diag(degrees ** -0.5)
    return np.eye(adjacency.shape[0]) - d_inv_sqrt @ adjacency @ d_inv_sqrt


def scaled_laplacian(adjacency):
    """L_tilde = 2 L / lambda_max - I, whose spectrum lives in [-1, 1].

    Chebyshev polynomials only behave on [-1, 1]; this is the scaling that makes
    the recursion of the next function stable instead of explosive.
    """
    laplacian = normalized_laplacian(adjacency)
    lambda_max = np.linalg.eigvalsh(laplacian)[-1]
    return (2.0 / lambda_max) * laplacian - np.eye(adjacency.shape[0])


def chebyshev_polynomials(l_tilde, order):
    """T_0 = I, T_1 = L_tilde, T_k = 2 L_tilde T_{k-1} - T_{k-2}.

    Returns a (order, N, N) stack: one matrix per term of the expansion.
    """
    n = l_tilde.shape[0]
    identity = torch.eye(n, dtype=l_tilde.dtype)
    terms = [identity]
    if order > 1:
        terms.append(l_tilde)
    for _ in range(2, order):
        terms.append(2 * l_tilde @ terms[-1] - terms[-2])
    return torch.stack(terms)


# --- 2. Temporal gated convolution: 1D convolution plus a GLU ---

class TemporalGatedConv(nn.Module):
    """A 1D convolution along time, gated by its own second half.

    The convolution produces twice the requested channels; one half is the signal,
    the other is squashed through a sigmoid and used as a gate. That gate is what
    lets the network drop a time step it has learned to distrust, which is the
    LSTM-like behaviour the chapter attributes to the GLU.
    """

    def __init__(self, in_channels, out_channels, kernel_size):
        super().__init__()
        self.out_channels = out_channels
        self.conv = nn.Conv1d(in_channels, 2 * out_channels, kernel_size,
                              padding="valid")

    def forward(self, x):
        # x is (batch, time, node, feature): fold node into the batch so the
        # convolution slides only along time.
        batch, time, node, features = x.shape
        folded = x.permute(0, 2, 3, 1).reshape(batch * node, features, time)
        convolved = self.conv(folded)                       # (B*N, 2F_out, T_out)
        convolved = convolved.reshape(batch * node, 2 * self.out_channels, -1)
        p, q = convolved.chunk(2, dim=1)
        gated = p * torch.sigmoid(q)                        # (B*N, F_out, T_out)
        time_out = gated.shape[-1]
        return gated.reshape(batch, node, self.out_channels, time_out) \
            .permute(0, 3, 1, 2)


# --- 3. Spatial graph convolution in the Chebyshev basis ---

class SpatialChebyshevConv(nn.Module):
    """sum_k theta_k T_k(L_tilde) X, with one trainable weight per term."""

    def __init__(self, order, in_channels, out_channels):
        super().__init__()
        self.order = order
        # One (F_in, F_out) matrix per Chebyshev term.
        self.theta = nn.Parameter(torch.empty(order, in_channels, out_channels))
        nn.init.xavier_uniform_(self.theta)

    def forward(self, x, l_tilde):
        terms = chebyshev_polynomials(l_tilde, self.order)  # (K, N, N)
        # Fold time into the batch: the same graph acts on every time step.
        batch, time, node, features = x.shape
        folded = x.reshape(batch * time, node, features)    # (B*T, N, F_in)
        out = None
        for k in range(self.order):
            # T_k (N,N) applied along the node axis, then the k-th weight matrix.
            aggregated = torch.einsum("ij,bjf->bif", terms[k], folded)
            weighted = torch.einsum("bnf,fo->bno", aggregated, self.theta[k])
            out = weighted if out is None else out + weighted
        return out.reshape(batch, time, node, -1)


# --- 4. The block: T-Conv -> S-Conv -> T-Conv, with a residual path ---

class STConvBlock(nn.Module):
    """The block the exercise asks for, including the dimension bookkeeping."""

    def __init__(self, order, kernel_size, in_channels, out_channels, nodes,
                 time_steps):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.tconv1 = TemporalGatedConv(in_channels, out_channels, kernel_size)
        self.sconv = SpatialChebyshevConv(order, out_channels, out_channels)
        self.tconv2 = TemporalGatedConv(out_channels, out_channels, kernel_size)
        # The residual path has to change both the channel count and the time
        # length, so it is a 1x1 convolution followed by a slice.
        self.residual = nn.Conv1d(in_channels, out_channels, 1)
        # Normalization over every axis except the batch: the block is used with
        # small batches where batch statistics are not worth trusting.
        time_out = time_steps - 2 * (kernel_size - 1)
        self.norm = nn.LayerNorm([time_out, nodes, out_channels])

    def forward(self, x, l_tilde):
        time_in = x.shape[1]
        h = self.tconv1(x)                  # T_in - (Kt-1)
        h = self.sconv(h, l_tilde)          # time unchanged
        h = self.tconv2(h)                  # T_in - 2(Kt-1)
        time_out = h.shape[1]

        folded = x.permute(0, 2, 3, 1).reshape(-1, x.shape[3], time_in)
        res = self.residual(folded)[:, :, :time_out]
        res = res.reshape(x.shape[0], x.shape[2], self.out_channels, time_out) \
            .permute(0, 3, 1, 2)
        out = torch.relu(h + res)
        return self.norm(out)


# --- 5. Run it ---

# A 50-link network with the same sparsity as exercise 1.
adjacency = (np.random.rand(N_NODES, N_NODES) > 0.9).astype(np.float64)
adjacency = np.triu(adjacency, 1)
adjacency = adjacency + adjacency.T
L_tilde = torch.from_numpy(scaled_laplacian(adjacency)).float()

X_batch = torch.randn(BATCH, T_IN, N_NODES, F_IN)

ORDER = 3        # K: Chebyshev terms
KERNEL = 3       # Kt: temporal kernel size
F_OUT = 64

st_conv = STConvBlock(order=ORDER, kernel_size=KERNEL, in_channels=F_IN,
                      out_channels=F_OUT, nodes=N_NODES, time_steps=T_IN)
H_output = st_conv(X_batch, L_tilde)

expected_time = T_IN - 2 * (KERNEL - 1)

print("--- ST-Conv block ---")
print(f"Adjacency shape (N, N): {adjacency.shape}")
print(f"Scaled Laplacian spectrum: [{np.linalg.eigvalsh(L_tilde.numpy()).min():.4f}, "
      f"{np.linalg.eigvalsh(L_tilde.numpy()).max():.4f}]")
print(f"Chebyshev terms for K={ORDER}: {tuple(chebyshev_polynomials(L_tilde, ORDER).shape)}")
print(f"Input X shape (B, T_in, N, F_in): {tuple(X_batch.shape)}")
print(f"Output H shape (B, T_out, N, F_out): {tuple(H_output.shape)}")
print(f"T_out = T_in - 2*(Kt-1) = {T_IN} - {2 * (KERNEL - 1)} = {expected_time}")
parameter_count = sum(p.numel() for p in st_conv.parameters())
print(f"Trainable parameters: {parameter_count}")

# The residual path is what makes a deep stack trainable: check the gradient
# reaches the input through it.
X_batch.requires_grad_(True)
st_conv.zero_grad()
st_conv(X_batch, L_tilde).sum().backward()
grad_norm = float(X_batch.grad.norm())
print(f"Gradient norm at the input after one backward pass: {grad_norm:.4f}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
(OUTPUT_DIR / "stconv_block.json").write_text(json.dumps({
    "nodes": N_NODES,
    "t_in": T_IN,
    "t_out": int(H_output.shape[1]),
    "batch": BATCH,
    "f_in": F_IN,
    "f_out": F_OUT,
    "chebyshev_order": ORDER,
    "temporal_kernel": KERNEL,
    "output_shape": list(H_output.shape),
    "parameter_count": parameter_count,
    "input_gradient_norm": round(grad_norm, 6),
    "laplacian_spectrum": [round(float(np.linalg.eigvalsh(L_tilde.numpy()).min()), 6),
                           round(float(np.linalg.eigvalsh(L_tilde.numpy()).max()), 6)],
}, indent=2) + "\n", encoding="utf-8")
print("Wrote output/stconv_block.json")
