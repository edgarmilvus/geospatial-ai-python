"""Chapter 20, exercise 3 — damage from two dates, not one.

The classifier in the exercise's starting point had a single heuristic: how much of
the structure is gone. This version adds the second signal a damage analyst actually
uses — the material change inside the same footprint — by reading the same window of
two rasters and comparing its NDVI. A building that lost a fifth of its roof and
turned from vegetation-dark to rubble-bright is a different case from one that lost
the same fifth to a tidier repair.

Both rasters are written by the listing, so the exercise runs without a download and
the numbers below are checkable by hand.
"""

import pathlib
from typing import Dict

import numpy as np
import rasterio
from rasterio.mask import mask as raster_mask
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
PRE_RASTER = OUTPUT_DIR / "pre_disaster_scene.tif"
POST_RASTER = OUTPUT_DIR / "post_disaster_scene.tif"

CRS = "EPSG:32611"
PIXEL = 10.0
SIZE = 32
ORIGIN = (640_000.0, 3_760_000.0)  # a UTM 11N corner near the AOI


def write_scenes():
    """Two four-band scenes: the left half lost its roof, the right half did not.

    Band order is the one the exercise assumes: 1 blue, 2 green, 3 red, 4 near
    infrared. Only bands 3 and 4 are read by the NDVI proxy.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    transform = from_origin(ORIGIN[0], ORIGIN[1], PIXEL, PIXEL)

    pre = np.zeros((4, SIZE, SIZE), dtype="float32")
    pre[0], pre[1] = 60.0, 70.0
    pre[2] = 50.0    # red
    pre[3] = 200.0   # near infrared: NDVI = (200 - 50) / 250 = 0.6

    post = np.zeros((4, SIZE, SIZE), dtype="float32")
    post[0], post[1] = 90.0, 95.0
    post[2, :, :SIZE // 2] = 150.0     # left: rubble, red rises
    post[3, :, :SIZE // 2] = 80.0      # left: near infrared collapses
    post[2, :, SIZE // 2:] = 60.0      # right: intact
    post[3, :, SIZE // 2:] = 180.0

    for path, array in ((PRE_RASTER, pre), (POST_RASTER, post)):
        with rasterio.open(path, "w", driver="GTiff", height=SIZE, width=SIZE,
                           count=4, dtype="float32", crs=CRS,
                           transform=transform) as destination:
            destination.write(array)


def building_footprint(column: int, row: int, side_m: float = 40.0) -> Dict:
    """A square footprint in the raster's CRS, as a GeoJSON-style geometry."""
    x = ORIGIN[0] + column * PIXEL
    y = ORIGIN[1] - row * PIXEL
    return mapping(box(x, y - side_m, x + side_m, y))


class DamageClassificationAgent:
    """Structural loss plus a spectral term, both measured inside the footprint."""

    def __init__(self, structural_loss_threshold: float = 0.20):
        self.structural_loss_threshold = structural_loss_threshold
        self.ndvi_change_threshold = 0.4

    def calculate_ndvi_proxy(self, raster_path: str, geometry: dict,
                             nir_band_idx: int = 4, red_band_idx: int = 3) -> float:
        """Mean (NIR - Red) / (NIR + Red) over the pixels inside `geometry`.

        `rasterio.open` is a context manager: the file is closed when the block
        ends, whether or not the arithmetic inside it raised.
        """
        try:
            with rasterio.open(raster_path) as source:
                clipped, _ = raster_mask(source, [geometry], crop=True, filled=False)
                near_infrared = clipped[nir_band_idx - 1].astype(float)
                red = clipped[red_band_idx - 1].astype(float)
                denominator = near_infrared + red
                denominator[denominator == 0] = 1e-6
                return float(np.mean((near_infrared - red) / denominator))
        except Exception as exc:  # noqa: BLE001 - a bad window is data, not a crash
            print(f"Error reading {pathlib.Path(raster_path).name}: {exc}")
            return 0.0

    def calculate_structural_loss(self, pre_area: float, post_area: float) -> float:
        """Fraction of the pre-disaster footprint that is no longer covered."""
        return (pre_area - post_area) / pre_area if pre_area > 0 else 0.0

    def classify_damage(self, pre_raster_path: str, post_raster_path: str,
                        building_footprint: Dict, pre_area: float,
                        post_area: float) -> Dict:
        """Both signals, then the rule the exercise asks for."""
        structural_loss = self.calculate_structural_loss(pre_area, post_area)

        pre_ndvi = self.calculate_ndvi_proxy(pre_raster_path, building_footprint)
        post_ndvi = self.calculate_ndvi_proxy(post_raster_path, building_footprint)
        ndvi_change = abs(pre_ndvi - post_ndvi)

        if structural_loss >= 0.80:
            damage_class = "Destroyed"
        elif structural_loss >= self.structural_loss_threshold:
            damage_class = "Moderate Damage"
        else:
            damage_class = "Minor/No Damage"

        # The new heuristic: a moderate loss plus a large material change is worse
        # than the same loss with the roof still where it was.
        if (structural_loss > 0.20 and ndvi_change > self.ndvi_change_threshold
                and damage_class != "Destroyed"):
            damage_class = "Major Damage"

        updated = dict(building_footprint)
        updated["properties"] = dict(building_footprint.get("properties", {}))
        updated["properties"]["structural_loss_pct"] = round(structural_loss, 4)
        updated["properties"]["ndvi_change_magnitude"] = round(ndvi_change, 4)
        updated["properties"]["damage_class"] = damage_class
        return updated


SCENARIOS = [
    # (label, column, row, pre_area, post_area, expected reason)
    ("A: roof gone on the rubble side", 4, 6, 100.0, 60.0),
    ("B: same loss, roof still standing", 22, 6, 100.0, 60.0),
    ("C: collapsed", 4, 12, 100.0, 15.0),
]


def main():
    write_scenes()
    agent = DamageClassificationAgent()
    results = []

    print("--- Multi-temporal damage classification ---")
    for label, column, row, pre_area, post_area in SCENARIOS:
        footprint = building_footprint(column, row)
        footprint["properties"] = {"id": label[0]}
        result = agent.classify_damage(str(PRE_RASTER), str(POST_RASTER), footprint,
                                        pre_area, post_area)
        properties = result["properties"]
        print(f"\n[{label}]")
        print(f"  Structural loss:     {properties['structural_loss_pct'] * 100:.2f}%")
        print(f"  NDVI change:         {properties['ndvi_change_magnitude']:.3f}")
        print(f"  Final classification: {properties['damage_class']}")
        results.append(properties)

    writeback = OUTPUT_DIR / "multitemporal_results.txt"
    writeback.write_text(
        "\n".join(f"{row['id']}: {row['damage_class']} "
                  f"(loss {row['structural_loss_pct']:.2f}, ndvi {row['ndvi_change_magnitude']:.3f})"
                  for row in results) + "\n", encoding="utf-8")
    print(f"\nWrote output/{writeback.name}")


if __name__ == "__main__":
    main()
