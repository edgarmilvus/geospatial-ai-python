import pyproj
import sys # Used for detailed object inspection later

# --- 1. Define Standard CRS Identifiers ---
# EPSG:4326 is the standard World Geodetic System 1984 (WGS 84).
# This is a Geographic CRS, using latitude and longitude (degrees).
WGS84_EPSG = 4326

# EPSG:3857 is Web Mercator (Spherical Mercator).
# This is a Projected CRS, using Easting and Northing (meters).
WEB_MERCATOR_EPSG = 3857

print("--- Initializing pyproj CRS Objects ---")

# --- 2. Instantiate the WGS 84 Geographic CRS object ---
# pyproj.CRS.from_epsg() reads the complex definition associated with the code.
try:
    geographic_crs = pyproj.CRS.from_epsg(WGS84_EPSG)
    print(f"Successfully loaded WGS 84 (EPSG:{WGS84_EPSG})")
except pyproj.exceptions.CRSError as e:
    print(f"Error loading WGS 84 CRS: {e}")
    sys.exit(1)

# --- 3. Instantiate the Web Mercator Projected CRS object ---
try:
    projected_crs = pyproj.CRS.from_epsg(WEB_MERCATOR_EPSG)
    print(f"Successfully loaded Web Mercator (EPSG:{WEB_MERCATOR_EPSG})\n")
except pyproj.exceptions.CRSError as e:
    print(f"Error loading Web Mercator CRS: {e}")
    sys.exit(1)


# --- 4. Examine and Print Properties of the Geographic CRS ---
print("--- Detailed Analysis of Geographic CRS (WGS 84) ---")

# The name property provides the human-readable identifier.
print(f"1. Name: {geographic_crs.name}")

# These boolean properties confirm the CRS type.
print(f"2. Is Geographic: {geographic_crs.is_geographic}")
print(f"3. Is Projected: {geographic_crs.is_projected}")

# Check the coordinate axis definitions (order and units).
# WGS 84 often defaults to Latitude/Longitude (North/East).
axis_1 = geographic_crs.axis_info[0]
axis_2 = geographic_crs.axis_info[1]
print(f"4. Axis Order/Units: {axis_1.name} ({axis_1.unit_name}), {axis_2.name} ({axis_2.unit_name})")

# The Well-Known Text (WKT) is the full, standardized string definition.
# We print only a snippet for readability.
wkt_snippet = geographic_crs.to_wkt(pretty=True).split('\n')[0:3]
print(f"5. WKT Representation (Snippet):\n{''.join(wkt_snippet)}...")


# --- 5. Examine and Print Properties of the Projected CRS ---
print("\n--- Detailed Analysis of Projected CRS (Web Mercator) ---")

print(f"1. Name: {projected_crs.name}")

# Note the inversion of boolean flags compared to WGS 84.
print(f"2. Is Geographic: {projected_crs.is_geographic}")
print(f"3. Is Projected: {projected_crs.is_projected}")

# Check the coordinate axis definitions for the projected system.
# Projected systems typically use Easting/Northing (X/Y).
p_axis_1 = projected_crs.axis_info[0]
p_axis_2 = projected_crs.axis_info[1]
print(f"4. Axis Order/Units: {p_axis_1.name} ({p_axis_1.unit_name}), {p_axis_2.name} ({p_axis_2.unit_name})")

# Projected systems must define a specific unit of measurement for distances.
# The unit lives on the axis, not on the CRS: this is where a metre is declared.
print(f"5. Linear Unit of Measurement: {projected_crs.axis_info[0].unit_name}")

# Projected systems also contain a defined projection method (e.g., Mercator).
print(f"6. Projection Method Name: {projected_crs.to_json_dict().get('conversion', {}).get('method', {}).get('name')}")
