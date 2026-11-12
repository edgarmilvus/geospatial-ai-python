import numpy as np
import rasterio
import scipy.ndimage as ndimage
import geopandas as gpd
from pathlib import Path
from shapely.geometry import shape
from rasterio.features import shapes
from rasterio.transform import Affine

# --- Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
INPUT_IMAGE_PATH = OUTPUT_DIR / "mock_satellite_image.tif"
OUTPUT_VECTOR_PATH = OUTPUT_DIR / "building_footprints.gpkg"

ROWS, COLS, CELL = 100, 100, 1.0
TRANSFORM = Affine(CELL, 0.0, 300000.0, 0.0, -CELL, 4500000.0)
CRS = "EPSG:32618"                    # UTM zone 18N: metres, so area is m²
BUILDING = (45, 55, 45, 55)           # rows 45-55, columns 45-55: 10 x 10 pixels
THRESHOLD = 0.6

try:
    from segment_anything import sam_model_registry, SamPredictor
    HAVE_SAM = True
except ImportError:
    sam_model_registry = None
    SamPredictor = None
    HAVE_SAM = False

CHECKPOINT_PATH = OUTPUT_DIR / "sam_vit_b.pth"


# --- The Segmenter: Real If Present, a Stand-in Otherwise ----------------------
class ThresholdSamPredictor:
    """Stand-in for `SamPredictor`: the bright blob under the prompt point.

    Same interface, no weights: `set_image` then `predict(point_coords=...)`. What it
    stands in for is the network; the prompt handling and the georeferencing below are
    the exercise.
    """

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
        scores = np.array([0.94 if region.any() else 0.3], dtype=np.float32)
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


# --- The Scene the Prompt Points At --------------------------------------------
def build_scene(path=INPUT_IMAGE_PATH):
    """A georeferenced 100 x 100 patch with one bright building."""
    rng = np.random.default_rng(5)
    image = rng.integers(60, 110, size=(ROWS, COLS, 3), dtype=np.uint8)
    row_start, row_stop, col_start, col_stop = BUILDING
    image[row_start:row_stop, col_start:col_stop, :] = np.array([225, 190, 175],
                                                               dtype=np.uint8)

    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=ROWS, width=COLS, count=3,
                       dtype="uint8", crs=CRS, transform=TRANSFORM,
                       compress="deflate") as dst:
        for band in range(3):
            dst.write(image[:, :, band], band + 1)
    print(f"Wrote {path.name}: {COLS} x {ROWS} at {CELL:.0f} m, {CRS}")
    return path


# --- The Conversion, With the Metadata Read From the Source --------------------
def export_to_geopackage(mask_array, source_image_path, output_path):
    """Binary mask -> georeferenced polygons, using the source image's transform.

    The transform and the CRS come from the file the mask was predicted on. Passing
    them in from the caller is how a pipeline ends up with polygons 40 km from the
    image they describe.
    """
    with rasterio.open(source_image_path) as src:
        source_transform = src.transform
        source_crs = src.crs
        print(f"Input image CRS: {source_crs.to_string()}")

    if mask_array.shape != (ROWS, COLS):
        raise ValueError(f"mask {mask_array.shape} does not match the image "
                         f"{(ROWS, COLS)}")

    geometries = []
    for geometry, value in shapes(mask_array.astype(np.uint8),
                                  mask=mask_array.astype(np.uint8),
                                  transform=source_transform, connectivity=8):
        if value == 1:
            geometries.append(shape(geometry))

    if not geometries:
        print("No features found to export.")
        return None

    gdf = gpd.GeoDataFrame({"class": ["building"] * len(geometries),
                            "area_sqm": [round(polygon.area, 2)
                                         for polygon in geometries]},
                           geometry=geometries, crs=source_crs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GPKG")

    print(f"\n[SUCCESS] Exported {len(gdf)} features to {output_path.name}")
    print(f"[VALIDATION] Output vector CRS: {gdf.crs.to_string()}")
    return gdf.crs


# --- Execution ------------------------------------------------------------------
def main():
    build_scene()
    with rasterio.open(INPUT_IMAGE_PATH) as src:
        # (band, row, col) -> (row, col, band): what the segmenter reads.
        image = src.read([1, 2, 3]).transpose(1, 2, 0)
        input_crs = src.crs

    predictor, mode = load_predictor(image)
    print(f"Segmenter: {mode}")

    # 1. The prompt: (x, y) in pixels, at the centre of the building.
    prompt_point = (50, 50)
    print(f"Prompting at pixel (x={prompt_point[0]}, y={prompt_point[1]})")

    # 2. The mask.
    masks, scores, _ = predictor.predict(point_coords=np.array([list(prompt_point)]),
                                         point_labels=np.array([1]),
                                         multimask_output=True)
    segmentation_mask = masks[int(np.argmax(scores))]
    print(f"Mask: {segmentation_mask.shape}, {int(segmentation_mask.sum())} pixels, "
          f"score {float(np.max(scores)):.2f}")

    # 3. The vectors, on the source image's grid.
    result_crs = export_to_geopackage(segmentation_mask, INPUT_IMAGE_PATH,
                                      OUTPUT_VECTOR_PATH)

    # 4. The check the exercise asks for.
    if result_crs is not None and result_crs.to_epsg() == input_crs.to_epsg():
        print("\n[VERIFICATION] Georeferencing Integrity Check PASSED: "
              "input CRS matches output CRS.")
    else:
        print("\n[VERIFICATION] Georeferencing Integrity Check FAILED.")

    reread = gpd.read_file(OUTPUT_VECTOR_PATH)
    print(f"Re-read {OUTPUT_VECTOR_PATH.name}: {len(reread)} feature(s), "
          f"CRS {reread.crs.to_string()}, area {reread.area.sum():.0f} m²")
    print(f"Bounds: {tuple(round(float(v), 1) for v in reread.total_bounds)}")

    return {
        "mode": mode,
        "input_crs": input_crs.to_string(),
        "output_crs": result_crs.to_string() if result_crs is not None else None,
        "mask_pixels": int(segmentation_mask.sum()),
        "mask_shape": tuple(int(v) for v in segmentation_mask.shape),
        "feature_count": len(reread),
        "area_sqm": float(reread.area.sum()),
        "bounds": tuple(float(v) for v in reread.total_bounds),
        "gpkg": OUTPUT_VECTOR_PATH.name,
    }


if __name__ == "__main__":
    main()
