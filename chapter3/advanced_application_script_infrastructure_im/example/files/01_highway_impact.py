"""Chapter 3, example 2 — a highway expansion impact assessment.

A proposed route through the Minneapolis area, two protected wetlands and five
parcels, all created in WGS 84 lon/lat. The script then behaves the way the
chapter insists: it reprojects to UTM zone 15N before it buffers 50 metres,
joins the parcels that fall inside the corridor, and intersects the route with
the wetlands to measure how many metres of road cross protected ground.

Buffering 50 *degrees* would swallow the whole state; that is the mistake this
listing is written to avoid, so the two steps are printed with their CRS.
"""
import warnings

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon

# The length below is taken in degrees on purpose, to show why it is the wrong
# number. geopandas warns about that; the listing reports both figures instead.
warnings.filterwarnings('ignore', message='Geometry is in a geographic CRS')

# --- 1. Data Simulation and Setup ---
# Define a standard Geographic CRS (WGS84) for initial data creation
WGS84_CRS = "EPSG:4326"
# Define a Projected CRS (UTM Zone 15N) for accurate metric calculations (meters)
UTM_CRS = "EPSG:32615"

print("--- Starting Infrastructure Impact Analysis ---")

# A. Simulate the Proposed Highway Route (LineString)
# Roughly four kilometres of new road north of Minneapolis, in lon/lat.
highway_geom = LineString([
    (-93.266321, 44.973130),
    (-93.262529, 44.975839),
    (-93.258712, 44.973148),
    (-93.254920, 44.975857),
])
highway_gdf = gpd.GeoDataFrame(
    {'route_id': [101], 'status': ['Proposed']},
    geometry=[highway_geom],
    crs=WGS84_CRS
)

# B. Simulate Protected Wetlands (Polygons)
wetlands_data = [
    {'name': 'Wetland A', 'area_sqkm': 0.04, 'geometry': Polygon([
        (-93.265689, 44.973582), (-93.263153, 44.973588),
        (-93.263161, 44.975388), (-93.265698, 44.975382)])},
    {'name': 'Wetland B', 'area_sqkm': 0.06, 'geometry': Polygon([
        (-93.257448, 44.974051), (-93.254278, 44.974058),
        (-93.254287, 44.976308), (-93.257458, 44.976301)])},
]
wetlands_gdf = gpd.GeoDataFrame(wetlands_data, crs=WGS84_CRS)

# C. Simulate Residential Parcels (Points)
parcel_data = [
    {'pid': 1, 'type': 'Residential', 'geometry': Point(-93.264425, 44.974485)},
    {'pid': 2, 'type': 'Commercial', 'geometry': Point(-93.262275, 44.975660)},
    {'pid': 3, 'type': 'Residential', 'geometry': Point(-93.259974, 44.971794)},
    {'pid': 4, 'type': 'Residential', 'geometry': Point(-93.255553, 44.975675)},
    {'pid': 5, 'type': 'Residential', 'geometry': Point(-93.258208, 44.973869)},
]
parcels_gdf = gpd.GeoDataFrame(parcel_data, crs=WGS84_CRS)


# --- 2. Spatial Operation 1: Buffering for Proximity Analysis ---

# The route is 1 272 m long in metres, but that number cannot be read in degrees.
print(f"\n[0/3] Route length: {highway_gdf.geometry.length.iloc[0]:.4f} degrees "
      f"-> {highway_gdf.to_crs(UTM_CRS).geometry.length.iloc[0]:.2f} m after reprojection")

# Reproject to UTM for accurate meter-based buffering (50 meters)
highway_utm = highway_gdf.to_crs(UTM_CRS)
print(f"[1/3] Calculating 50-meter buffer (using CRS: {UTM_CRS})...")

# Create the impact zone buffer
impact_zone_gdf = highway_utm.buffer(50)
# Convert the resulting geometry series back into a GeoDataFrame for joining
impact_zone_gdf = gpd.GeoDataFrame(geometry=impact_zone_gdf, crs=UTM_CRS)


# --- 3. Spatial Operation 2: Spatial Join for Affected Parcels ---

# Ensure parcels are also in the metric CRS for the join operation
parcels_utm = parcels_gdf.to_crs(UTM_CRS)

print(f"[2/3] Performing Spatial Join to identify affected residential parcels...")

# Perform the spatial join: Find all parcels *within* the impact zone.
# We use 'within' predicate here, joining the attributes of the parcels (left)
# to the geometry of the impact zone (right).
affected_parcels_join = gpd.sjoin(
    parcels_utm,
    impact_zone_gdf,
    how='inner',
    predicate='within'
)

# Filter the results to only include 'Residential' types for the final count
affected_residential_parcels = affected_parcels_join[
    affected_parcels_join['type'] == 'Residential'
]

print(f"   -> Total affected residential parcels identified: {len(affected_residential_parcels)}")


# --- 4. Spatial Operation 3: Intersection for Environmental Conflict ---

# Ensure both layers are in the metric CRS for accurate area calculation
wetlands_utm = wetlands_gdf.to_crs(UTM_CRS)

print(f"[3/3] Calculating geometric intersection with protected wetlands...")

# Use GeoPandas overlay function with 'intersection' op
# This returns a new GeoDataFrame containing only the overlapping geometries.
conflict_area_gdf = gpd.overlay(
    highway_utm,
    wetlands_utm,
    how='intersection'
)

# Calculate the length of the intersected line segments (in meters)
conflict_area_gdf['conflict_length_m'] = conflict_area_gdf.geometry.length

# Calculate the total length of the highway intersecting wetlands
total_conflict_length = conflict_area_gdf['conflict_length_m'].sum()

print(f"   -> Total length of highway intersecting wetlands: {total_conflict_length:.2f} meters.")

# --- 5. Reporting and Cleanup ---

print("\n--- Summary of Impact Assessment ---")
print(f"1. Residential Parcels within 50m Buffer: {len(affected_residential_parcels)}")
print(f"2. Total Highway Conflict Length (Wetlands): {total_conflict_length:.2f} m")

# Display the PIDs of the affected parcels
if not affected_residential_parcels.empty:
    print(f"   Affected Parcel IDs: {affected_residential_parcels['pid'].tolist()}")

# Display the names of the affected wetlands
if not conflict_area_gdf.empty:
    print(f"   Wetlands affected: {conflict_area_gdf['name'].unique().tolist()}")
