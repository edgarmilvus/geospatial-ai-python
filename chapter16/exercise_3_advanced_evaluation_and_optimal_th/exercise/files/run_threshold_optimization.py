"""Harness for exercise 3 — the threshold sweep on a fixed probability map.

The numbers graded here are the counts: 1 979 roof pixels out of 16 384, 1 525 true
positives at the chosen threshold, and an F1 that peaks between 0.50 and 1.00 rather
than at an end of the sweep. The hand-counted metrics are also compared with sklearn,
because a utility that disagrees with the library is measuring something else.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np  # noqa: E402

from harness import Harness, load_listing  # noqa: E402

# From this session's run, and from the simulation's own parameters: 4 chips of
# 64 x 64, of which 1 979 pixels are roof.
TOTAL_PIXELS = 4 * 64 * 64
ROOF_PIXELS = 1979


def main():
    h = Harness("exercise 3 (threshold sweep)", FILES)
    module = load_listing(FILES / "threshold_optimization.py", "threshold_optimization")
    measured = module.main()

    # --- the sweep ---
    thresholds = measured["thresholds"]
    h.equal(len(thresholds), 17, "0.10 to 0.90 in steps of 0.05 is seventeen thresholds")
    h.close(thresholds[0], 0.10, "the sweep starts at 0.10")
    h.close(thresholds[-1], 0.90, "the sweep ends at 0.90")
    h.close(thresholds[1] - thresholds[0], 0.05, "the step is 0.05")

    # --- the data ---
    h.equal(measured["total_pixels"], TOTAL_PIXELS, "four 64 x 64 chips, pooled: 16 384 pixels")
    h.equal(measured["positive_pixels"], ROOF_PIXELS, "1 979 of them are roof")
    h.close(measured["positive_pixels"] / measured["total_pixels"], 0.1208,
            "the roofs are 12.08% of the pixels", tol=1e-4)

    # --- the answer ---
    h.close(measured["optimal_threshold"], 0.55, "the best F1 is at 0.55, not at 0.50")
    h.close(measured["max_f1"], 0.741, "the best F1 is 0.741", tol=5e-4)
    h.check(measured["f1_at_default"] < measured["max_f1"] - 0.05,
            "the default threshold loses (%.3f against %.3f)"
            % (measured["f1_at_default"], measured["max_f1"]))
    h.close(measured["sklearn_f1"], measured["max_f1"],
            "sklearn agrees with the hand-counted F1", tol=1e-9)

    # --- the counts behind it ---
    best = measured["at_best"]
    h.close(best["precision"], 0.714, "precision at the optimum is 0.714", tol=5e-4)
    h.close(best["recall"], 0.771, "recall at the optimum is 0.771", tol=5e-4)
    h.equal(best["tp"] + best["fn"], ROOF_PIXELS,
            "every roof pixel is either a TP or an FN")
    h.equal(best["tp"] + best["fp"], 2135,
            "2 135 pixels are predicted positive at 0.55")
    harmonic = 2 * best["precision"] * best["recall"] / (best["precision"] + best["recall"])
    h.close(harmonic, measured["max_f1"], "F1 is the harmonic mean of P and R", tol=1e-9)

    # --- the curve behaves like a threshold curve ---
    precision = np.array(measured["precision_curve"])
    recall = np.array(measured["recall_curve"])
    f1 = np.array(measured["f1_curve"])
    h.check(bool(np.all(np.diff(precision) >= -1e-12)),
            "precision never falls as the threshold rises")
    h.check(bool(np.all(np.diff(recall) <= 1e-12)),
            "recall never rises as the threshold rises")
    peak = int(np.argmax(f1))
    h.check(0 < peak < len(f1) - 1, "the F1 peak is interior, not at an end of the sweep")
    h.equal(peak, thresholds.index(measured["optimal_threshold"]),
            "the peak is the threshold the function returns")
    h.check(f1[peak] > f1[peak - 1] and f1[peak] > f1[peak + 1],
            "the F1 curve rises into the peak and falls after it")

    # --- the edge cases ---
    prediction = np.array([[0.1, 0.9], [0.4, 0.6]])
    target = np.zeros((2, 2), dtype=np.int8)
    precision_zero, recall_zero, f1_zero, tp, fp, fn = module.calculate_metrics(
        prediction, target, 0.95)
    h.equal((tp, fp, fn), (0, 0, 0), "a threshold nothing crosses counts no positives")
    h.equal((precision_zero, recall_zero, f1_zero), (0.0, 0.0, 0.0),
            "an empty prediction scores zero, not a division error")

    # A hand-checked case: two of four pixels are roof, one of them predicted.
    prediction = np.array([0.9, 0.2, 0.8, 0.1])
    target = np.array([1, 1, 0, 0], dtype=np.int8)
    precision_one, recall_one, f1_one, tp, fp, fn = module.calculate_metrics(
        prediction, target, 0.5)
    h.equal((tp, fp, fn), (1, 1, 1), "one TP, one FP and one FN in the toy case")
    h.close(precision_one, 0.5, "precision is one of two predicted positives")
    h.close(recall_one, 0.5, "recall is one of two true positives")
    h.close(f1_one, 0.5, "F1 is 0.5 when precision and recall are both 0.5")

    h.write_json("threshold_optimization.json", {
        "chips": {"count": 4, "size": 64, "total_pixels": measured["total_pixels"],
                  "roof_pixels": measured["positive_pixels"]},
        "sweep": {"thresholds": thresholds,
                  "f1": [round(v, 3) for v in measured["f1_curve"]],
                  "precision": [round(v, 3) for v in measured["precision_curve"]],
                  "recall": [round(v, 3) for v in measured["recall_curve"]]},
        "default_threshold": {"value": 0.5, "f1": round(measured["f1_at_default"], 3),
                              "precision": round(measured["precision_at_default"], 3),
                              "recall": round(measured["recall_at_default"], 3)},
        "optimal": {"threshold": measured["optimal_threshold"],
                    "f1": round(measured["max_f1"], 3),
                    "precision": round(best["precision"], 3),
                    "recall": round(best["recall"], 3),
                    "tp": best["tp"], "fp": best["fp"], "fn": best["fn"]},
        "sklearn_f1": round(measured["sklearn_f1"], 3),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (threshold sweep)", FILES).crash())
