"""Harness for chapter 19, exercise 3 — a model that learns, on a fixed seed.

Three things are graded: the split arithmetic (268 windows, 160/40/68), the fact
that training actually reduces the loss rather than merely running, and the
metrics on the held-out tail — a mean absolute error of a couple of km/h and an
R^2 well above zero, which is what separates a model from a moving average.
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
    h = Harness("exercise 3 (STGCN training and HPO)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_train_stgcn.py", "train_stgcn")
    printed = log.getvalue()

    import numpy as np

    # --- the split ---
    total = module.total
    h.equal(total, 268, "a day of 288 steps minus 18 history and 3 horizon leaves 268 windows")
    h.equal(len(module.X_train), 160, "60% of the windows are training data")
    h.equal(len(module.X_val), 40, "15% are validation data")
    h.equal(len(module.X_test), 68, "the remaining 25% is the test tail")
    h.equal(len(module.X_train) + len(module.X_val) + len(module.X_test), total,
            "the three splits partition the windows, with no overlap")
    h.equal(tuple(module.X_train.shape[1:]), (18, 30, 3),
            "an input window is 18 steps of 30 links and 3 features")
    h.equal(tuple(module.Y_train.shape[1:]), (3, 30),
            "a target is three future speeds for 30 links")

    # --- the graph operator the model consumes ---
    lt = module.L_TILDE.numpy()
    h.check(bool(np.allclose(lt, lt.T, atol=1e-5)), "the scaled Laplacian is symmetric")
    spectrum = np.linalg.eigvalsh(lt)
    h.check(float(spectrum.min()) >= -1.0 - 1e-5 and float(spectrum.max()) <= 1.0 + 1e-5,
            "its spectrum sits inside [-1, 1], where Chebyshev terms are stable")

    # --- the search ---
    grid = module.grid_results
    h.equal(len(grid), 8, "the grid visits 2 orders x 2 kernels x 2 widths")
    h.equal({row["order"] for row in grid}, {2, 3}, "both Chebyshev orders were tried")
    h.equal({row["kernel"] for row in grid}, {3, 5}, "both temporal kernels were tried")
    best_order, best_kernel, best_hidden, best_val = module.best
    h.close(best_val, min(row["val_loss"] for row in grid), tol=1e-5,
            message="the chosen configuration is the one with the lowest validation loss")

    # --- the training curve ---
    losses = module.losses
    h.equal(len(losses), 8, "the final model trains for eight epochs")
    h.check(losses[-1] < losses[0] * 0.5,
            "training loss falls by more than half (%.3f -> %.3f)"
            % (losses[0], losses[-1]))
    h.check(losses[-1] < losses[-2], "the last epoch improves on the one before it")
    h.check(all(b <= a for a, b in zip(losses, losses[1:])),
            "training loss never rises: the fixed seed gives a monotone curve")
    h.check(min(module.val_losses) < module.val_losses[0],
            "validation loss improves on the first epoch, so the model generalizes")
    h.check(losses[-1] < min(module.val_losses),
            "training loss ends below the best validation loss (mild overfitting)")

    # --- the metrics on the held-out tail ---
    mae = module.mae
    rmse = module.rmse
    r2 = module.r2
    h.check(mae < 5.0, "mean absolute error is under 5 km/h (%.2f)" % mae)
    h.check(rmse < 6.0, "root mean square error is under 6 km/h (%.2f)" % rmse)
    h.check(rmse > mae, "RMSE exceeds MAE, as it must for the same residuals")
    h.check(r2 > 0.5, "R^2 on the test tail is above 0.5 (%.3f)" % r2)
    h.check(r2 < 1.0, "R^2 stays below a perfect fit (%.3f)" % r2)

    horizon_mae = module.horizon_mae
    h.equal(len(horizon_mae), 3, "the error is reported for each of three horizons")
    h.check(horizon_mae[0] <= horizon_mae[-1],
            "the five-minute horizon is not harder than the fifteen-minute one")

    # --- the model itself ---
    parameters = sum(p.numel() for p in module.model.parameters())
    h.equal(parameters, 6_435, "the trained model holds 6 435 parameters")
    predicted = module.predicted_speed
    h.equal(predicted.shape, (68, 3, 30), "one prediction per window, horizon and link")
    h.check(bool(np.isfinite(predicted).all()), "every prediction is finite")
    h.check(float(predicted.min()) > 0, "no prediction is a negative speed")

    # --- the figure ---
    figure = FILES.parent / "output" / "stgcn_training.png"
    h.check(figure.exists(), "the run wrote the loss and forecast figure")
    if figure.exists():
        h.equal(figure.read_bytes()[:8], b"\x89PNG\r\n\x1a\n",
                "the figure is a PNG, not an empty file")
        h.check(figure.stat().st_size > 20_000, "the figure has real content")

    # --- what the reader sees ---
    h.contains(printed, "Windows: 268 total | 160 train | 40 val | 68 test",
               "the run prints the split")
    h.contains(printed, "Best configuration:", "the run prints the winning configuration")
    h.contains(printed, "Segmented MAE by horizon:", "the run reports per-horizon error")

    artefact = json.loads((FILES.parent / "output" / "stgcn_training.json").read_text())
    h.equal(artefact["windows"]["total"], 268, "the artefact records the window count")
    h.check(artefact["metrics"]["r2"] > 0.5, "the artefact records a positive R^2")

    h.write_json("stgcn_training_exercise.json", {
        "windows": artefact["windows"],
        "best": artefact["best"],
        "train_loss": [round(v, 5) for v in losses],
        "val_loss": [round(v, 5) for v in module.val_losses],
        "metrics": {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4)},
        "horizon_mae": horizon_mae,
        "parameter_count": parameters,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (STGCN training and HPO)", FILES).crash())
