import math

# 5. EPSG Code Lookup
CRS_NAMES = {
    5070: "NAD83 / Conus Albers (Equal Area)",
    6933: "Equal Earth (Global Equal Area)",
    3857: "WGS 84 / Pseudo-Mercator (Web Mapping)",
}

def get_utm_epsg(lon, lat):
    """Calculates the WGS 84 UTM EPSG code for a given location."""
    # Determine UTM Zone Number (1 to 60)
    zone_number = math.floor((lon + 180) / 6) + 1
    
    # Determine North (326xx) or South (327xx)
    if lat >= 0:
        return int(f"326{zone_number:02d}")
    else:
        return int(f"327{zone_number:02d}")

# 1. Input Function Definition
def recommend_crs(latitude, longitude, goal):
    """Recommends the optimal CRS based on location and goal."""
    goal = goal.upper()
    recommended_epsg = None
    justification = ""

    # 3. Logic Implementation
    if goal == 'AREA':
        # Check for Contiguous US (25°N to 50°N)
        if 25 <= latitude <= 50 and -125 <= longitude <= -65: 
            recommended_epsg = 5070
            justification = f"{CRS_NAMES[5070]} is recommended. This is a continental Equal Area projection optimized for the contiguous US, minimizing area distortion."
        else:
            # Global area comparison
            recommended_epsg = 6933
            justification = f"{CRS_NAMES[6933]} is recommended. This is a global Equal Area projection (Equal Earth), suitable for comparing areas worldwide."
            
    elif goal == 'DISTANCE':
        # Calculate local UTM zone (Equidistant/Conformal)
        recommended_epsg = get_utm_epsg(longitude, latitude)
        zone_str = "North" if latitude >= 0 else "South"
        justification = f"UTM Zone {recommended_epsg % 100} {zone_str} (WGS 84) is recommended. UTM is an equidistant projection optimized for local distance and shape preservation."
        
    elif goal == 'MAPPING':
        # Standard web visualization CRS
        recommended_epsg = 3857
        justification = f"{CRS_NAMES[3857]} is recommended. This is the standard Web Mercator projection used for online map services, prioritizing visual direction and shape over accurate distance/area."
        
    else:
        print("Error: Invalid goal specified.")
        return None

    # 4. Output and Justification
    print("\n--- CRS Recommendation ---")
    lat_label = "N" if latitude >= 0 else "S"
    lon_label = "E" if longitude >= 0 else "W"
    print(f"Input Location: ({abs(latitude):.2f}°{lat_label}, {abs(longitude):.2f}°{lon_label})")
    print(f"Measurement Goal: {goal}")
    print(f"Recommended EPSG Code: {recommended_epsg}")
    print(f"Justification: {justification}")
    return recommended_epsg

# 2. Interactive Input Simulation (using fixed test data for deterministic output)
print("--- Running Test Case 1: Chicago (Distance) ---")
recommend_crs(latitude=41.88, longitude=-87.63, goal='DISTANCE') # UTM Zone 16N

print("\n--- Running Test Case 2: Brazil (Area) ---")
recommend_crs(latitude=-15.78, longitude=-47.93, goal='AREA') # Outside Conus, uses 6933
