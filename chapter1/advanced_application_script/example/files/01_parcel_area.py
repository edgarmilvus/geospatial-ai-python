import geopandas as gpd
from shapely.geometry import Polygon
import pandas as pd
import pyproj
import os
import pathlib
from datetime import datetime

# --- Configuration and Constants ---
# Define the standard Geographic CRS (WGS 84)
GCS_WGS84_EPSG = 4326

# Define the target Projected CRS for the San Francisco area (UTM Zone 10N)
# This is crucial for accurate metric measurement in this region.
PCS_UTM_EPSG = 26910
PCS_UTM_NAME = "NAD83 / UTM zone 10N"

# Define the coordinates for a hypothetical land parcel (in decimal degrees)
# These points define a small, irregular polygon near San Francisco.
# Format: (Longitude, Latitude)
parcel_coordinates_wgs84 = [
    (-122.45, 37.78),  # Point 1 (SW Corner)
    (-122.44, 37.79),  # Point 2 (NW Corner)
    (-122.43, 37.785), # Point 3 (NE Corner)
    (-122.445, 37.775) # Point 4 (SE Corner)
]

def calculate_and_verify_area(coords: list, source_crs: int, target_crs: int, target_crs_name: str):
    """
    Creates a GeoDataFrame, calculates area in the source CRS (for demonstration),
    transforms the data to a target projected CRS, and calculates the accurate area.
    """
    print(f"--- Starting CRS Verification Process ---")
    
    # 1. Geometry Creation (Shapely)
    # Create the polygon object from the raw WGS 84 coordinates.
    try:
        parcel_polygon = Polygon(coords)
    except Exception as e:
        print(f"Error creating Polygon: {e}")
        return

    # 2. GeoDataFrame Initialization (Assigning the Source CRS)
    # A GeoDataFrame is required to manage the CRS metadata.
    gdf = gpd.GeoDataFrame(
        {'name': ['Development Parcel A']},
        geometry=[parcel_polygon],
        crs=f"EPSG:{source_crs}"
    )
    print(f"1. Initial Data Loaded. Source CRS: {gdf.crs}")

    # 3. Area Calculation in Geographic CRS (Demonstrating the Error)
    # The area calculated here is in square decimal degrees, which is not useful.
    area_gcs = gdf.geometry.area.iloc[0]
    print(f"\n2. Area calculated in EPSG:{source_crs} (WGS 84): {area_gcs:.4f} square degrees.")
    print("   (NOTE: This value is mathematically invalid for metric measurement.)")

    # 4. CRS Transformation
    # Transform the GeoDataFrame from the geographic CRS (4326) to the localized projected CRS (26910).
    print(f"\n3. Transforming CRS to Projected System: {target_crs_name} (EPSG:{target_crs})...")
    gdf_projected = gdf.to_crs(epsg=target_crs)
    
    print(f"   Transformation successful. New CRS: {gdf_projected.crs}")

    # 5. Area Calculation in Projected CRS (Accurate Measurement)
    # Since the target CRS is metric (UTM uses meters), the area is now in square meters.
    area_pcs_sq_m = gdf_projected.geometry.area.iloc[0]
    
    # Convert square meters to hectares (1 ha = 10,000 sq m)
    area_pcs_hectares = area_pcs_sq_m / 10000

    print(f"\n4. Accurate Area Calculation (in Projected CRS):")
    print(f"   Area in Square Meters: {area_pcs_sq_m:,.2f} m²")
    print(f"   Area in Hectares:     {area_pcs_hectares:,.4f} ha")
    
    # 6. Verification of Projection Parameters (Using pyproj)
    # We can inspect the properties of the chosen projection.
    crs_obj = pyproj.CRS.from_epsg(target_crs)
    print(f"\n5. Verification of Projection Details (via pyproj):")
    print(f"   Projection Type: {crs_obj.type_name}")
    print(f"   Is Projected: {crs_obj.is_projected}")
    print(f"   Unit of Measure: {crs_obj.axis_info[0].unit_name}")
    
    # 7. Exporting Results (Optional but good practice)
    # Export the projected data for use in other GIS software.
    # Artefacts belong to the project, not to whatever directory this script is
    # started from: `files/` under any shell, one `output/` for the reader.
    output_dir = pathlib.Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    output_filename = output_dir / "parcel_verification.gpkg"
    gdf_projected[['name', 'geometry']].to_file(output_filename, driver="GPKG")
    # Printed relative to the project, so the line carries no machine's paths.
    shown = output_filename.relative_to(output_dir.parent)
    print(f"\n6. Data successfully exported to {shown} with CRS EPSG:{target_crs}.")

# --- Execution ---
if __name__ == "__main__":
    calculate_and_verify_area(
        coords=parcel_coordinates_wgs84,
        source_crs=GCS_WGS84_EPSG,
        target_crs=PCS_UTM_EPSG,
        target_crs_name=PCS_UTM_NAME
    )
