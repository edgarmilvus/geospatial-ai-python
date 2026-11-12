import numpy as np
import scipy.ndimage as ndimage
from pathlib import Path

# --- Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
IMAGE_H, IMAGE_W = 256, 256
SEED = 4

# The wetland: an ellipse centred at (125, 125) with a 65-pixel north-south radius and
# a 55-pixel east-west one, which is 11 231 pixels of saturated ground.
CENTRE = (125, 125)
RADIUS = (65, 55)
BOX = [50, 50, 200, 200]          # [x_min, y_min, x_max, y_max], one large prompt

MIN_AREA_THRESHOLD = 6000         # square pixels: a wetland, not a puddle
THRESHOLD = 0.6

# Twelve single-pixel dropouts the segmenter leaves inside the field: the artefact the
# closing step of the exercise is for. A 3 x 3 element fills a one-pixel hole and
# leaves the outline alone; a bigger hole would survive, which is the lesson.
HOLES = [(90, 120), (92, 150), (100, 95), (110, 165), (120, 105), (125, 150),
         (135, 110), (140, 140), (150, 120), (155, 155), (105, 130), (145, 95)]

try:
    from segment_anything import sam_model_registry, SamPredictor
    HAVE_SAM = True
except ImportError:
    sam_model_registry = None
    SamPredictor = None
    HAVE_SAM = False

CHECKPOINT_PATH = OUTPUT_DIR / "sam_vit_b.pth"


# --- 1. The Segmenter: Real If Present, a Stand-in Otherwise --------------------
class BoxPromptStandIn:
    """Stand-in for a SAM predictor driven by one box prompt.

    It returns three hypotheses, as the real decoder does: the object itself, the
    object with a margin, and the whole box. The scores say which to believe, and the
    areas differ enough for the selection rule of this exercise to bite.
    """

    def __init__(self, threshold=THRESHOLD):
        self.threshold = threshold
        self.features = None

    def set_image(self, image):
        self.features = image.astype(np.float32).mean(axis=2) / 255.0
        return self

    def predict(self, box=None, multimask_output=True, **kwargs):
        if self.features is None:
            raise RuntimeError("call set_image before predict")
        x_min, y_min, x_max, y_max = [int(round(value)) for value in box]
        inside = np.zeros(self.features.shape, dtype=bool)
        inside[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)] = True

        region = inside & (self.features > self.threshold)
        for row, col in HOLES:
            region[row, col] = False

        # Nested on purpose: the margin contains the object, and the filled box
        # contains the margin. Choosing between them is choosing a scale.
        dilated = ndimage.binary_dilation(region, iterations=1)
        masks = np.stack([region, dilated, _filled_box(dilated)])
        scores = np.array([0.94, 0.86, 0.72], dtype=np.float32)
        return masks, scores, np.zeros((3, 64, 64), dtype=np.float32)


def _filled_box(region):
    rows = np.where(region.any(axis=1))[0]
    cols = np.where(region.any(axis=0))[0]
    filled = np.zeros_like(region)
    filled[rows.min():rows.max() + 1, cols.min():cols.max() + 1] = True
    return filled


def load_predictor(image):
    if HAVE_SAM and CHECKPOINT_PATH.exists():
        sam = sam_model_registry["vit_b"](checkpoint=str(CHECKPOINT_PATH))
        sam.eval()
        predictor = SamPredictor(sam)
        mode = "segment_anything (vit_b)"
    else:
        reason = ("segment_anything is not installed" if not HAVE_SAM
                  else f"{CHECKPOINT_PATH.name} is not present")
        print(f"[SAM] {reason}; using the box-prompt stand-in.")
        predictor = BoxPromptStandIn()
        mode = "stand-in"
    predictor.set_image(image)
    return predictor, mode


