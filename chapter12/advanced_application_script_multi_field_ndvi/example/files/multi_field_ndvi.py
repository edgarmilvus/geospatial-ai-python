import numpy as np
import rasterio
from pathlib import Path
from typing import Dict

# --- Configuration and Constants ---
# Standard thresholds for vegetation health classification (NDVI range -1.0 to 1.0).
# The top band is closed at 1.0: an index that lands exactly on 1.0 (a pixel whose
# Red band clipped to zero) is dense vegetation, not "unclassified".
NDVI_THRESHOLDS = {
    "Water/Shadow": (-1.0, 0.0),  # NDVI < 0: more Red than NIR
    "Poor": (0.0, 0.2),           # Stress or bare soil
    "Moderate": (0.2, 0.5),       # Early growth or moderate stress
    "Healthy": (0.5, 1.0)         # Active, dense vegetation (upper bound included)
}

# A real tile is 512x512 or larger. The example uses a 96x96 window so that two
# fields, their two GeoTIFFs and their two index rasters finish in about a second.
TILE_SIZE = (96, 96)

# Spatial context for the simulated scenes: 10 m pixels in UTM zone 10N.
CELL_SIZE = 10.0
CRS = "EPSG:32610"
SCENE_NODATA = 0          # a DN of 0 in both bands means "no signal", not "no vegetation"
NDVI_NODATA = -9999.0     # the out-of-range marker written into the index raster
SEED = 20240617           # one seed: the same two fields on every machine

# The two scenes are written to disk and read back, exactly as a real workflow
# would read two satellite tiles.
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


# --- 1. Data Simulation Utility (Mimicking Geospatial Read Operations) ---
def simulate_band_data(mean_reflectance: float, rng) -> np.ndarray:
    """
    Simulates reading a single band (NIR or Red) array from a file source.
    Satellite data is often stored as scaled integers (e.g., 0-10000).
    """
    # Generate a randomized array centered around the specified mean reflectance (scaled by 10000)
    base = rng.normal(loc=mean_reflectance * 10000, scale=400, size=TILE_SIZE)

    # Clip and convert to unsigned 16-bit integer (standard satellite data format)
    data = np.clip(base, 0, 10000).astype(np.uint16)
    return data


