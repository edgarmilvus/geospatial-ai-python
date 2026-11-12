import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score

# The sweep the exercise asks for: 0.10 to 0.90 in steps of 0.05, seventeen points.
THRESHOLDS = np.arange(0.1, 0.95, 0.05)

SEED = 11
N_TILES = 4
TILE = 64

# A classifier is not a coin: its probability map is drawn around a different mean on
# roof pixels than on background, with overlap wide enough that no threshold is free.
FG_MEAN, FG_SD = 0.62, 0.10
BG_MEAN, BG_SD = 0.38, 0.10


# --- 1. A Probability Map and Its Ground Truth ---
def simulate_tile(rng, size=TILE):
    """One chip: two rectangular roofs, and a probability map with overlap."""
    target = np.zeros((size, size), dtype=np.int8)
    for _ in range(2):
        height = int(rng.integers(10, 22))
        width = int(rng.integers(12, 26))
        row = int(rng.integers(2, size - height - 2))
        col = int(rng.integers(2, size - width - 2))
        target[row:row + height, col:col + width] = 1

    # Background first, then the roofs overwrite it: a pixel is one or the other.
    prediction = np.clip(rng.normal(BG_MEAN, BG_SD, size=(size, size)), 0.01, 0.99)
    prediction[target == 1] = np.clip(
        rng.normal(FG_MEAN, FG_SD, size=int(target.sum())), 0.01, 0.99)
    return prediction, target


def simulate_batch(seed=SEED, n_tiles=N_TILES):
    rng = np.random.default_rng(seed)
    tiles = [simulate_tile(rng) for _ in range(n_tiles)]
    return [tile[0] for tile in tiles], [tile[1] for tile in tiles]


# --- 2. The Metrics, Counted by Hand ---
def calculate_metrics(prediction, target, threshold):
    """TP, FP, FN from one threshold, then precision, recall and F1.

    The counts are computed here rather than imported because the exercise is about
    them: precision is TP / (TP + FP), recall is TP / (TP + FN), and F1 is their
    harmonic mean. sklearn is used at the end of the module as the cross-check.
    """
    binary = (prediction >= threshold).astype(np.int8)
    truth = target.astype(np.int8)

    tp = int(np.sum((binary == 1) & (truth == 1)))
    fp = int(np.sum((binary == 1) & (truth == 0)))
    fn = int(np.sum((binary == 0) & (truth == 1)))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


# --- 3. The Sweep ---
def find_optimal_threshold(predictions_list, targets_list, thresholds=THRESHOLDS):
    """Score every threshold on the pooled pixels and keep the best F1.

    Pooling before scoring matters: a per-tile average lets one nearly empty tile
    outvote a dense one.
    """
    all_predictions = np.concatenate([p.ravel() for p in predictions_list])
    all_targets = np.concatenate([t.ravel() for t in targets_list])

    history = {"thresholds": [], "precision": [], "recall": [], "f1": [],
               "tp": [], "fp": [], "fn": []}
    best_f1, optimal = -1.0, 0.5
    for threshold in thresholds:
        precision, recall, f1, tp, fp, fn = calculate_metrics(
            all_predictions, all_targets, threshold)
        history["thresholds"].append(round(float(threshold), 2))
        history["precision"].append(precision)
        history["recall"].append(recall)
        history["f1"].append(f1)
        history["tp"].append(tp)
        history["fp"].append(fp)
        history["fn"].append(fn)
        if f1 > best_f1:
            best_f1, optimal = f1, round(float(threshold), 2)

    best_index = history["thresholds"].index(optimal)
    return {
        "optimal_threshold": optimal,
        "max_f1": best_f1,
        "metrics_history": history,
        "at_best": {
            "precision": history["precision"][best_index],
            "recall": history["recall"][best_index],
            "tp": history["tp"][best_index],
            "fp": history["fp"][best_index],
            "fn": history["fn"][best_index],
        },
        "positive_pixels": int(all_targets.sum()),
        "total_pixels": int(all_targets.size),
    }


# --- 4. The Report ---
def main():
    predictions, targets = simulate_batch()
    result = find_optimal_threshold(predictions, targets)

    print(f"{len(predictions)} chips of {TILE} x {TILE}: "
          f"{result['positive_pixels']} roof pixels of {result['total_pixels']} "
          f"({100 * result['positive_pixels'] / result['total_pixels']:.2f}%)")

    print("\nthreshold  precision  recall      f1       tp      fp      fn")
    history = result["metrics_history"]
    for index, threshold in enumerate(history["thresholds"]):
        print(f"{threshold:9.2f}  {history['precision'][index]:9.3f}  "
              f"{history['recall'][index]:6.3f}  {history['f1'][index]:6.3f}  "
              f"{history['tp'][index]:6d}  {history['fp'][index]:6d}  "
              f"{history['fn'][index]:6d}")

    # Where the default sits, for comparison: the sweep only earns its keep if the
    # answer is not 0.5.
    default_index = history["thresholds"].index(0.5)
    print(f"\nF1 at the default 0.50: {history['f1'][default_index]:.3f} "
          f"(precision {history['precision'][default_index]:.3f}, "
          f"recall {history['recall'][default_index]:.3f})")
    print(f"Optimal Threshold: {result['optimal_threshold']:.2f}")
    print(f"Max F1 Score: {result['max_f1']:.3f}")
    best = result["at_best"]
    print(f"At the optimum: precision {best['precision']:.3f}, recall {best['recall']:.3f}, "
          f"{best['tp']} TP / {best['fp']} FP / {best['fn']} FN")

    # The cross-check: the hand-counted counts and sklearn must agree, or one of the
    # two is measuring something else.
    all_predictions = np.concatenate([p.ravel() for p in predictions])
    all_targets = np.concatenate([t.ravel() for t in targets])
    sklearn_f1 = f1_score(all_targets, (all_predictions >= result["optimal_threshold"]).astype(int),
                          zero_division=0)
    print(f"sklearn f1_score at the optimum: {sklearn_f1:.3f}")

    return {
        "optimal_threshold": result["optimal_threshold"],
        "max_f1": result["max_f1"],
        "f1_at_default": history["f1"][default_index],
        "precision_at_default": history["precision"][default_index],
        "recall_at_default": history["recall"][default_index],
        "at_best": result["at_best"],
        "positive_pixels": result["positive_pixels"],
        "total_pixels": result["total_pixels"],
        "thresholds": history["thresholds"],
        "f1_curve": history["f1"],
        "precision_curve": history["precision"],
        "recall_curve": history["recall"],
        "sklearn_f1": float(sklearn_f1),
        "predictions": predictions,
        "targets": targets,
    }


if __name__ == "__main__":
    main()
