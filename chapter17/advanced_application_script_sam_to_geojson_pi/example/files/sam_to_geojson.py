import json
import numpy as np
import rasterio
import geopandas as gpd
from pathlib import Path
from shapely.geometry import shape
from rasterio.features import shapes
from rasterio.transform import Affine

# --- 1. Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
IMAGE_PATH = OUTPUT_DIR / "industrial_park.tif"
OUTPUT_PATH = OUTPUT_DIR / "mapped_warehouses.geojson"

ROWS, COLS = 1000, 1000
ORIGIN = (500000.0, 4200000.0)     # UTM zone 17N, one metre per pixel
CRS = "EPSG:32617"
THRESHOLD = 0.6                    # the stand-in's decision boundary

# Four bounding-box prompts, in SAM's order: [x_min, y_min, x_max, y_max], pixels.
WAREHOUSE_PROMPTS = np.array([
    [150, 200, 350, 450],   # a large structure in the north-west
    [500, 100, 700, 300],   # north-centre
    [800, 600, 950, 750],   # south-east
    [100, 700, 250, 850],   # a smaller one beside it
])

# The roofs actually on the ground, as (row_start, row_stop, col_start, col_stop). Each
# sits strictly inside its prompt: the box says "somewhere here", the segmenter says
# "exactly this".
WAREHOUSES = [(210, 440, 160, 340), (110, 290, 510, 690),
              (610, 740, 810, 940), (710, 840, 110, 240)]

# The real API, when the package and the weights are both installed.
try:
    from segment_anything import sam_model_registry, SamPredictor
    HAVE_SAM = True
except ImportError:
    sam_model_registry = None
    SamPredictor = None
    HAVE_SAM = False

CHECKPOINT_PATH = OUTPUT_DIR / "sam_vit_b.pth"


# --- 2. The Segmenter: Real If Present, a Stand-in Otherwise --------------------
class BoxRefinePredictor:
    """Stand-in for `SamPredictor` driven by a box prompt.

    The step it stands in for is the network. What it keeps is the contract: a box
    goes in, a mask of the whole image comes out, tighter than the box, with a score.
    The mask is the bright region inside the box, so the refinement is measurable.
    """

    def __init__(self, threshold=THRESHOLD):
        self.threshold = threshold
        self.features = None

    def set_image(self, image):
        self.features = image.astype(np.float32).mean(axis=2) / 255.0
        return self

    def predict(self, box, multimask_output=False, **kwargs):
        if self.features is None:
            raise RuntimeError("call set_image before predict")
        height, width = self.features.shape
        x_min, y_min, x_max, y_max = [int(round(value)) for value in box]

        inside = np.zeros((height, width), dtype=bool)
        inside[max(y_min, 0):max(y_max, 0), max(x_min, 0):max(x_max, 0)] = True
        mask = inside & (self.features > self.threshold)

        masks = mask[None, :, :]
        scores = np.array([0.93 if mask.any() else 0.31], dtype=np.float32)
        logits = np.zeros((1, 64, 64), dtype=np.float32)
        return masks, scores, logits


def load_predictor(image):
    """Return (predictor, mode): the real SAM when it can run, the stand-in otherwise."""
    if HAVE_SAM and CHECKPOINT_PATH.exists():
        sam = sam_model_registry["vit_b"](checkpoint=str(CHECKPOINT_PATH))
        sam.eval()
        predictor = SamPredictor(sam)
        mode = "segment_anything (vit_b)"
    else:
        reason = ("segment_anything is not installed" if not HAVE_SAM
                  else f"{CHECKPOINT_PATH.name} is not present")
        print(f"[SAM] {reason}; using the box-refinement stand-in.")
        predictor = BoxRefinePredictor()
        mode = "stand-in"
    predictor.set_image(image)
    return predictor, mode


def segment_boxes(predictor, boxes):
    """One mask per box, at the image's resolution."""
    masks = []
    for box in boxes:
        predicted, scores, _ = predictor.predict(box=np.asarray(box, dtype=np.float64),
                                                 multimask_output=False)
        masks.append(predicted[0])
    return np.stack(masks)


