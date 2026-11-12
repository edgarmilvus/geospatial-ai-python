import json
from pathlib import Path

import numpy as np
import rasterio
import torch
import torch.nn as nn
from rasterio.features import shapes

# --- 1. Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
TILE = 512                       # a 512 x 512 chip, the unit a tiled inference job uses
CELL = 10.0                      # 10 m pixels, so a polygon's area is in m²
CRS = "EPSG:32617"               # UTM zone 17N
ORIGIN = (600000.0, 4200000.0)   # north-west corner of the chip, in projected metres
SEED = 42

# Five roofs, in (row_start, col_start, row_stop, col_stop) order. Together they cover
# 2400 + 1500 + 1600 + 4800 + 1600 = 11 900 pixels.
BUILDINGS = [
    (20, 20, 60, 80),
    (20, 100, 50, 150),
    (120, 30, 160, 70),
    (200, 200, 260, 280),
    (300, 320, 340, 360),
]


# --- 2. The Model: A Placeholder for the Trained U-Net ---
class SimpleBuildingDetector(nn.Module):
    """Three channels in, one logit per pixel out.

    In the trained pipeline this is the U-Net of the previous section. Here it is the
    same interface — convolution, ReLU, 1 x 1 classifier — with weights that stand in
    for the trained ones, so the raster-to-vector half can be read on its own.
    """

    def __init__(self, in_channels=3, out_channels=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.final_conv = nn.Conv2d(64, out_channels, kernel_size=1)

    def forward(self, x):
        # Logits, not probabilities: the sigmoid belongs to post-processing.
        return self.final_conv(self.relu(self.conv1(x)))


def load_mock_weights(model):
    """Stand-in for `model.load_state_dict(torch.load(...))`.

    The stand-in is the trained network, not the pipeline. Channel 0 of the first
    convolution becomes the mean of the three bands, and the 1 x 1 classifier maps
    that mean m to the logit 12m - 9: a roof above DN 191 crosses p = 0.5, the
    background around DN 120 sits at p = 0.05. That is the response a model trained
    on this kind of chip converges to, and it keeps every downstream number fixed.
    """
    with torch.no_grad():
        model.conv1.weight.zero_()
        model.conv1.bias.zero_()
        for band in range(3):
            model.conv1.weight[0, band, 1, 1] = 1.0 / 3.0

        model.final_conv.weight.zero_()
        model.final_conv.bias.zero_()
        model.final_conv.weight[0, 0, 0, 0] = 12.0
        model.final_conv.bias[0] = -9.0
    print("[SimpleBuildingDetector] Stand-in weights loaded (threshold at DN 191).")
    return model


# --- 3. Georeferenced Input ---
def build_tile(path):
    """Write, and return, a deterministic 512 x 512 RGB chip with its transform."""
    rng = np.random.default_rng(SEED)

    # Bare ground: textured but dark, so brightness alone is not the label.
    tile = rng.integers(90, 145, size=(TILE, TILE, 3), dtype=np.uint8)

    # Roofs: light grey, each with its own per-pixel texture.
    for row_start, col_start, row_stop, col_stop in BUILDINGS:
        shape_h = row_stop - row_start
        shape_w = col_stop - col_start
        roof = rng.integers(-10, 11, size=(shape_h, shape_w, 3))
        tile[row_start:row_stop, col_start:col_stop, :] = np.clip(
            228 + roof, 0, 255).astype(np.uint8)

    transform = rasterio.transform.from_origin(ORIGIN[0], ORIGIN[1], CELL, CELL)
    profile = {
        "driver": "GTiff", "height": TILE, "width": TILE, "count": 3,
        "dtype": "uint8", "crs": CRS, "transform": transform, "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        for band in range(3):
            dst.write(tile[:, :, band], band + 1)   # rasterio wants (band, row, col)
    return tile, transform


def read_tile(path):
    """Read the chip back as HWC plus the metadata the vector step needs."""
    with rasterio.open(path) as src:
        # Rasterio returns (band, row, col); SAM, Matplotlib and this listing want
        # (row, col, band), so the axes move once, here.
        image = src.read([1, 2, 3]).transpose(1, 2, 0)
        return image, src.transform, src.crs


# --- 4. Inference ---
def run_inference(model, image, device="cpu"):
    """HWC uint8 -> probability map, through the same three steps as the book."""
    model.eval()
    # (H, W, C) -> (1, C, H, W): the batch axis a trained model expects.
    image_tensor = torch.from_numpy(image).float().permute(2, 0, 1).unsqueeze(0) / 255.0
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        logits = model(image_tensor)                    # (1, 1, H, W)

    probability = torch.sigmoid(logits).squeeze().cpu().numpy()
    # One threshold, applied once, to the probability map — never to the logits.
    binary_mask = (probability > 0.5).astype(np.uint8)
    return logits.squeeze().cpu().numpy(), binary_mask


# --- 5. Raster to Vector ---
def vectorize(binary_mask, transform, crs):
    """Turn the mask into GeoJSON features whose coordinates are in metres."""
    features = []
    for index, (geometry, value) in enumerate(
            shapes(binary_mask, transform=transform, mask=binary_mask, connectivity=8)):
        if value != 1:          # `mask=` already excludes 0, and the check documents it
            continue
        area_m2 = _ring_area(geometry)
        features.append({
            "type": "Feature",
            "properties": {
                "building_id": len(features),
                "class": int(value),
                "area_m2": round(area_m2, 1),
            },
            "geometry": geometry,
        })
    print(f"[Vectorization] Detected {len(features)} building polygons, "
          f"{sum(f['properties']['area_m2'] for f in features):,.0f} m² in total.")
    return {
        "type": "FeatureCollection",
        # GeoJSON's crs member is deprecated by RFC 7946, and a GIS reader that honours
        # it still gets UTM metres instead of assuming degrees.
        "crs": {"type": "name", "properties": {"name": crs.to_string()}},
        "features": features,
    }


def _ring_area(geometry):
    """Shoelace area of the outer ring.

    `shapes` has already written the ring in map coordinates — metres here — so this
    is an area in m². Multiplying it by the pixel area as well is the classic
    double-count, and it inflates a 1.19 km² tile to 119 km².
    """
    ring = geometry["coordinates"][0]
    total = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


# --- 6. Execution ---
def run_geo_inference(tile_path, output_path):
    """Load, infer, threshold, vectorize, save."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not tile_path.exists():
        build_tile(tile_path)
    image, transform, crs = read_tile(tile_path)
    print(f"[Data Load] Image shape: {image.shape}. CRS: {crs}")
    print(f"[Data Load] Pixel size: {transform.a:.1f} m, origin "
          f"({transform.c:.0f}, {transform.f:.0f})")

    model = SimpleBuildingDetector().to("cpu")
    model = load_mock_weights(model)

    logits, binary_mask = run_inference(model, image)
    print(f"[Inference] Logit range [{logits.min():.2f}, {logits.max():.2f}], "
          f"{int(binary_mask.sum())} pixels above p = 0.5")

    collection = vectorize(binary_mask, transform, crs)
    output_path.write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    print(f"[Success] GeoJSON written to {output_path.name}")
    if collection["features"]:
        first = collection["features"][0]
        print("--- First feature ---")
        print(json.dumps({"properties": first["properties"],
                          "geometry_type": first["geometry"]["type"]}, indent=2))

    return {
        "image_shape": tuple(int(v) for v in image.shape),
        "mask_pixels": int(binary_mask.sum()),
        "logit_min": float(logits.min()),
        "logit_max": float(logits.max()),
        "feature_count": len(collection["features"]),
        "total_area_m2": float(sum(f["properties"]["area_m2"]
                                   for f in collection["features"])),
        "geojson": output_path.name,
        "crs": crs.to_string(),
        "transform": [transform.a, transform.c, transform.f],
    }


if __name__ == "__main__":
    run_geo_inference(OUTPUT_DIR / "industrial_tile.tif",
                      OUTPUT_DIR / "detected_buildings.geojson")
