# Required structure for Exercise 3.
# A sketch, not a program: the two functions are the interface to fill in.
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score


def calculate_metrics(prediction: np.ndarray, target: np.ndarray,
                      threshold: float) -> tuple:
    """Calculates P, R, F1 based on a specific threshold."""
    # 1. Convert prediction to binary mask using the threshold.
    # 2. Flatten arrays for metric calculation.
    # 3. Calculate TP, FP, FN, and the resulting metrics.
    pass


def find_optimal_threshold(predictions_list: list, targets_list: list) -> float:
    """Iterates thresholds to find the maximum F1 score."""
    thresholds = np.arange(0.1, 0.95, 0.05)
    best_f1 = -1
    optimal_t = 0.5

    # Loop through thresholds, calculate aggregate metrics, and update best_f1.
    pass


# Expected output format:
# Optimal Threshold: 0.65
# Max F1 Score: 0.891
