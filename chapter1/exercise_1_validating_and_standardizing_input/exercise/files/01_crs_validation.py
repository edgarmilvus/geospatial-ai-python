import pyproj
from pyproj.exceptions import CRSError

# 3. Define custom exception class
class InvalidCRSDefinitionError(Exception):
    """Custom exception raised for invalid or unparsable CRS definitions."""
    pass

def standardize_crs(input_crs):
    """
    Parses a CRS definition using pyproj, standardizes it to an integer EPSG code,
    and validates if it's a GCS or PCS.
    """
    print(f"\n--- Processing Input: {input_crs} ({type(input_crs).__name__}) ---")
    
    try:
        # 1. CRS Definition Handling: Robustly parse the input
        crs = pyproj.CRS.from_user_input(input_crs)
        
    except (CRSError, TypeError) as e:
        # 3. Error Handling: Catch parsing errors (e.g., malformed string)
        raise InvalidCRSDefinitionError(f"Failed to parse CRS input '{input_crs}'. Underlying error: {e}")

    # 2. Validation Check: Must be GCS or PCS
    if not (crs.is_geographic or crs.is_projected):
        raise InvalidCRSDefinitionError(
            f"CRS '{crs.name}' is not a standard Geographic or Projected Coordinate System."
        )

    # Attempt to retrieve the EPSG code
    epsg_code = crs.to_epsg()

    if epsg_code is not None:
        print(f"Standardized EPSG Code: {epsg_code}")
        return int(epsg_code)
    else:
        print(f"CRS parsed successfully but has no standard EPSG code. Name: {crs.name}")
        return None

# 4. Testing Data
wkt_wgs84 = """GEOGCRS["WGS 84",
    DATUM["World Geodetic System 1984",
        ELLIPSOID["WGS 84",6378137,298.257223563,
            LENGTHUNIT["metre",1]]],
    PRIMEM["Greenwich",0,
        ANGLEUNIT["degree",0.0174532925199433]],
    CS[ellipsoidal,2],
        AXIS["geodetic latitude (Lat)",north,
            ORDER[1],
            ANGLEUNIT["degree",0.0174532925199433]],
        AXIS["geodetic longitude (Lon)",east,
            ORDER[2],
            ANGLEUNIT["degree",0.0174532925199433]],
    ID["EPSG",4326]]"""
test_inputs = [
    4326,
    'EPSG:3857',
    wkt_wgs84,
    'WGS 84 ZONEX'  # Intentionally malformed
]

for input_crs in test_inputs:
    try:
        standardize_crs(input_crs)
    except InvalidCRSDefinitionError as e:
        print(f"Error Caught: {e}")
