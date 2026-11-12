import numpy as np
import scipy.ndimage as ndimage
from pathlib import Path

# --- 1. Configuration ---
MODEL_TYPE = "vit_b"          # the smallest SAM encoder: the right one to prototype with
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
CHECKPOINT_PATH = OUTPUT_DIR / f"sam_{MODEL_TYPE}.pth"   # a 375 MB download, not shipped
THRESHOLD = 0.6                # the stand-in's decision boundary, on mean intensity

# The real API is imported when it is installed. It is not a dependency of this book:
# the package is not on PyPI and the weights are a 375 MB download.
try:
    from segment_anything import sam_model_registry, SamPredictor
    HAVE_SAM = True
except ImportError:
    sam_model_registry = None
    SamPredictor = None
    HAVE_SAM = False


# --- 2. The Stand-in for the Segmenter ------------------------------------------
class ThresholdSamPredictor:
    """A small, deterministic stand-in for `SamPredictor`.

    It is not a model: it is the same interface, so the chapter's prompt handling runs
    without the package. `set_image` keeps a one-number feature per pixel (the mean of
    the three bands) and `predict` returns the connected bright region that contains
    the prompted point, cut to the prompt box, as three masks with a score each —
    the shape and the ambiguity of SAM's output.
    """

    def __init__(self, threshold=THRESHOLD):
        self.threshold = threshold
        self.image = None
        self.features = None

    def set_image(self, image):
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError("the stand-in wants an HxWx3 uint8 image")
        self.image = image
        self.features = image.astype(np.float32).mean(axis=2) / 255.0
        return self

    def predict(self, point_coords=None, point_labels=None, box=None,
                multimask_output=True, **kwargs):
        if self.features is None:
            raise RuntimeError("call set_image before predict")
        height, width = self.features.shape
        region = self.features > self.threshold
        if not region.any():
            region = np.zeros((height, width), dtype=bool)

        if point_coords is not None:
            points = np.asarray(point_coords, dtype=np.float64).reshape(-1, 2)
            labels = (np.ones(len(points), dtype=int) if point_labels is None
                      else np.asarray(point_labels).reshape(-1))
            positive = np.zeros_like(region)
            for (x, y), label in zip(points, labels):
                # (x, y) — the SAM convention: x is the column, y is the row.
                column, row = int(round(x)), int(round(y))
                if label == 1 and 0 <= row < height and 0 <= column < width:
                    positive[row, column] = True
            if positive.any():
                # Keep only the bright blob the prompt landed on, as SAM would.
                region = region & _components_touching(region, positive)
            else:
                region = np.zeros_like(region)

        if box is not None:
            x_min, y_min, x_max, y_max = [int(round(value)) for value in box]
            inside = np.zeros_like(region)
            inside[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)] = True
            region = region & inside

        # Three hypotheses, as `multimask_output=True` returns: the object itself, a
        # margin around it and its bounding box. The scores say which to trust.
        masks = np.stack([
            region,
            ndimage.binary_dilation(region, iterations=2),
            _filled_box(region),
        ]).astype(bool)
        scores = np.array([0.96, 0.88, 0.71], dtype=np.float32)
        if not region.any():
            scores = np.array([0.34, 0.31, 0.29], dtype=np.float32)

        # A coarse logit map, the shape the real decoder returns (64 x 64).
        logits = np.stack([_downsample(mask, 64) for mask in masks]).astype(np.float32)
        return (masks[:3] if multimask_output else masks[:1],
                scores[:3] if multimask_output else scores[:1],
                logits[:3] if multimask_output else logits[:1])


def _components_touching(region, hint):
    labels, _ = ndimage.label(region)
    touching = sorted(set(int(value) for value in np.unique(labels[hint])) - {0})
    if not touching:
        return np.zeros_like(region)
    return np.isin(labels, touching)


def _filled_box(region):
    if not region.any():
        return region
    rows = np.where(region.any(axis=1))[0]
    cols = np.where(region.any(axis=0))[0]
    filled = np.zeros_like(region)
    filled[rows.min():rows.max() + 1, cols.min():cols.max() + 1] = True
    return filled


def _downsample(mask, size):
    rows = (np.linspace(0, mask.shape[0] - 1, size)).astype(int)
    cols = (np.linspace(0, mask.shape[1] - 1, size)).astype(int)
    return mask[np.ix_(rows, cols)].astype(np.float32) * 10.0 - 5.0


# --- 3. Choosing the Real Model or the Stand-in ---------------------------------
def load_predictor(checkpoint_path=CHECKPOINT_PATH, model_type=MODEL_TYPE):
    """Return (predictor, mode). The weights are never downloaded here."""
    if HAVE_SAM and checkpoint_path.exists():
        sam = sam_model_registry[model_type](checkpoint=str(checkpoint_path))
        sam.eval()
        return SamPredictor(sam), f"segment_anything ({model_type})"

    if HAVE_SAM:
        reason = f"{checkpoint_path.name} is not present"
    else:
        reason = "segment_anything is not installed"
    print(f"[SAM] {reason}; using the threshold stand-in for the segmenter.")
    return ThresholdSamPredictor(), "stand-in"


# --- 4. Simulated Geospatial Input ----------------------------------------------
def build_patch(seed=7, size=256):
    """A 256 x 256 RGB patch with one bright building that is not square."""
    rng = np.random.default_rng(seed)
    image = rng.integers(60, 121, size=(size, size, 3), dtype=np.uint8)
    # Rows 50..80 and columns 100..140: 30 x 40 pixels. The rectangle is deliberately
    # not square, so a (row, column) prompt cannot be mistaken for an (x, y) one.
    image[50:80, 100:140, :] = np.array([235, 170, 160], dtype=np.uint8)
    return image


# --- 5. Prediction --------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    image = build_patch()
    print(f"Image: {image.shape} {image.dtype}, one 30 x 40 building at "
          f"rows 50-80, columns 100-140")

    predictor, mode = load_predictor()
    predictor.set_image(image)
    print(f"Encoder: {mode}. Image ({image.shape[0]}x{image.shape[1]}) encoded once.")

    # (x, y): 120 is a column, 65 is a row. The centre of the building is (120, 65).
    input_point = np.array([[120, 65]])
    input_label = np.array([1])            # 1 = foreground, 0 = background

    masks, scores, logits = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
    )

    print(f"\n--- Prediction Results ({mode}) ---")
    print(f"Total masks generated: {masks.shape[0]}")
    print(f"Masks shape: {masks.shape}, logits shape: {logits.shape}")
    print(f"Confidence scores: {np.round(scores, 2)}")

    best_index = int(np.argmax(scores))
    best_mask = masks[best_index]
    best_score = float(scores[best_index])

    print(f"Selected mask index {best_index} with score {best_score:.2f}")
    print(f"Area segmented (pixels): {int(best_mask.sum())}")
    print(f"Best mask shape: {best_mask.shape} | dtype: {best_mask.dtype}")
    print(f"The prompt (x=120, y=65) falls inside the mask: {bool(best_mask[65, 120])}")

    return {
        "mode": mode,
        "image_shape": tuple(int(v) for v in image.shape),
        "masks_shape": tuple(int(v) for v in masks.shape),
        "logits_shape": tuple(int(v) for v in logits.shape),
        "scores": [float(value) for value in scores],
        "best_index": best_index,
        "best_score": best_score,
        "segmented_pixels": int(best_mask.sum()),
        "prompt_inside": bool(best_mask[65, 120]),
        "predictor": predictor,
        "image": image,
    }


if __name__ == "__main__":
    main()
