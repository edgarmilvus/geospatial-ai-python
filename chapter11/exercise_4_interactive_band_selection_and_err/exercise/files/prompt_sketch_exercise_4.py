# Required Imports
import rasterio
import sys
import numpy as np
# Assume IMAGE_PATH is defined

def interactive_band_reader(image_path: str):
    """
    Prompts the user for a band number and reads the corresponding band,
    handling input validation and range errors.
    """
    with rasterio.open(image_path) as src:
        band_count = src.count
        
        # POLA: Inform user of the valid range immediately
        print(f"The dataset has {band_count} bands (1-indexed).")
        
        # Your code here: Implement the try/except block and input logic
        
        # Example of the core reading operation (to be placed inside try block):
        # selected_band_data = src.read(band_index)
        
        pass

# interactive_band_reader(IMAGE_PATH)