def write_field_scene(path, red_band, nir_band):
    """Write the Red band as band 1 and the NIR band as band 2 of one GeoTIFF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = {
        'driver': 'GTiff',
        'dtype': 'uint16',
        'nodata': SCENE_NODATA,
        'width': TILE_SIZE[1],
        'height': TILE_SIZE[0],
        'count': 2,
        'crs': CRS,
        'transform': rasterio.transform.from_origin(500000.0, 4500000.0,
                                                    CELL_SIZE, CELL_SIZE)
    }
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(red_band, 1)   # band 1 is Red, the convention every vendor follows
        dst.write(nir_band, 2)   # band 2 is NIR
    return path


def read_bands(path):
    """Read bands 1 (Red) and 2 (NIR) as float32, with the scene profile."""
    with rasterio.open(path) as src:
        red = src.read(1).astype(np.float32)
        nir = src.read(2).astype(np.float32)
        profile = src.profile.copy()
    return red, nir, profile


# --- 2. Core Band Math Function: Robust NDVI Calculation ---
def calculate_ndvi(nir_band: np.ndarray, red_band: np.ndarray):
    """
    Calculates the Normalized Difference Vegetation Index: NDVI = (NIR - Red) / (NIR + Red).
    Returns the index and the boolean mask of pixels where the denominator was usable.
    """
    # Convert input bands from integer types (uint16) to float32 for accurate division
    nir_float = nir_band.astype(np.float32)
    red_float = red_band.astype(np.float32)

    # Calculate the denominator (NIR + Red)
    denominator = nir_float + red_float

    # Initialize the output NDVI array with zeros. This handles areas where the denominator is zero.
    ndvi = np.zeros_like(nir_float)

    # Create a boolean mask identifying pixels where the denominator is valid (i.e., > 0)
    # This is the standard NumPy practice for avoiding ZeroDivisionError in vectorized math.
    valid_pixels = denominator > 0

    # Perform the calculation only on the valid pixels using the mask
    numerator = nir_float[valid_pixels] - red_float[valid_pixels]

    # Assign the calculated value back into the corresponding locations in the NDVI map
    ndvi[valid_pixels] = numerator / denominator[valid_pixels]

    # Clip the final results to the standard NDVI range [-1.0, 1.0]
    return np.clip(ndvi, -1.0, 1.0), valid_pixels


def write_ndvi(ndvi_map, valid_pixels, scene_profile, path):
    """Write the index as one float32 band, marking unusable pixels as nodata."""
    profile = scene_profile.copy()
    profile.update({
        'count': 1,
        'dtype': 'float32',
        'nodata': NDVI_NODATA,
    })
    band = np.where(valid_pixels, ndvi_map, NDVI_NODATA).astype(np.float32)
    with rasterio.open(path, 'w', **profile) as dst:
        dst.write(band, 1)
    return path


# --- 3. Analysis and Reporting Function ---
def analyze_ndvi(ndvi_map: np.ndarray, valid_pixels: np.ndarray, field_name: str) -> Dict:
    """Analyzes the NDVI map, classifies pixels, and generates descriptive statistics."""
    # Pixels without signal are not "bare soil": they are excluded from the total.
    total_pixels = int(valid_pixels.sum())
    valid_values = ndvi_map[valid_pixels]
    analysis = {"Field": field_name, "Mean_NDVI": float(np.mean(valid_values)),
                "Valid_Pixels": total_pixels}

    print(f"\n--- Analysis for {field_name} ---")
    print(f"Mean NDVI: {analysis['Mean_NDVI']:.4f}")
    print(f"Valid pixels: {total_pixels} of {ndvi_map.size} "
          f"({ndvi_map.size - total_pixels} nodata)")

    # Iterate through defined health thresholds to classify the map
    for index, (health_status, (low, high)) in enumerate(NDVI_THRESHOLDS.items()):
        # Create a boolean mask for the current classification range. Every band but
        # the last is half-open; the last is closed at 1.0, so the four bands tile
        # [-1.0, 1.0] and the percentages add up to 100.
        mask = valid_pixels & (ndvi_map >= low)
        if index < len(NDVI_THRESHOLDS) - 1:
            mask &= ndvi_map < high

        # Use np.sum(mask) to count True values (pixels in this category)
        pixel_count = int(np.sum(mask))

        # Calculate percentage coverage
        percentage = (pixel_count / total_pixels) * 100

        analysis[f"Pixels_{health_status}"] = pixel_count
        analysis[f"Percent_{health_status}"] = percentage

        print(f"  {health_status}: {pixel_count} pixels ({percentage:.2f}%)")

    return analysis


# --- 4. Main Execution Flow ---
def main_ndvi_workflow():
    """Manages the end-to-end process of data simulation, calculation, and reporting."""

    # Define two distinct field scenarios: one healthy, one stressed
    field_data_configs = {
        "Field_A_Healthy_Corn": {"NIR_Mean": 0.55, "Red_Mean": 0.08},
        "Field_B_Stressed_Wheat": {"NIR_Mean": 0.25, "Red_Mean": 0.15}
    }

    rng = np.random.default_rng(SEED)
    results = []
    rasters = {}

    for field_name, config in field_data_configs.items():
        print(f"\n[START PROCESSING] {field_name}")

        # A. Data Acquisition: two bands out of a simulated GeoTIFF on disk
        red_data = simulate_band_data(config["Red_Mean"], rng)
        nir_data = simulate_band_data(config["NIR_Mean"], rng)

        # A patch of deep shadow: no signal in either band, so NIR + Red is zero.
        # This is the case the masked division has to survive.
        red_data[0:6, 0:6] = SCENE_NODATA
        nir_data[0:6, 0:6] = SCENE_NODATA

        scene_file = OUTPUT_DIR / f"{field_name}_scene.tif"
        write_field_scene(scene_file, red_data, nir_data)
        print(f"-> Simulated 2-band scene: {scene_file.name}")
        red_data, nir_data, scene_profile = read_bands(scene_file)

        # B. Validation Check (Essential for any Band Math operation)
        if nir_data.shape != red_data.shape:
            raise ValueError("Band Math requires input arrays to have identical dimensions.")

        # C. Core Band Math Operation: NDVI Calculation
        ndvi_output_map, valid_pixels = calculate_ndvi(nir_data, red_data)

        # D. The index as a product: one band, float32, with its nodata value
        ndvi_file = OUTPUT_DIR / f"{field_name}_ndvi.tif"
        write_ndvi(ndvi_output_map, valid_pixels, scene_profile, ndvi_file)
        rasters[field_name] = ndvi_file.name

        # E. Analysis and Reporting
        field_analysis = analyze_ndvi(ndvi_output_map, valid_pixels, field_name)
        results.append(field_analysis)

    # Final Summary Report Generation
    print("\n=============================================")
    print("SERIES SUMMARY REPORT: VEGETATION HEALTH INDEX")
    print("=============================================")
    for res in results:
        print(f"\nField: {res['Field']}")
        print(f"  Overall Mean NDVI: {res['Mean_NDVI']:.4f}")
        print(f"  Healthy Area Coverage: {res['Percent_Healthy']:.2f}%")
        print(f"  Index raster: {rasters[res['Field']]}")

    return results


OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    main_ndvi_workflow()
