"""Harness for chapter 19, exercise 1 — the topology and the tensor it feeds.

The exercise is arithmetic with a deadline: 2016 five-minute steps of one week,
a twelve-step window and a three-step horizon leave 2002 windows, and the 70/15/15
split puts 1401 of them in training. The assertions check those counts, that the
Laplacian is the normalized operator, and that the target really is the speed
channel three steps after the window closes.
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
    h = Harness("exercise 1 (graph construction)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_graph_construction.py", "graph_construction")
    printed = log.getvalue()

    import numpy as np

    A = module.A
    L = module.L_hat
    X = module.X_features
    train, val, test = module.train_data, module.val_data, module.test_data

    # --- the graph ---
    h.equal(A.shape, (50, 50), "the network has fifty road links")
    h.check(bool((A == A.T).all()), "A is symmetric: every link is two-way")
    h.equal(int(A.diagonal().sum()), 0, "no link connects to itself")
    h.check(bool(np.isin(A, [0, 1]).all()), "A is binary after the sparsity cut")
    h.equal(int(A.sum()), 470, "470 directed cells = 235 road segments")
    h.equal(int(A.sum()) // 2, 235, "the run reports 235 road segments")

    # --- the normalized Laplacian ---
    h.equal(L.shape, (50, 50), "the operator is one row and column per node")
    h.check(bool(np.allclose(L, L.T)), "L_hat is symmetric")
    degrees = A.sum(axis=1) + 1
    h.check(bool(np.allclose(np.diag(L), 1.0 / degrees)),
            "the diagonal is 1/(degree+1), the self-loop weight")
    eigenvalues = np.linalg.eigvalsh(L)
    h.check(float(eigenvalues.max()) <= 1.0 + 1e-9,
            "the largest eigenvalue of a normalized adjacency is at most 1")
    h.check(float(eigenvalues.min()) > -1.0 - 1e-9,
            "the smallest eigenvalue stays above -1, so message passing is stable")

    # --- the feature tensor ---
    h.equal(X.shape, (2016, 50, 5), "one week of five-minute steps, 50 links, 5 features")
    h.check(bool(abs(X[..., 0].mean()) < 1e-9), "speed is z-scored to mean zero")
    h.check(bool(abs(X[..., 0].std() - 1.0) < 1e-6), "speed is z-scored to unit variance")
    h.check(bool(abs(X[..., 1].mean()) < 1e-9), "volume is z-scored to mean zero")
    h.close(float(X[0, 0, 2]), 0.0, "midnight encodes as sin(0) = 0")
    h.close(float(X[0, 0, 3]), 1.0, "midnight encodes as cos(0) = 1")
    h.close(float(X[0, 0, 4]), 1.0, "1 January 2023 is a Sunday: 6/6 = 1.0")
    h.check(bool(np.allclose(X[0, :, 2], X[0, 0, 2])),
            "the clock encoding is the same at every link")

    # --- the windows ---
    h.equal(len(train), 1401, "70% of 2002 windows are training samples")
    h.equal(len(val), 300, "15% are validation samples")
    h.equal(len(test), 301, "the rest are test samples")
    h.equal(list(module.X_train.shape), [1401, 12, 50, 5],
            "a training batch is (samples, T_hist, N, F)")
    h.equal(list(module.Y_train.shape), [1401, 3, 50],
            "a target batch is (samples, T_pred, N)")
    h.check(bool(np.allclose(module.Y_train[0], X[12:15, :, 0])),
            "the first target is the speed channel at steps 12-14, not at step 11")
    h.check(bool(np.allclose(train[1][0], X[1:13, :, :])),
            "the second window starts one step later: time is not shuffled")

    # --- what the reader sees ---
    h.contains(printed, "Final feature tensor X shape (T, N, F): (2016, 50, 5)",
               "the run prints the tensor shape")
    h.contains(printed, "Train samples: 1401 | Val samples: 300 | Test samples: 301",
               "the run prints the split")
    h.contains(printed, "Road segments in the network: 235",
               "the run prints the edge count")

    artefact = json.loads((FILES.parent / "output" / "graph_construction.json").read_text())
    h.equal(artefact["splits"], [1401, 300, 301], "the artefact records the split")
    h.equal(artefact["feature_shape"], [2016, 50, 5], "the artefact records the tensor")

    h.write_json("graph_construction_exercise.json", {
        "nodes": int(A.shape[0]),
        "edges": int(A.sum()) // 2,
        "degree_sum": int(A.sum()),
        "laplacian_trace": round(float(np.trace(L)), 6),
        "feature_shape": list(X.shape),
        "splits": [len(train), len(val), len(test)],
        "samples": len(train) + len(val) + len(test),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 1 (graph construction)", FILES).crash())
