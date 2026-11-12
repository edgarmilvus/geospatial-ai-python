# Setup: Assume extraction_sites_gdf, sensitive_areas_gdf, and concession_boundaries_gdf are loaded
# and all are in an appropriate metric CRS.

# Part A: Implement the Proximity Flag (Buffer + Join).
# Part B: Implement the Concession ID Assignment (Join).
# Part C: Implement the Quantified Impact Area (Buffer + Intersection + Aggregation + Join).

# Write the complete GeoPandas pipeline required to generate the final 'enriched_sites_gdf'.
# Pay specific attention to how intermediate aggregated results are merged back
# into the original point GeoDataFrame without losing the original index or attributes.
