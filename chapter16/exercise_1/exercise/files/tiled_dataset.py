import math
import random
from pathlib import Path

import numpy as np
import torch
from rasterio.windows import Window
from torch.utils.data import Dataset

# Example of required global statistics (Placeholder values)
MEAN_STATS = [0.298, 0.315, 0.289]
STD_STATS = [0.101, 0.098, 0.105]

TILE_SIZE = 256
SCENE_WIDTH = 10_000     # the scene the exercise describes: 10 000 x 10 000 pixels
SCENE_HEIGHT = 10_000
SEED = 3                 # one seed: the same scene, the same augmentation, every run
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# Roofs repeat on a 256-pixel block: 100 rows by 150 columns of every block, which is
# 22.9% of the scene. A real mask comes from rasterized footprints; these rectangles
# are what rasterizing them onto a fixed grid looks like.
BLOCK = 256
ROOF_ROWS = (40, 140)
ROOF_COLS = (40, 190)
ROOF_INTENSITY = 0.90    # a roof reflects more than bare ground in these three bands


# --- The File Reader, Stands In for rasterio.open -------------------------------
# The exercise's data is a real GeoTIFF the reader does not have. This stand-in
# answers the two calls the dataset makes — `.width/.height` and `.read(window=...)`
# — from a value derived from each pixel's absolute coordinates, so a tile read at
# any offset is reproducible and two reads of the same window agree exactly.
def _noise(row_start, row_stop, col_start, col_stop, seed):
    """Three deterministic [0, 1) planes for the absolute coordinates asked for."""
    rows = np.arange(row_start, row_stop, dtype=np.float64)[:, None]
    cols = np.arange(col_start, col_stop, dtype=np.float64)[None, :]
    planes = []
    for channel in range(3):
        phase = np.sin(rows * 12.9898 + cols * 78.233 + seed * 3.7 + channel * 1.3)
        value = phase * 43758.5453
        planes.append(value - np.floor(value))
    return np.stack(planes)


def _roof(row_start, row_stop, col_start, col_stop):
    """True where the pixel is inside a roof: a rectangle on every 512-pixel block."""
    rows = np.arange(row_start, row_stop)[:, None] % BLOCK
    cols = np.arange(col_start, col_stop)[None, :] % BLOCK
    return ((rows >= ROOF_ROWS[0]) & (rows < ROOF_ROWS[1]) &
            (cols >= ROOF_COLS[0]) & (cols < ROOF_COLS[1]))


class MockRaster:
    """The slice of `rasterio.DatasetReader` this dataset uses, and nothing more."""

    def __init__(self, width, height, count, seed, is_mask=False):
        self.width = width
        self.height = height
        self.count = count
        self.seed = seed
        self.is_mask = is_mask
        self.last_window = None
        self.pixels_read = 0

    def read(self, indexes=None, window=None):
        if window is None:
            row_off, col_off, height, width = 0, 0, self.height, self.width
        else:
            # int(), because a Window built from division can carry floats.
            row_off, col_off = int(window.row_off), int(window.col_off)
            height, width = int(window.height), int(window.width)

        self.last_window = (col_off, row_off, width, height)
        self.pixels_read += width * height

        if self.is_mask:
            data = _roof(row_off, row_off + height,
                         col_off, col_off + width).astype(np.float32)[None]
        else:
            noise = _noise(row_off, row_off + height, col_off, col_off + width, self.seed)
            mean = np.array(MEAN_STATS, dtype=np.float64)[:, None, None]
            deviation = np.array(STD_STATS, dtype=np.float64)[:, None, None]
            # A uniform on [m - s*sqrt(3), m + s*sqrt(3)] has mean m and deviation s,
            # so the scene really is the distribution the statistics describe.
            data = mean + deviation * (2.0 * noise - 1.0) * math.sqrt(3.0)
            data = np.where(_roof(row_off, row_off + height, col_off, col_off + width)[None],
                            ROOF_INTENSITY, data)
            data = data.astype(np.float32)

        if indexes is not None:
            selected = [indexes] if isinstance(indexes, int) else list(indexes)
            data = data[[index - 1 for index in selected]]
        return data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def mock_rasterio_open(path, seed=SEED):
    if "mask" in str(path):
        return MockRaster(SCENE_WIDTH, SCENE_HEIGHT, 1, seed, is_mask=True)
    return MockRaster(SCENE_WIDTH, SCENE_HEIGHT, 3, seed)


