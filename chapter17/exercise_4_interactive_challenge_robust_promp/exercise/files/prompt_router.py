import numpy as np
import scipy.ndimage as ndimage
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
THRESHOLD = 0.6

try:
    from segment_anything import sam_model_registry, SamPredictor
    HAVE_SAM = True
except ImportError:
    sam_model_registry = None
    SamPredictor = None
    HAVE_SAM = False

CHECKPOINT_PATH = OUTPUT_DIR / "sam_vit_b.pth"


# --- 1. The Defensive Extraction ------------------------------------------------
def process_sam_prompts(prompt_dictionary):
    """Safely turn a sparse user dictionary into keyword arguments for `predict`.

    Every key is read with `dict.get`, so a dialog that sent only a box, or only two
    points, produces a smaller argument set instead of a KeyError. A malformed value
    is a different thing from a missing one: a box of three numbers is not a box, and
    it is refused rather than dropped.
    """
    positive_points = prompt_dictionary.get('positive_points', [])
    negative_points = prompt_dictionary.get('negative_points', [])
    bounding_box = prompt_dictionary.get('bounding_box', None)

    sam_args = {}

    if positive_points or negative_points:
        all_coords = list(positive_points) + list(negative_points)
        # 1 for a positive point, 0 for a negative one: the SAM convention.
        labels = [1] * len(positive_points) + [0] * len(negative_points)
        for point in all_coords:
            if len(point) != 2:
                raise ValueError(f"a point needs two numbers, got {point!r}")
        sam_args['point_coords'] = np.array(all_coords, dtype=np.float64)
        sam_args['point_labels'] = np.array(labels, dtype=np.int64)

    if bounding_box is not None:
        if len(bounding_box) != 4:
            raise ValueError(f"a box needs four numbers, got {bounding_box!r}")
        sam_args['box'] = np.array(bounding_box, dtype=np.float64)

    print("--- Processed Prompts ---")
    print(f"Raw input dict: {prompt_dictionary}")
    print(f"Structured SAM args: { {key: value.tolist() for key, value in sam_args.items()} }")
    return sam_args


# --- 2. The Segmenter: Real If Present, a Stand-in Otherwise --------------------
class ThresholdSamPredictor:
    """Stand-in for `SamPredictor`, so the dictionary can be unpacked into a call."""

    def __init__(self, threshold=THRESHOLD):
        self.threshold = threshold
        self.features = None

    def set_image(self, image):
        self.features = image.astype(np.float32).mean(axis=2) / 255.0
        return self

    def predict(self, point_coords=None, point_labels=None, box=None,
                multimask_output=True, **kwargs):
        if self.features is None:
            raise RuntimeError("call set_image before predict")
        height, width = self.features.shape
        region = self.features > self.threshold

        if point_coords is not None:
            points = np.asarray(point_coords, dtype=np.float64).reshape(-1, 2)
            labels = (np.ones(len(points), dtype=int) if point_labels is None
                      else np.asarray(point_labels).reshape(-1))
            seed = np.zeros_like(region)
            for (x, y), label in zip(points, labels):
                column, row = int(round(x)), int(round(y))
                if label == 1 and 0 <= row < height and 0 <= column < width:
                    seed[row, column] = True
            region = region & _components_touching(region, seed) if seed.any() \
                else np.zeros_like(region)

        if box is not None:
            x_min, y_min, x_max, y_max = [int(round(value)) for value in box]
            inside = np.zeros_like(region)
            inside[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)] = True
            region = region & inside

        masks = region[None, :, :]
        scores = np.array([0.95 if region.any() else 0.3], dtype=np.float32)
        return masks, scores, np.zeros((1, 64, 64), dtype=np.float32)


def _components_touching(region, hint):
    labels, _ = ndimage.label(region)
    touching = sorted(set(int(value) for value in np.unique(labels[hint])) - {0})
    if not touching:
        return np.zeros_like(region)
    return np.isin(labels, touching)


def load_predictor(image):
    if HAVE_SAM and CHECKPOINT_PATH.exists():
        sam = sam_model_registry["vit_b"](checkpoint=str(CHECKPOINT_PATH))
        sam.eval()
        predictor = SamPredictor(sam)
        mode = "segment_anything (vit_b)"
    else:
        reason = ("segment_anything is not installed" if not HAVE_SAM
                  else f"{CHECKPOINT_PATH.name} is not present")
        print(f"[SAM] {reason}; using the threshold stand-in.")
        predictor = ThresholdSamPredictor()
        mode = "stand-in"
    predictor.set_image(image)
    return predictor, mode


# --- 3. A Patch to Segment ------------------------------------------------------
def build_patch(size=128, seed=12):
    """One bright building at rows 30-60, columns 70-100: 900 pixels."""
    rng = np.random.default_rng(seed)
    image = rng.integers(55, 105, size=(size, size, 3), dtype=np.uint8)
    image[30:60, 70:100, :] = np.array([230, 200, 190], dtype=np.uint8)
    return image


# --- 4. Execution ---------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image = build_patch()
    predictor, mode = load_predictor(image)
    print(f"Patch {image.shape}, segmenter: {mode}")

    test_cases = {
        "full": {
            'positive_points': [(85, 45)],
            'bounding_box': [60, 20, 110, 70],
            'negative_points': [(10, 10)],
        },
        "sparse": {
            'positive_points': [(85, 45)],
            # 'bounding_box' and 'negative_points' are missing
        },
        "negative_only": {
            'negative_points': [(10, 10)],
        },
        "empty": {},
    }

    results = {}
    for name, prompts in test_cases.items():
        print(f"\n=== Test case: {name} ===")
        sam_args = process_sam_prompts(prompts)
        # The whole point of the dictionary: it unpacks into the call.
        masks, scores, _ = predictor.predict(**sam_args)
        area = int(masks[0].sum())
        results[name] = {"keys": sorted(sam_args), "area": area,
                         "score": float(np.max(scores))}
        print(f"mask area: {area} pixels, score {float(np.max(scores)):.2f}")

    print("\n=== Test case: malformed box ===")
    try:
        process_sam_prompts({'bounding_box': [10, 10, 200]})
    except ValueError as error:
        print(f"[REFUSED] {error}")

    print("\nKeys accepted by the four cases:")
    for name, result in results.items():
        print(f"  {name:<14} {result['keys']}")

    return {"mode": mode, "results": results, "image_shape":
            tuple(int(v) for v in image.shape)}


if __name__ == "__main__":
    main()
