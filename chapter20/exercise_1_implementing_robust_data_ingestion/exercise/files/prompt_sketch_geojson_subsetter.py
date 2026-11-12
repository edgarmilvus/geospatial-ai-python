# Setup for exercise 1: the context-manager skeleton.
import json
from typing import Tuple, Dict, List

# 1. Define DataProcessingError here


def safe_geojson_subsetter(input_path: str, output_path: str,
                           bbox_filter: Tuple[float, float, float, float]) -> int:
    """
    Reads GeoJSON data, filters features based on a bounding box, and writes the
    subset to a new file, guaranteeing resource cleanup via context managers.
    Returns the count of features written.
    """
    # Implementation must use nested 'with open(...)' statements for robust
    # resource management. The core logic involves reading the input JSON,
    # iterating through features, applying the bbox_filter (e.g., checking feature
    # coordinates), and writing the filtered results to the output_path.
    pass


# Example usage pattern to test robustness (the solution must provide simulated
# files or mock data):
# feature_count = safe_geojson_subsetter('valid_input.geojson', 'output.geojson', (0, 0, 10, 10))
# print(f"Successfully processed {feature_count} features.")
# safe_geojson_subsetter('non_existent_data.geojson', 'error_output.geojson', (0, 0, 10, 10))
