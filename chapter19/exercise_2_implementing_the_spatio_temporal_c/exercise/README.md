# Exercise 2 — the ST-Conv block

## What it does

Builds one ST-Conv block in PyTorch: a gated temporal convolution, a spatial
convolution in the Chebyshev basis of the scaled Laplacian, and a second gated
temporal convolution, with a residual path that reslices the shortened time axis.
It runs one forward pass on a 50-link network and one backward pass to show the
gradient reaches the input.

## The listings

| file | what it is |
| --- | --- |
| `01_stconv_block.py` | the solution: the Laplacian, the polynomials, the two layers, the block |
| `run_stconv_block.py` | the harness: the recurrence, the spectrum, the shapes, the parameter count |

## Run it

```bash
cd chapter19/exercise_2_implementing_the_spatio_temporal_c/exercise/files
python3 01_stconv_block.py
```

It prints the adjacency and spectrum, the Chebyshev stack, the input and output
shapes, the time-axis arithmetic, the parameter count and the gradient norm at the
input, then writes them to `output/`. `run_stconv_block.py` asserts that `T_0` is the
identity, that `T_out = 12 - 2*(3-1) = 8`, that the block holds 90 624 parameters,
and exits non-zero if the residual path stops carrying gradient.

```text
--- ST-Conv block ---
Adjacency shape (N, N): (50, 50)
Scaled Laplacian spectrum: [-0.8057, 1.0000]
Chebyshev terms for K=3: (3, 50, 50)
Input X shape (B, T_in, N, F_in): (4, 12, 50, 5)
Output H shape (B, T_out, N, F_out): (4, 8, 50, 64)
T_out = T_in - 2*(Kt-1) = 12 - 4 = 8
Trainable parameters: 90624
Gradient norm at the input after one backward pass: 0.0007
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/stconv_block.json` | shapes, the kernel sizes, the parameter count, the spectrum |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/stconv_block_exercise.json` | the same shapes, the gradient norm, the basis checks |

## Notes

- The book showed a TensorFlow/Keras sketch for this exercise and the surrounding
  prose asked for PyTorch. The listing is now PyTorch, so the block can be trained
  by exercise 3 without a second framework in the environment.
- `TensorFlow`'s `'valid'` padding becomes PyTorch's default `padding=0` on a
  `Conv1d`, so two temporal convolutions shorten twelve steps to eight. The residual
  path therefore needs both a 1x1 convolution (channels) and a slice (time).
- Degrees are counted from `A + I`. A sparsity cut can leave a link with no
  neighbours, and `D^-1/2` for that link is a division by zero.
