import rasterio
from rasterio.mask import mask
import geopandas as gpd
from shapely.geometry import box, Polygon
import numpy as np
import pathlib
import json
import warnings

# Suppress minor GeoPandas warnings during dummy data creation
warnings.filterwarnings('ignore', 'The CRS is not defined')

# --- Configuration and Setup ---
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# A fixed seed keeps the simulated satellite tile identical on every run.
RNG = np.random.default_rng(14)

# --- 1. Utility Functions for Data Simulation (Mandatory for executable examples) ---

def create_dummy_raster(path):
    """Creates a simple 3-band, 1000x1000 dummy GeoTIFF simulating large satellite data."""
    width, height = 1000, 1000
    # Define a simple affine transform (0-10 units in both axes)
    transform = rasterio.transform.from_bounds(
        west=0, south=0, east=10, north=10, width=width, height=height
    )
    
    # Create random 8-bit integer data for 3 bands (RGB simulation)
    data = RNG.integers(0, 255, (3, height, width), dtype=np.uint8)

    # Write the dummy raster file
    with rasterio.open(
        path, 'w', driver='GTiff',
        height=height, width=width,
        count=3, dtype=rasterio.uint8,
        crs='EPSG:4326', # Standard WGS 84
        transform=transform
    ) as new_dataset:
        new_dataset.write(data)
        
    print(f"Created dummy raster: {path.name} ({width} x {height} px, {3} bands)")
    return transform

def create_dummy_vector_data(infra_path):
    """Creates dummy vector data (infrastructure) and the ROI boundary GeoDataFrame."""
    
    # Infrastructure (scattered features across the larger 10x10 area)
    infra_geom = [
        # Feature 1: Fully outside the ROI (ROI is 3-7)
        Polygon([(1, 1), (1.5, 1), (1.5, 1.5), (1, 1.5)]),
        # Feature 2: Fully inside the ROI
        box(4, 4, 4.5, 4.5), 
        # Feature 3: Partially crossing the ROI boundary
        box(6.5, 6.5, 7.5, 7.5) 
    ]
    
    infra_data = gpd.GeoDataFrame({
        'id': [1, 2, 3], 
        'type': ['road', 'pipeline', 'building'], 
        'geometry': infra_geom
    }, crs="EPSG:4326")
    infra_data.to_file(infra_path, driver="GeoJSON")
    print(f"Created dummy infrastructure vector: {infra_path.name} ({len(infra_data)} features)")

    # Region of Interest (ROI) - The protected zone (4x4 area centered at 5,5)
    roi_poly = box(3, 3, 7, 7) 
    roi_gdf = gpd.GeoDataFrame({
        'id': [101], 
        'name': ['Protected_Zone_A'], 
        'geometry': [roi_poly]
    }, crs="EPSG:4326")
    return roi_gdf

# --- 2. File Paths and Data Generation ---
RASTER_INPUT = OUTPUT_DIR / "large_satellite_image.tif"
VECTOR_INFRA_INPUT = OUTPUT_DIR / "state_infrastructure.geojson"
ROI_RASTER_OUTPUT = OUTPUT_DIR / "roi_raster_clip.tif"
ROI_VECTOR_OUTPUT = OUTPUT_DIR / "roi_vector_clip.geojson"

# Execute data creation
create_dummy_raster(RASTER_INPUT)
roi_boundary_gdf = create_dummy_vector_data(VECTOR_INFRA_INPUT)

# --- 3. Main Clipping Logic ---

print("\n--- Starting GeoAI Data Preparation (Clipping) ---")

# A. Raster Clipping using rasterio.mask
print("Step A: Clipping large raster to ROI boundary...")

# rasterio.mask expects a list of GeoJSON geometry dictionaries.
# We convert the GeoPandas geometry column to the required format.
geojson_features = json.loads(roi_boundary_gdf.to_json())['features']
geometries = [feature['geometry'] for feature in geojson_features]

with rasterio.open(RASTER_INPUT) as src:
    # Perform the masking operation.
    # 'crop=True' ensures the output raster is the smallest bounding box covering the ROI.
    # 'all_touched=False' ensures only pixels whose center falls within the polygon are included (precise).
    out_image, out_transform = mask(
        dataset=src, 
        shapes=geometries, 
        crop=True, 
        all_touched=False, 
        filled=False 
    )

    # Update the metadata based on the output array's dimensions and new transform
    out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform,
        "nodata": 0 # Set explicit nodata value
    })

    # Write the clipped raster to disk using the updated metadata
    with rasterio.open(ROI_RASTER_OUTPUT, "w", **out_meta) as dest:
        dest.write(out_image)

with rasterio.open(ROI_RASTER_OUTPUT) as clipped:
    print(f"Raster clipping complete. Output saved to: {ROI_RASTER_OUTPUT.name}")
    print(f"  raster: {clipped.width} x {clipped.height} px, "
          f"bounds {tuple(round(value, 2) for value in clipped.bounds)}")

# B. Vector Clipping using GeoPandas
print("\nStep B: Clipping infrastructure vector data to ROI boundary...")

# 1. Load the infrastructure data
infrastructure_gdf = gpd.read_file(VECTOR_INFRA_INPUT)

# 2. Prepare the clipping geometry
# geopandas.clip expects a single geometry object or a GeoSeries/GeoDataFrame.
# Using .union_all() ensures that if the ROI boundary was composed of multiple polygons,
# they are treated as a single, combined clipping area.
clip_geometry = roi_boundary_gdf.geometry.union_all()

# 3. Perform the vector clipping operation
# gpd.clip handles geometric intersection, retaining attributes and clipping partial features.
clipped_infrastructure = gpd.clip(
    infrastructure_gdf, 
    clip_geometry, 
    keep_geom_type=True # Ensures the output geometry type matches the input (e.g., polygon remains polygon)
)

# 4. Save the resulting GeoDataFrame
clipped_infrastructure.to_file(ROI_VECTOR_OUTPUT, driver="GeoJSON")

print(f"Vector clipping complete. Output saved to: {ROI_VECTOR_OUTPUT.name}")
print(f"  vector: {len(clipped_infrastructure)} of {len(infrastructure_gdf)} features kept, "
      f"ids {clipped_infrastructure['id'].tolist()}")
print(f"\nPreparation complete. Clipped data ready for GeoAI model training.")
