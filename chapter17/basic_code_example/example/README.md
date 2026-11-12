# Example 1 — one point prompt, one mask

## What it does

Encodes a 256 x 256 patch, sends a single positive point at `(x=120, y=65)`, and gets back
three candidate masks with a score each. It picks the highest-scoring one, prints its area,
and checks that the prompted pixel is inside it. The segmenter is Meta's SAM when the
package and the weights are installed, and a small threshold stand-in otherwise.

## The listings

| file | what it is |
| --- | --- |
| `sam_point_prompt.py` | the example: patch, predictor, point prompt, mask selection |
| `run_sam_point_prompt.py` | the harness: shapes, scores, the (x, y) convention |

## Run it

```bash
cd chapter17/basic_code_example/example/files
python3 sam_point_prompt.py
```

It prints which segmenter it used, then the mask count, the three scores, the chosen index
and the segmented area. `run_sam_point_prompt.py` asserts that three masks come back at the
image's resolution with descending scores, that the wrong axis order selects nothing, and
that the mask is the 1 200-pixel building; it exits non-zero when the prompt handling or the
mask selection changes.

```text
Image: (256, 256, 3) uint8, one 30 x 40 building at rows 50-80, columns 100-140
[SAM] segment_anything is not installed; using the threshold stand-in for the segmenter.
Encoder: stand-in. Image (256x256) encoded once.

--- Prediction Results (stand-in) ---
Total masks generated: 3
Masks shape: (3, 256, 256), logits shape: (3, 64, 64)
Confidence scores: [0.96 0.88 0.71]
Selected mask index 0 with score 0.96
Area segmented (pixels): 1200
```

## What it produces

| path | what it is |
| --- | --- |
| `output/sam_point_prompt.json` | the segmenter used, the scores and the mask's area |

## Notes

- **The package and the weights are the boundary, and both are absent.** `segment_anything`
  is not on PyPI and the `vit_b` checkpoint is a 375 MB download, so nothing here fetches
  either. The listing imports the real API when it is present *and* the checkpoint file is
  on disk; otherwise it uses `ThresholdSamPredictor`, a 60-line stand-in that returns the
  connected bright region containing the prompted point. The comment above the class says
  so, and the run prints which one it used.
- What is being taught is the prompt protocol, and that is real in both modes: `(x, y)` not
  `(row, col)`, an `N x 2` array even for one point, labels of 1 and 0, three masks from
  `multimask_output`, and `np.argmax(scores)` to choose.
- The building is 30 rows by 40 columns on purpose. A square one would segment identically
  with the axes swapped, and the harness's swapped-prompt check would pass for the wrong
  reason.
- The stand-in's numbers are exact (1 200 pixels, rows 50-79, columns 100-139) and the
  harness asserts them only when the stand-in is in use, so the suite stays green on a
  machine that does have SAM.
- Runs in about 0.2 s; `scipy` is the only dependency beyond NumPy.
