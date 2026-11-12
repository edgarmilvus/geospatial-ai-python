"""Harness for chapter 19, example 2 — the generated graph and the STGCN block.

The numbers here are properties of the architecture, not of this run: a 4x4 grid
has 24 street segments, so the degree sum is 48; the block's parameter count is
fixed by its four layers; and the same seed must produce the same forecast twice.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("example 2 (simplified STGCN)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_stgcn_forward.py", "stgcn_forward")
        second = module.stgcn_block(module.X_features, module.A_tilde)
    printed = log.getvalue()

    import numpy as np
    import torch

    A = module.A
    N = module.N

    # --- the generated road network ---
    h.equal(N, 16, "a 4x4 intersection grid has sixteen nodes")
    h.equal(module.G.number_of_edges(), 24, "the grid has 24 two-way street segments")
    h.equal(A.shape, (16, 16), "A is one row and column per intersection")
    h.check(bool((A == A.T).all()), "the grid adjacency is symmetric")
    h.equal(int(A.diagonal().sum()), 0, "the base adjacency carries no self-loops")
    h.equal(int(A.sum()), 48, "degree sum is twice the edge count")
    degree = A.sum(axis=1).astype(int)
    h.equal(int(degree.min()), 2, "corner intersections have degree 2")
    h.equal(int(degree.max()), 4, "interior intersections have degree 4")
    h.equal(float(degree.mean()), 3.0, "average degree of a 4x4 grid is 3")

    # --- the normalized operator ---
    at = module.A_tilde.numpy()
    h.check(bool(np.allclose(at, at.T)), "A_tilde is symmetric")
    h.check(bool(np.allclose(np.diag(at), 1.0 / (degree + 1))),
            "A_tilde puts 1/(degree+1) on the diagonal (the self-loop weight)")

    # --- the block ---
    X = module.X_features
    h.equal(tuple(X.shape), (16, 12, 2), "the feature tensor is (nodes, time, features)")
    h.equal(tuple(module.H_hidden.shape), (16, 12, 32),
            "the ST-Conv output keeps T and N and maps 2 features to 32")
    h.equal(tuple(module.predicted_traffic.shape), (16, 1),
            "one speed prediction per intersection")
    h.check(bool(torch.isfinite(module.predicted_traffic).all()),
            "every prediction is a finite number")

    parameters = (sum(p.numel() for p in module.stgcn_block.parameters())
                  + sum(p.numel() for p in module.final_predictor.parameters()))
    h.equal(parameters, 13_569, "the block and the head hold 13 569 parameters")
    h.equal(sum(p.numel() for p in module.stgcn_block.parameters()), 13_536,
            "the block alone holds 13 536: 224 + 1024 + 12288")
    h.equal(sum(p.numel() for p in module.final_predictor.parameters()), 33,
            "the head is a 32-to-1 linear layer, weights plus bias")

    # --- determinism: the same input must give the same forecast ---
    # H_hidden has already been through the ReLU the listing applies after the block.
    h.check(bool(torch.allclose(torch.relu(second), module.H_hidden)),
            "a second forward pass with the same seed is bit-identical")

    # --- what the reader sees ---
    h.contains(printed, "Road network: 16 intersections, 24 street segments",
               "the run reports the graph it generated")
    h.contains(printed, "Hidden state output shape (N, T, Hidden): (16, 12, 32)",
               "the run prints the hidden shape")
    h.contains(printed, "Parameters in the block and the head: 13569",
               "the run prints the parameter count")

    artefact = json.loads((FILES.parent / "output" / "stgcn_forward.json").read_text())
    h.equal(artefact["degree_sum"], 48, "the artefact records the degree sum")
    h.equal(len(artefact["predicted_speed"]), 16, "the artefact holds sixteen forecasts")

    h.write_json("stgcn_forward_example.json", {
        "nodes": int(N),
        "edges": int(module.G.number_of_edges()),
        "degree_sum": int(A.sum()),
        "average_degree": round(float(degree.mean()), 3),
        "feature_shape": list(X.shape),
        "hidden_shape": list(module.H_hidden.shape),
        "parameter_count": parameters,
        "prediction_range": [round(float(module.predicted_traffic.detach().min()), 4),
                             round(float(module.predicted_traffic.detach().max()), 4)],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (simplified STGCN)", FILES).crash())