# --- 3. The Input Tile, on Disk and Georeferenced -------------------------------
def build_tile(path=IMAGE_PATH):
    """Write a 1000 x 1000 industrial park with four roofs."""
    rng = np.random.default_rng(21)
    # Ground texture is low-frequency — parcels, shadow, soil — so it is drawn coarse and
    # repeated. Per-pixel noise would look the same at 1 m and cost 2 MB of GeoTIFF.
    base = rng.integers(70, 115, size=(ROWS // 8, COLS // 8, 3), dtype=np.uint8)
    tile = np.repeat(np.repeat(base, 8, axis=0), 8, axis=1)
    for row_start, row_stop, col_start, col_stop in WAREHOUSES:
        texture = rng.integers(-8, 9, size=(row_stop - row_start,
                                            col_stop - col_start, 3))
        tile[row_start:row_stop, col_start:col_stop, :] = np.clip(
            218 + texture, 0, 255).astype(np.uint8)

    transform = Affine(1.0, 0.0, ORIGIN[0], 0.0, -1.0, ORIGIN[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=ROWS, width=COLS, count=3,
                       dtype="uint8", crs=CRS, transform=transform,
                       compress="deflate") as dst:
        for band in range(3):
            dst.write(tile[:, :, band], band + 1)
    print(f"Wrote {path.name}: {COLS} x {ROWS} at 1 m, {CRS}")
    return path


# --- 4. The Bridge: Masks to GeoJSON -------------------------------------------
def vectorize_masks(masks_array, transform, crs):
    """A stack of binary masks (N, H, W) becomes one polygon per object."""
    rows = []
    for index, mask in enumerate(masks_array):
        # rasterio.features.shapes needs an integer raster, not a boolean one.
        mask = mask.astype(np.uint8)
        for geometry, value in shapes(mask, transform=transform, connectivity=8):
            if value != 1:       # foreground only; 0 is background
                continue
            polygon = shape(geometry)
            rows.append({
                "prompt_id": index,
                "type": "Industrial Warehouse",
                # The transform already put the ring in metres, so this is m².
                "area_sqm": round(polygon.area, 1),
                "geometry": polygon,
            })
    if not rows:
        return gpd.GeoDataFrame()
    return gpd.GeoDataFrame(rows, crs=crs)


# --- 5. The Pipeline ------------------------------------------------------------
def run_sam_geo_segmentation(image_path=IMAGE_PATH, prompts=WAREHOUSE_PROMPTS,
                             output_path=OUTPUT_PATH):
    """Load, segment, vectorize, save."""
    if not Path(image_path).exists():
        build_tile(image_path)

    with rasterio.open(image_path) as src:
        # Rasterio is (band, row, col); the segmenter wants (row, col, band).
        image = src.read([1, 2, 3]).transpose(1, 2, 0)
        transform = src.transform
        crs = src.crs
    print(f"Image loaded (shape {image.shape}). CRS: {crs}")

    predictor, mode = load_predictor(image)
    print(f"Segmenter: {mode}")
    print(f"Starting segmentation with {len(prompts)} bounding-box prompts...")

    masks = segment_boxes(predictor, prompts)
    print(f"Prediction complete. {masks.shape[0]} masks of "
          f"{masks.shape[1]} x {masks.shape[2]}.")

    gdf = vectorize_masks(masks, transform, crs)
    print(f"\n--- SUCCESS ---")
    print(f"Successfully mapped {len(gdf)} features, "
          f"{gdf['area_sqm'].sum():,.0f} m² in total.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    collection = json.loads(gdf.to_json())
    # GeoJSON's optional crs member is what tells a reader these are metres.
    collection["crs"] = {"type": "name", "properties": {"name": crs.to_string()}}
    output_path.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    print(f"Results saved to {output_path.name}")

    return {
        "mode": mode,
        "image_shape": tuple(int(v) for v in image.shape),
        "mask_shape": tuple(int(v) for v in masks.shape),
        "mask_areas": [int(mask.sum()) for mask in masks],
        "feature_count": len(gdf),
        "areas_sqm": [float(value) for value in gdf["area_sqm"]],
        "total_area_sqm": float(gdf["area_sqm"].sum()),
        "bounds": [float(value) for value in gdf.total_bounds],
        "crs": crs.to_string(),
        "geojson": output_path.name,
        "tile": Path(image_path).name,
        "masks": masks,
    }


if __name__ == "__main__":
    run_sam_geo_segmentation()
