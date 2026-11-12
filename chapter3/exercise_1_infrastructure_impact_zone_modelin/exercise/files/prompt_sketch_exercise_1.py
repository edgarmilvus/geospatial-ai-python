# Setup: Assume pipeline_gdf and parcels_gdf are loaded and reprojected to a metric CRS.
# The task requires a multi-step process involving buffering, overlay, and attribute joining.

# Step 1: Generate the buffer (500m).
# Step 2: Perform the spatial overlay (intersection) to find the overlap geometries.
# Step 3: Calculate the area of the resulting overlap geometries.
# Step 4: Join the original parcel area attribute back to the intersected results.
# Step 5: Calculate the final impact percentage.

# Write the GeoPandas code necessary to execute Steps 1, 2, 3, 4, and 5,
# resulting in the final GeoDataFrame 'final_impact_analysis_gdf'.
