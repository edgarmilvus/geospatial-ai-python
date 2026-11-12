# Exercise 2 — the SE block in the bottleneck, and a training run that proves it

## What it does

Implements a Squeeze-and-Excitation block — global average pool, 64 -> 4 -> 64, sigmoid,
rescale — puts it between the bottleneck and the decoder of a small U-Net, and trains that
U-Net for 60 full-batch steps on six synthetic 64 x 64 chips. It prints the parameter table,
the loss per tenth epoch and the IoU on the training chips and on two held-out ones.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_exercise_2.py` | the book's required structure, bodies left as `pass` |
| `se_unet.py` | the solution: SE block, U-Net, chips, training, IoU |
| `run_se_unet.py` | the harness: shape, gate, gradient, parameters, curve, IoU |

## Run it

```bash
cd chapter16/exercise_2_modifying_u_net_for_enhanced_featu/exercise/files
python3 se_unet.py
```

It builds the model, prints the bottleneck's shape before and after the SE block, trains and
reports the loss and the two IoUs. `run_se_unet.py` asserts that the block preserves the
shape, carries exactly 512 parameters, receives a gradient, and that the loss falls and the
mask overlaps; it exits non-zero when the block is a no-op or the curve stops descending.

```text
Output logits: (6, 1, 64, 64), range [-0.27, 3.08]
Bottleneck shape in/out of the SE block: (2, 64, 16, 16) -> (2, 64, 16, 16)

--- Parameters by block ---
  inc                   840
  ...
  total              94,441
The SE block is 512 parameters: 64 x 4 plus 4 x 64, no bias.

--- Training ---
epoch  1/60  loss 0.73844
epoch 10/60  loss 0.36042
...
epoch 60/60  loss 0.06897

Loss: first 0.73844, last 0.06897
Training IoU at p = 0.5: 0.9955
Held-out IoU at p = 0.5: 0.9973
```

## What it produces

| path | what it is |
| --- | --- |
| `output/se_unet.json` | parameters by block, the loss curve, both IoUs, the drift |

## Notes

- **This is the chapter's real training run, and it is on CPU.** Sixty full-batch steps over
  six 64 x 64 chips take about three seconds; the harness trains a second time with the same
  seed to prove the curve is reproducible to 1e-6, so the whole file takes about six seconds.
- No `DataLoader`, no workers, no shuffle, no CUDA: `torch.manual_seed(7)` before the model
  is built, `torch.set_num_threads(1)`, and one batch of six. The loss is a number, not a
  sample.
- The book's draft `ModifiedUNet` was a shape sketch — `max_pool2d(x1, 8)` into a 256 -> 512
  convolution, then interpolate back — which cannot be trained or checked. The solution keeps
  the two classes and completes the network, because "the bottleneck keeps its shape" is only
  a claim about a real bottleneck.
- The parameter table is arithmetic, not a reading: 3 -> 8 double convolution is 840, the two
  SE matrices over 64 channels with a reduction of 16 are 512, and the total is 94 441. The
  harness asserts all ten numbers.
- Needs `torch` (`pip install -r requirements-ml.txt`); without it the harness prints `skip`
  with the command and ends green.
