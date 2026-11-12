import numpy as np
import rasterio
import scipy.ndimage as ndimage
from pathlib import Path
from rasterio.merge import merge
from rasterio.transform import Affine

# --- Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
TILE_DIR = OUTPUT_DIR / "tiles"
MASK_DIR = OUTPUT_DIR / "processed_masks"
MOSAIC_PATH = OUTPUT_DIR / "mosaic.tif"

TILE = 100
CELL = 1.0
CRS = "EPSG:32618"                 # UTM zone 18N: 1 m pixels, so the mosaic is in metres
THRESHOLD = 0.6

# Three tiles on a clean 100 m grid, so the mosaic has no half-pixel seam. The fourth
# entry in BATCH_TILES below is a path that does not exist: the error branch.
TILE_SPECS = [
    {"name": "tile_01.tif", "origin": (300000.0, 4500200.0),
     "building": (20, 50, 20, 60), "prompt": [10, 10, 70, 60]},
    {"name": "tile_02.tif", "origin": (300100.0, 4500200.0),
     "building": (40, 80, 10, 40), "prompt": [5, 30, 50, 90]},
    {"name": "tile_03.tif", "origin": (300000.0, 4500100.0),
     "building": (30, 60, 50, 90), "prompt": [40, 20, 95, 70]},
]

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
    """Stand-in for a SAM predictor on one tile: the bright region inside the box."""

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
        masks = region[None, :, :]
        scores = np.array([0.93 if region.any() else 0.3], dtype=np.float32)
        return masks, scores, np.zeros((1, 64, 64), dtype=np.float32)


def load_predictor():
    if HAVE_SAM and CHECKPOINT_PATH.exists():
        sam = sam_model_registry["vit_b"](checkpoint=str(CHECKPOINT_PATH))
        sam.eval()
        return SamPredictor(sam), "segment_anything (vit_b)"
    reason = ("segment_anything is not installed" if not HAVE_SAM
              else f"{CHECKPOINT_PATH.name} is not present")
    print(f"[SAM] {reason}; using the box-prompt stand-in.")
    return BoxPromptStandIn(), "stand-in"


# --- 2. Batch Setup: Three Real Tiles and One That Is Not There ----------------
def build_tiles():
    """Write the three tiles and return the batch description."""
    TILE_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(31)
    tiles = []
    for spec in TILE_SPECS:
        image = rng.integers(60, 110, size=(TILE, TILE, 3), dtype=np.uint8)
        row_start, row_stop, col_start, col_stop = spec["building"]
        image[row_start:row_stop, col_start:col_stop, :] = np.array([225, 195, 180],
                                                                   dtype=np.uint8)
        path = TILE_DIR / spec["name"]
        transform = Affine(CELL, 0.0, spec["origin"][0], 0.0, -CELL, spec["origin"][1])
        with rasterio.open(path, "w", driver="GTiff", height=TILE, width=TILE,
                           count=3, dtype="uint8", crs=CRS, transform=transform,
                           compress="deflate") as dst:
            for band in range(3):
                dst.write(image[:, :, band], band + 1)
        tiles.append({"path": path, "prompt": spec["prompt"]})

    tiles.append({"path": TILE_DIR / "tile_404.tif", "prompt": [10, 10, 90, 90]})
    return tiles


# --- 3. Metadata Preservation ---------------------------------------------------
def create_georeferenced_mask(mask_array, affine_transform, crs, output_path):
    """Write the raw NumPy mask with the tile's own transform and CRS."""
    profile = {
        "driver": "GTiff",
        "height": mask_array.shape[0],
        "width": mask_array.shape[1],
        "count": 1,
        "dtype": "uint8",
        "crs": crs,
        "transform": affine_transform,
        "compress": "deflate",
        "nodata": 0,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(mask_array.astype(np.uint8), 1)
    return output_path


def _pixels(path):
    with rasterio.open(path) as src:
        return int(src.read(1).sum())


# --- 4. The Batch Loop ----------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    for stale in MASK_DIR.glob("mask_*.tif"):
        stale.unlink()

    batch = build_tiles()
    predictor, mode = load_predictor()
    print(f"Starting batch processing of {len(batch)} tiles ({mode})...")

    processed, skipped = [], []
    for index, tile_info in enumerate(batch):
        tile_path = tile_info["path"]
        print(f"\nProcessing tile {index + 1}: {tile_path.name}")
        try:
            # 1. The tile's own metadata, read from the tile.
            with rasterio.open(tile_path) as src:
                image = src.read([1, 2, 3]).transpose(1, 2, 0)
                tile_transform = src.transform
                tile_crs = src.crs
            print(f"  Metadata: CRS={tile_crs}, origin=({tile_transform.c:.0f}, "
                  f"{tile_transform.f:.0f})")

            # 2. Segment this tile.
            predictor.set_image(image)
            masks, scores, _ = predictor.predict(
                box=np.array(tile_info["prompt"], dtype=np.float64),
                multimask_output=False)
            raw_mask = masks[0].astype(np.uint8)
            print(f"  Predicted {int(raw_mask.sum())} pixels at "
                  f"score {float(np.max(scores)):.2f}")

            # 3. Write the mask back to disk, georeferenced with this tile's metadata.
            output_path = MASK_DIR / f"mask_{tile_path.name}"
            create_georeferenced_mask(raw_mask, tile_transform, tile_crs, output_path)
            print(f"  Wrote {output_path.name}")
            processed.append(output_path)

        except rasterio.RasterioIOError as error:
            # The file name and the exception class, not rasterio's message: that one
            # repeats the absolute path, and a book's output carries no home directory.
            print(f"  FATAL ERROR: cannot read {tile_path.name}; skipping "
                  f"({type(error).__name__}).")
            skipped.append(tile_path.name)
        except Exception as error:      # noqa: BLE001 - a batch must finish
            print(f"  Unexpected error on {tile_path.name}: {error}")
            skipped.append(tile_path.name)

    # --- Stitching ---
    print("\n" + "=" * 50)
    print(f"Batch complete: {len(processed)} masks, {len(skipped)} tile(s) skipped")
    if not processed:
        print("Nothing to merge.")
        return {"mode": mode, "processed": [], "skipped": skipped}

    mosaic, mosaic_transform = merge([str(path) for path in processed])
    profile = {
        "driver": "GTiff", "height": mosaic.shape[1], "width": mosaic.shape[2],
        "count": 1, "dtype": "uint8", "crs": CRS, "transform": mosaic_transform,
        "compress": "deflate", "nodata": 0,
    }
    with rasterio.open(MOSAIC_PATH, "w", **profile) as dst:
        dst.write(mosaic[0].astype(np.uint8), 1)

    print(f"Merged {len(processed)} masks into {MOSAIC_PATH.name}: "
          f"{mosaic.shape[1]} x {mosaic.shape[2]}, "
          f"{int(mosaic.sum())} building pixels")
    print(f"Mosaic origin: ({mosaic_transform.c:.0f}, {mosaic_transform.f:.0f}), "
          f"pixel {mosaic_transform.a:.0f} m")

    return {
        "mode": mode,
        "processed": [path.name for path in processed],
        "skipped": skipped,
        "mosaic_shape": tuple(int(v) for v in mosaic.shape),
        "mosaic_pixels": int(mosaic.sum()),
        "mosaic_origin": (float(mosaic_transform.c), float(mosaic_transform.f)),
        "mosaic_pixel_size": float(mosaic_transform.a),
        "masks": {path.name: _pixels(path) for path in processed},
        "mosaic": MOSAIC_PATH.name,
    }


if __name__ == "__main__":
    main()
