# Required structure for Exercise 1.
# A sketch, not a program: every body is `pass`, because filling them is the exercise.
import torch
from torch.utils.data import Dataset
import rasterio
import numpy as np


class BuildingSegmentationDataset(Dataset):
    """
    A custom PyTorch Dataset that loads tiles dynamically from large GeoTIFF files
    using rasterio windowed reading, minimizing memory footprint.
    """
    def __init__(self, image_path, mask_path, tile_size=256):
        # 1. Load metadata (profile/transform) but not the full array.
        # 2. Calculate the total number of tiles (N_rows * N_cols).
        pass

    def __len__(self):
        # Return the total number of tiles.
        pass

    def __getitem__(self, index):
        # 1. Determine the window/coordinates for the 'index'.
        # 2. Use rasterio.open().read(window=...) for efficient loading.
        # 3. Apply normalization and synchronized augmentation.
        # 4. Return tensors.
        pass


# Example of required global statistics (Placeholder values)
MEAN_STATS = [0.298, 0.315, 0.289]
STD_STATS = [0.101, 0.098, 0.105]
