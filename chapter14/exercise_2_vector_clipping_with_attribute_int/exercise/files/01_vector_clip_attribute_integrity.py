import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
import pathlib

# Everything this listing writes goes into the project's own output folder.
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Mock Data Setup (Simulating loading from files) ---
# 1. Create a large administrative boundary GeoDataFrame (Counties)
data = {
    'County_Name': ['Alpha', 'Beta', 'Gamma', 'Delta'],
    'Population_2020': [50000, 120000, 80000, 95000],
    'geometry': [
        Polygon([(0, 0), (0, 10), (10, 10), (10, 0)]),
        Polygon([(10, 0), (10, 10), (20, 10), (20, 0)]),
        Polygon([(20, 0), (20, 10), (30, 10), (30, 0)]),
        Polygon([(30, 0), (30, 10), (40, 10), (40, 0)])
    ]
}
counties_gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

# 2. Create the clipping boundary (ROI)
roi_geom = Polygon([(5, 5), (5, 15), (15, 15), (15, 5)])
roi_gdf = gpd.GeoDataFrame({'id': [1], 'geometry': [roi_geom]}, crs="EPSG:4326")

# --------------------------------------------------------

# 3. Clipping Operation
clipped_gdf = gpd.clip(counties_gdf, roi_gdf)

# 4. Attribute Validation
print("--- Validation Check ---")
print(f"Clipped features: {len(clipped_gdf)} of {len(counties_gdf)}")
if not clipped_gdf.empty:
    # Select the first row of the clipped data (which should be County Alpha)
    sample_clipped = clipped_gdf.iloc[0]
    
    # Find the corresponding original feature (using County_Name for lookup)
    original_feature = counties_gdf[counties_gdf['County_Name'] == sample_clipped['County_Name']].iloc[0]

    # Check attribute preservation
    is_name_preserved = sample_clipped['County_Name'] == original_feature['County_Name']
    is_pop_preserved = sample_clipped['Population_2020'] == original_feature['Population_2020']

    print(f"Clipped Feature Name: {sample_clipped['County_Name']}")
    print(f"Clipped Population: {sample_clipped['Population_2020']}")
    print(f"Attribute Integrity Check (Name): {is_name_preserved}")
    print(f"Attribute Integrity Check (Population): {is_pop_preserved}")
    
    if is_name_preserved and is_pop_preserved:
        print("Validation Successful: Attributes were preserved during clipping.")
else:
    print("No features were clipped.")

# 5. Output (Saving to GeoJSON)
output_path = OUTPUT_DIR / "clipped_boundaries.geojson"
clipped_gdf.to_file(output_path, driver='GeoJSON')
print(f"\nClipped GeoDataFrame saved to {output_path.name}")

# Handling Edge Cases Documentation (as required by prompt)
# Note: gpd.clip inherently handles geometries that are partially within the ROI. 
# It performs an intersection operation, splitting the geometry at the boundary 
# and retaining only the part that overlaps with the ROI. The attributes 
# (County_Name, Population_2020) are automatically copied to the new, split geometry.
