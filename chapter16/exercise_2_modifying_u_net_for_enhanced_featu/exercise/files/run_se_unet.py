"""Harness for exercise 2 — the SE block in the bottleneck, and a real training run.

What is graded is the modification, not the printed sentence: the block keeps the
bottleneck's shape, adds exactly the two matrices the paper describes, receives a
gradient, and leaves a U-Net that still fits six chips well enough to say so with an
IoU. The loss curve is reproducible to the last digit with the same seed.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

try:
    import torch
except ImportError:
    print("skip    exercise 2 (SE U-Net) — pip install -r requirements-ml.txt")
    print("__VERDICT__ 0 0 exercise 2 (SE U-Net)", file=sys.stderr)
    raise SystemExit(0)

from harness import Harness, load_listing  # noqa: E402

# Every parameter of the architecture the solution builds, block by block. The
# numbers are arithmetic on the layer sizes, not a reading of one run: a 3 -> 8
# double convolution is 840 weights, and the two SE matrices over 64 channels with a
# reduction of 16 are 64 x 4 + 4 x 64 = 512.
EXPECTED_PARAMETERS = {
    "inc": 840, "down1": 3552, "down2": 14016, "bottleneck_conv": 55680,
    "se_block": 512, "up2": 8224, "dec2": 9312, "up1": 520, "dec1": 1776, "outc": 9,
}


def main():
    h = Harness("exercise 2 (SE U-Net)", FILES)
    module = load_listing(FILES / "se_unet.py", "se_unet")
    measured = module.main()

    torch.manual_seed(module.SEED)
    torch.set_num_threads(1)
    model = module.ModifiedUNet()
    x, y = module.build_batch()

    # --- the forward pass ---
    with torch.no_grad():
        logits = model(x)
    h.equal(tuple(logits.shape), (6, 1, 64, 64),
            "six chips in, one logit map of 64 x 64 out")
    h.check(float(logits.min()) > -20.0 and float(logits.max()) < 20.0,
            "the untrained logits stay in a sane range (%.2f .. %.2f)"
            % (float(logits.min()), float(logits.max())))
    h.check(float(logits.max()) > float(logits.min()),
            "the output is not a constant: the kernels produce a field")

    # --- the SE block: shape, gate and arithmetic ---
    bottleneck = torch.zeros(2, 64, 16, 16)
    with torch.no_grad():
        recalibrated = model.se_block(bottleneck)
    h.equal(tuple(recalibrated.shape), (2, 64, 16, 16),
            "the SE block returns the bottleneck's shape unchanged")
    h.equal(model.bottleneck_conv.double_conv[0].out_channels, 64,
            "the bottleneck feeds 64 channels into the block")
    h.equal(model.se_block.fc[0].in_features, 64,
            "the block's first matrix reads those 64 channels")
    h.equal(model.se_block.fc[0].out_features, 4,
            "a reduction of 16 gives 64 / 16 = 4 hidden units")
    h.equal(model.dec2.double_conv[0].in_channels, 48,
            "the decoder concatenates 32 upsampled and 16 skip channels")

    # A zero feature map must produce a zero output: the block scales, never offsets.
    h.close(float(recalibrated.abs().sum()), 0.0,
            "scaling a zero bottleneck returns zeros")

    # The gate is a sigmoid: every weight is in (0, 1), and it is not a no-op at
    # initialisation, because a freshly initialised sigmoid sits near 0.5.
    gate = model.se_block.fc(
        model.se_block.avg_pool(torch.rand(1, 64, 16, 16)).view(1, 64))
    h.check(bool((gate > 0).all() and (gate < 1).all()),
            "every channel weight is a sigmoid output in (0, 1)")
    h.check(bool((gate < 0.9).all()), "the gate is not saturated at 1 on initialisation")

    # --- the block is in the gradient path ---
    model.zero_grad()
    loss = torch.nn.BCEWithLogitsLoss()(model(x), y)
    loss.backward()
    gate_grads = [p.grad for p in model.se_block.fc.parameters() if p.grad is not None]
    h.equal(len(gate_grads), 2, "both SE matrices receive a gradient")
    h.check(all(float(g.abs().sum()) > 0 for g in gate_grads),
            "neither SE matrix has a dead gradient")

    # --- the parameter count ---
    table = module.parameter_table(model)
    h.equal(table, EXPECTED_PARAMETERS, "every block matches its arithmetic parameter count")
    h.equal(table["se_block"], 512, "the SE block costs 512 parameters: 64x4 plus 4x64")
    h.equal(sum(table.values()), 94_441, "the modified U-Net has 94 441 parameters")

    # --- the training run ---
    history = measured["loss_history"]
    h.equal(len(history), module.EPOCHS, "the run records one loss per epoch")
    h.check(history[0] > 0.6, "the first loss starts where an untrained net starts (%.4f)"
            % history[0])
    h.check(history[-1] < 0.15, "the last loss is an order of magnitude lower (%.4f)"
            % history[-1])
    h.check(history[-1] < history[0] / 5.0, "the loss falls by at least a factor of five")
    h.check(history.index(min(history)) >= len(history) - 10,
            "the lowest loss is in the last ten epochs, so the run had converged")
    h.check(measured["train_iou"] > 0.9,
            "the trained net overlaps the synthetic masks (IoU %.3f)"
            % measured["train_iou"])
    h.check(measured["held_out_iou"] > 0.8,
            "it also segments two chips drawn from another seed (IoU %.3f)"
            % measured["held_out_iou"])

    # --- same seed, same curve ---
    torch.manual_seed(module.SEED)
    repeat = module.ModifiedUNet()
    repeat_history = module.train(repeat, x, y)
    drift = max(abs(a - b) for a, b in zip(history, repeat_history))
    h.check(drift < 1e-6, "a second run with the same seed reproduces the curve (%.2e)"
            % drift)

    h.write_json("se_unet.json", {
        "batch": {"input": list(measured["batch_shape"]),
                  "roof_pixels": measured["roof_pixels"]},
        "logits": {"shape": list(measured["logit_shape"]),
                   "min": round(measured["logit_min"], 3),
                   "max": round(measured["logit_max"], 3)},
        "parameters": table,
        "total_parameters": measured["total_parameters"],
        "se_parameters": measured["se_parameters"],
        "training": {"epochs": module.EPOCHS, "lr": module.LEARNING_RATE,
                     "loss_first": round(history[0], 5),
                     "loss_last": round(history[-1], 5),
                     "curve_every_10": [round(v, 5) for v in history[::10]]},
        "iou": {"train": round(measured["train_iou"], 4),
                "held_out": round(measured["held_out_iou"], 4)},
        "determinism_drift": drift,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (SE U-Net)", FILES).crash())
