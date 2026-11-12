# Example 1 — the image/mask pair a segmentation model is fed

## What it does

Builds one 128 x 128 RGB patch and its 128 x 128 binary mask, paints the roof under the
label it belongs to, then converts the pair to the tensors PyTorch expects: a 3 x 128 x 128
float image in [0, 1] and a 1 x 128 x 128 mask. It prints the shapes, the dtypes, the class
count and the mean intensity on each side of the label.

## The listings

| file | what it is |
| --- | --- |
| `simulate_segmentation_pair.py` | the example: pair, figure, tensor conversion |
| `run_simulate_segmentation_pair.py` | the harness: grid, label, brightness, transpose |

## Run it

```bash
cd chapter16/basic_code_example_simulating_and_visualizing/example/files
python3 simulate_segmentation_pair.py
```

It writes `output/segmentation_pair.png` and prints the structure check, the class
balance and the two tensor shapes. `run_simulate_segmentation_pair.py` asserts that the
mask is on the image's grid, that the 900 labelled pixels are the brightest region, that
brightness alone does not define the class, and that the transpose moves axes and not
pixels; it exits non-zero when any of those changes.

```text
--- Data Structure Check ---
Satellite Image Shape (H, W, C): (128, 128, 3)
Mask Shape (H, W): (128, 128)
Image Data Type: uint8
Mask Data Type: uint8

Height and width match: True
Mask classes: [0, 1]
Building pixels: 900 of 16384 (5.49%)
Mean intensity under the mask: 209.9
Mean intensity everywhere else: 129.9
```

## What it produces

| path | what it is |
| --- | --- |
| `output/segmentation_pair.png` | the chip and its mask, side by side |
| `output/segmentation_pair.json` | the harness's shapes, class balance and means |

## Notes

- The `plt.show()` of the draft is gone: the figure goes to `output/` with the Agg
  backend, so a headless run does not block on a window.
- The book's draft drew the bright feature in the middle and the mask in the corner, so
  the pair was not spatially consistent. Here the roof is painted under the label, and the
  bright 20 x 20 block in the centre is deliberately *not* labelled: it is a road, and it
  is what makes "brightness is not the class" a checkable statement.
- Everything is seeded (`np.random.default_rng(42)`); two runs produce the same PNG.
- Needs `torch` (`pip install -r requirements-ml.txt`). Without it the harness prints
  `skip` and ends green with 0 assertions. The listing itself takes under a second.