# --- The Dataset ---------------------------------------------------------------
class BuildingSegmentationDataset(Dataset):
    """
    A custom PyTorch Dataset that loads tiles dynamically from large GeoTIFF files
    using rasterio windowed reading, minimizing memory footprint.
    """

    def __init__(self, image_path, mask_path, tile_size=TILE_SIZE, seed=SEED):
        self.image_path = image_path
        self.mask_path = mask_path
        self.tile_size = tile_size
        self.seed = seed

        # 1. Metadata only: the arrays are never loaded whole.
        with mock_rasterio_open(image_path, seed) as src:
            self.width = src.width
            self.height = src.height

        # 2. The grid of tiles: 10 000 / 256 rounds up to 40, so 40 x 40 = 1 600.
        self.n_cols = math.ceil(self.width / self.tile_size)
        self.n_rows = math.ceil(self.height / self.tile_size)
        self.total_tiles = self.n_rows * self.n_cols

        # Set by __getitem__, so a caller can see what was read and how it was turned.
        self.last_window = None
        self.last_rotation = None
        self.last_read_pixels = 0

    def __len__(self):
        return self.total_tiles

    def __getitem__(self, index):
        if index < 0 or index >= self.total_tiles:
            raise IndexError(f"tile {index} is outside 0..{self.total_tiles - 1}")

        # 1. Pixel coordinates of the tile this index names.
        row_idx, col_idx = divmod(index, self.n_cols)
        x_start = col_idx * self.tile_size
        y_start = row_idx * self.tile_size
        width = min(self.tile_size, self.width - x_start)
        height = min(self.tile_size, self.height - y_start)
        window = Window(x_start, y_start, width, height)
        self.last_window = (x_start, y_start, width, height)

        # 2. Windowed reads: only this tile crosses the disk.
        with mock_rasterio_open(self.image_path, self.seed) as image_src, \
                mock_rasterio_open(self.mask_path, self.seed) as mask_src:
            image = image_src.read(window=window).astype(np.float32)
            mask = mask_src.read(window=window).astype(np.float32)
            self.last_read_pixels = image_src.pixels_read

        # 3a. Edge tiles are smaller than the grid; pad them back to tile_size.
        #     The image is padded by reflection, the mask with zeros: a reflected roof
        #     is still a roof, and an invented label at the edge of the scene is not.
        if height < self.tile_size or width < self.tile_size:
            pad_h = self.tile_size - height
            pad_w = self.tile_size - width
            image = np.pad(image, ((0, 0), (0, pad_h), (0, pad_w)), mode="reflect")
            mask = np.pad(mask, ((0, 0), (0, pad_h), (0, pad_w)), mode="constant")

        # 3b. Normalisation, channel by channel, with statistics from the whole scene.
        for channel in range(image.shape[0]):
            image[channel] = (image[channel] - MEAN_STATS[channel]) / STD_STATS[channel]

        # 3c. The same rotation on both, chosen from the index: a run repeats exactly.
        turns = random.Random(self.seed + index).choice([0, 1, 2, 3])
        image = np.rot90(image, k=turns, axes=(1, 2)).copy()
        mask = np.rot90(mask, k=turns, axes=(1, 2)).copy()
        self.last_rotation = turns

        # 4. (C, H, W) and (1, H, W), float32: what the model and the loss want.
        return torch.from_numpy(image).float(), torch.from_numpy(mask).float()


# --- Demonstration -------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset = BuildingSegmentationDataset("scene_image.tif", "scene_mask.tif")
    print(f"Scene: {dataset.width} x {dataset.height} pixels")
    print(f"Grid: {dataset.n_rows} rows x {dataset.n_cols} columns "
          f"= {len(dataset)} tiles of {dataset.tile_size} px")

    for index in (0, 41, len(dataset) - 1):
        image, mask = dataset[index]
        x_start, y_start, width, height = dataset.last_window
        roof = float(mask.sum())
        print(f"\ntile {index}: window x={x_start} y={y_start} {width} x {height} px, "
              f"rotated {90 * dataset.last_rotation}°")
        print(f"  image {tuple(image.shape)} {image.dtype}, "
              f"mean {float(image.mean()):+.3f}, std {float(image.std()):.3f}")
        print(f"  mask  {tuple(mask.shape)} {mask.dtype}, "
              f"{roof:.0f} roof pixels ({100 * roof / mask.numel():.2f}%)")

    image, mask = dataset[41]
    background = mask[0] == 0
    print(f"\nTile 41 read {dataset.last_read_pixels:,} pixels, "
          f"not the {dataset.width * dataset.height:,} of the whole scene.")
    print(f"Normalized mean on background pixels: "
          f"{[round(float(image[channel][background].mean()), 3) for channel in range(3)]}")
    print(f"Normalized mean on roof pixels: "
          f"{[round(float(image[channel][~background].mean()), 3) for channel in range(3)]}")

    return dataset


if __name__ == "__main__":
    main()