# --- 2. The Image and the Truth -------------------------------------------------
def build_patch(seed=SEED, height=IMAGE_H, width=IMAGE_W):
    """A bright wetland on darker vegetation, plus the land cover it stands for."""
    rng = np.random.default_rng(seed)
    image = rng.integers(70, 110, size=(height, width, 3), dtype=np.uint8)

    rows = np.arange(height)[:, None]
    cols = np.arange(width)[None, :]
    distance = (((rows - CENTRE[0]) / RADIUS[0]) ** 2 +
                ((cols - CENTRE[1]) / RADIUS[1]) ** 2)

    # The land cover truth is the whole ellipse; the spectral signature of saturated
    # ground stops just short of the field's edge, which is why a perfect IoU is not
    # on offer from a threshold.
    truth = distance < 1.0
    signature = distance < 0.94
    texture = rng.integers(-6, 7, size=(height, width, 3))
    image[signature] = np.clip(215 + texture[signature], 0, 255).astype(np.uint8)
    return image, truth


# --- 3. Selection and Refinement ------------------------------------------------
def to_candidates(masks, scores):
    return [{"mask": mask, "confidence": float(score), "area": int(mask.sum())}
            for mask, score in zip(masks, scores)]


def select_best_mask(predictions, area_threshold_sq_pixels):
    """Highest confidence among the masks that are at least the minimum area."""
    eligible = [candidate for candidate in predictions
                if candidate["area"] >= area_threshold_sq_pixels]
    if not eligible:
        print(f"Warning: no mask reached {area_threshold_sq_pixels} pixels; "
              f"falling back to the most confident one.")
        return max(predictions, key=lambda candidate: candidate["confidence"])["mask"]

    best = max(eligible, key=lambda candidate: candidate["confidence"])
    print(f"  eligible: {[c['area'] for c in eligible]} -> picked "
          f"confidence {best['confidence']:.2f}, {best['area']} pixels")
    return best["mask"]


def refine_mask(mask_array, size=3):
    """Morphological closing: fill the holes, leave the outline where it was."""
    structure = np.ones((size, size), dtype=bool)
    return ndimage.binary_closing(mask_array, structure=structure).astype(bool)


def iou(predicted, truth):
    intersection = float((predicted & truth).sum())
    union = float((predicted | truth).sum())
    return intersection / union if union else 1.0


# --- 4. Execution ---------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    image, truth = build_patch()
    print(f"Patch {image.shape}, the wetland is {int(truth.sum())} pixels "
          f"({100 * truth.mean():.1f}% of the scene)")

    predictor, mode = load_predictor(image)
    masks, scores, _ = predictor.predict(box=np.array(BOX, dtype=np.float64),
                                         multimask_output=True)
    candidates = to_candidates(masks, scores)

    print(f"\n--- {len(candidates)} hypotheses for one box prompt ({mode}) ---")
    for index, candidate in enumerate(candidates):
        print(f"  mask {index}: confidence {candidate['confidence']:.2f}, "
              f"area {candidate['area']} px")

    print(f"\nSelection with a {MIN_AREA_THRESHOLD}-pixel floor:")
    selected = select_best_mask(candidates, MIN_AREA_THRESHOLD)

    refined = refine_mask(selected)
    print(f"Refinement: closing a 3 x 3 element filled "
          f"{int(refined.sum()) - int(selected.sum())} pixels "
          f"({int(selected.sum())} -> {int(refined.sum())}), one per dropout")
    print(f"IoU against the land cover truth: {iou(refined, truth):.4f}")

    # The floor is what turns the rule from "most confident" into "large enough":
    # at 12 000 no tight mask qualifies and the box-filling hypothesis wins.
    print("\nThe same rule with a 12 000-pixel floor:")
    select_best_mask(candidates, 12_000)
    print("And with a 20 000-pixel floor, which nothing reaches:")
    select_best_mask(candidates, 20_000)

    np.save(OUTPUT_DIR / "selected_mask.npy", refined)
    print(f"\nWrote selected_mask.npy: {refined.shape} {refined.dtype}, "
          f"{int(refined.sum())} pixels")

    return {
        "mode": mode,
        "image_shape": tuple(int(v) for v in image.shape),
        "truth_pixels": int(truth.sum()),
        "candidates": [(c["confidence"], c["area"]) for c in candidates],
        "selected_area": int(selected.sum()),
        "refined_area": int(refined.sum()),
        "iou": iou(refined, truth),
        "selected": selected,
        "refined": refined,
        "truth": truth,
        "mask_file": "selected_mask.npy",
    }


if __name__ == "__main__":
    main()
