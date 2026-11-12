import numpy as np
import matplotlib
matplotlib.use("Agg")          # the run writes a PNG; it never opens a window
import matplotlib.pyplot as plt
import torch
from pathlib import Path

# --- 1. Define Data Simulation Parameters ---
IMAGE_SIZE = 128       # Standard patch size (128x128 pixels)
NUM_CHANNELS = 3       # Standard RGB bands
SEED = 42              # one seed: the same pair on every machine
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"

# The footprint the mask labels, in (row, column) order: 30 rows by 30 columns.
BUILDING = (30, 60, 80, 110)


# --- 2. Simulate the Pair (Input Feature and Target Label) ---
def build_pair(seed=SEED, image_size=IMAGE_SIZE):
    """Return the HWC satellite image and the HW binary mask, spatially consistent.

    The roof is painted where the mask says the building is. That is what
    rasterizing a footprint onto the image grid produces, and it is the property
    the model learns from; a pair whose label sits on noise teaches nothing.
    """
    rng = np.random.default_rng(seed)

    # A patch of 8-bit imagery: (Height, Width, Channels), the format Matplotlib and
    # every image library read without being told twice.
    satellite_image = rng.integers(0, 256, size=(image_size, image_size, NUM_CHANNELS),
                                   dtype=np.uint8)

    # The mask is (Height, Width): one label per pixel, no channel axis.
    ground_truth_mask = np.zeros((image_size, image_size), dtype=np.uint8)
    row_start, row_stop, col_start, col_stop = BUILDING
    ground_truth_mask[row_start:row_stop, col_start:col_stop] = 1

    # A bright feature in the middle that is NOT labelled: a road or a yard. It makes
    # the pair non-trivial, because brightness alone does not define the class.
    center = image_size // 2
    satellite_image[center - 10:center + 10, center - 10:center + 10, :] = 255

    # The roof: light grey with a little per-pixel texture, painted only under the mask.
    roof = rng.integers(-12, 13, size=(row_stop - row_start, col_stop - col_start,
                                       NUM_CHANNELS))
    satellite_image[row_start:row_stop, col_start:col_stop, :] = np.clip(
        210 + roof, 0, 255).astype(np.uint8)

    return satellite_image, ground_truth_mask


# --- 3. Visualization ---
def plot_pair(satellite_image, ground_truth_mask, path):
    """Draw the pair side by side and write it to disk."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle("Simulated Geospatial Segmentation Data Pair (HWC Format)")

    axes[0].imshow(satellite_image)
    axes[0].set_title("Input Image (RGB)")
    axes[0].axis('off')

    # 'binary' keeps 0 black and 1 white: a mask with two classes reads better than
    # one rendered on a continuous colour map.
    axes[1].imshow(ground_truth_mask, cmap='binary')
    axes[1].set_title("Target Mask (Building Footprint)")
    axes[1].axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


# --- 4. The Conversion a Model Expects ---
def to_tensors(satellite_image, ground_truth_mask):
    """HWC -> CHW for the image, and a float mask with a channel axis for the loss."""
    # 1. Transpose the axes to CWH format: (128, 128, 3) -> (3, 128, 128)
    cwh_image = satellite_image.transpose((2, 0, 1))
    # 2. Float in [0, 1]. Dividing uint8 by 255 is the normalisation every RGB
    #    encoder assumes before its own mean/std.
    image_tensor = torch.from_numpy(cwh_image).float() / 255.0
    # 3. The mask keeps its shape and gains a channel axis: (H, W) -> (1, H, W).
    mask_tensor = torch.from_numpy(ground_truth_mask).float().unsqueeze(0)
    return image_tensor, mask_tensor


# --- 5. Main Execution Flow ---
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    satellite_image, ground_truth_mask = build_pair()

    print("--- Data Structure Check ---")
    print(f"Satellite Image Shape (H, W, C): {satellite_image.shape}")
    print(f"Mask Shape (H, W): {ground_truth_mask.shape}")
    print(f"Image Data Type: {satellite_image.dtype}")
    print(f"Mask Data Type: {ground_truth_mask.dtype}")

    # The two first dimensions must agree, or the loss cannot be computed at all.
    same_grid = satellite_image.shape[:2] == ground_truth_mask.shape
    building_pixels = int(ground_truth_mask.sum())
    print(f"\nHeight and width match: {same_grid}")
    print(f"Mask classes: {sorted(np.unique(ground_truth_mask).tolist())}")
    print(f"Building pixels: {building_pixels} of {ground_truth_mask.size} "
          f"({100 * building_pixels / ground_truth_mask.size:.2f}%)")

    roof = satellite_image[ground_truth_mask == 1]
    background = satellite_image[ground_truth_mask == 0]
    print(f"Mean intensity under the mask: {roof.mean():.1f}")
    print(f"Mean intensity everywhere else: {background.mean():.1f}")

    figure = plot_pair(satellite_image, ground_truth_mask,
                       OUTPUT_DIR / "segmentation_pair.png")

    image_tensor, mask_tensor = to_tensors(satellite_image, ground_truth_mask)
    print("\n--- PyTorch Tensors ---")
    print(f"Image tensor: {tuple(image_tensor.shape)} {image_tensor.dtype} "
          f"range [{image_tensor.min():.3f}, {image_tensor.max():.3f}]")
    print(f"Mask tensor:  {tuple(mask_tensor.shape)} {mask_tensor.dtype} "
          f"range [{mask_tensor.min():.1f}, {mask_tensor.max():.1f}]")

    print(f"\nWrote {figure.name}")
    return {
        "image_shape": tuple(int(v) for v in satellite_image.shape),
        "mask_shape": tuple(int(v) for v in ground_truth_mask.shape),
        "image_dtype": str(satellite_image.dtype),
        "mask_dtype": str(ground_truth_mask.dtype),
        "building_pixels": building_pixels,
        "roof_mean": float(roof.mean()),
        "background_mean": float(background.mean()),
        "tensor_shape": tuple(int(v) for v in image_tensor.shape),
        "mask_tensor_shape": tuple(int(v) for v in mask_tensor.shape),
        "tensor_max": float(image_tensor.max()),
        "figure": figure.name,
    }


if __name__ == "__main__":
    main()
