"""Harness for chapter 19, exercise 2 — the block's shape arithmetic and its basis.

The exercise is graded on four domain facts: the Chebyshev recurrence really
starts at the identity, the scaled Laplacian has a spectrum inside [-1, 1], two
valid convolutions of kernel 3 shorten twelve steps to eight, and the parameter
count follows from the four layers. A backward pass proves the residual path is
not decorative.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 2 (ST-Conv block)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_stconv_block.py", "stconv_block")
    printed = log.getvalue()

    import numpy as np
    import torch

    # --- the scaled Laplacian and its Chebyshev basis ---
    lt = module.L_tilde
    h.equal(tuple(lt.shape), (50, 50), "the operator is one row per road link")
    h.check(bool(torch.allclose(lt, lt.T, atol=1e-6)),
            "the scaled Laplacian is symmetric")
    eigenvalues = np.linalg.eigvalsh(lt.numpy())
    h.check(float(eigenvalues.min()) >= -1.0 - 1e-6,
            "the spectrum is scaled into [-1, 1]: min is above -1")
    h.check(float(eigenvalues.max()) <= 1.0 + 1e-6,
            "the spectrum is scaled into [-1, 1]: max is below 1")

    identity = torch.eye(50)
    basis = module.chebyshev_polynomials(lt, 3)
    h.equal(tuple(basis.shape), (3, 50, 50), "K=3 gives three N x N terms")
    h.check(bool(torch.allclose(basis[0], identity)), "T_0 is the identity")
    h.check(bool(torch.allclose(basis[1], lt)), "T_1 is the scaled Laplacian")
    h.check(bool(torch.allclose(basis[2], 2 * lt @ lt - identity, atol=1e-6)),
            "T_2 follows the recurrence 2 L T_1 - T_0")

    # --- the block ---
    out = module.H_output
    h.equal(tuple(out.shape), (4, 8, 50, 64),
            "twelve steps in, eight steps out, fifty nodes, sixty-four features")
    h.equal(int(out.shape[1]), module.T_IN - 2 * (module.KERNEL - 1),
            "T_out = T_in - 2*(Kt-1)")
    h.check(bool(torch.isfinite(out).all()), "every value in the block output is finite")

    conv_weight = module.st_conv.tconv1.conv.weight
    h.equal(int(conv_weight.shape[0]), 2 * module.F_OUT,
            "the temporal convolution emits twice F_out so the GLU can gate it")
    h.equal(tuple(module.st_conv.sconv.theta.shape), (3, 64, 64),
            "the spatial layer holds one 64x64 weight matrix per Chebyshev term")

    parameters = sum(p.numel() for p in module.st_conv.parameters())
    h.equal(parameters, 90_624, "the block holds 90 624 parameters")
    h.equal(sum(p.numel() for p in module.st_conv.tconv1.parameters()), 2_048,
            "the input convolution is 5x128x3 weights plus 128 biases")
    h.equal(sum(p.numel() for p in module.st_conv.sconv.parameters()), 12_288,
            "three Chebyshev terms of 64x64 weights")

    # --- the residual path ---
    h.check(module.X_batch.grad is not None, "the backward pass reached the input")
    h.check(float(module.X_batch.grad.norm()) > 0, "the input gradient is not zero")
    h.check(bool(torch.isfinite(module.X_batch.grad).all()),
            "the input gradient is finite: no explosion through the recursion")

    # --- determinism ---
    torch.manual_seed(module.SEED)
    fresh = module.STConvBlock(order=module.ORDER, kernel_size=module.KERNEL,
                               in_channels=module.F_IN, out_channels=module.F_OUT,
                               nodes=module.N_NODES, time_steps=module.T_IN)
    with torch.no_grad():
        again = fresh(module.X_batch.detach(), lt)
    h.check(bool(torch.isfinite(again).all()),
            "a freshly seeded block runs on the same input")

    # --- what the reader sees ---
    h.contains(printed, "Output H shape (B, T_out, N, F_out): (4, 8, 50, 64)",
               "the run prints the output shape")
    h.contains(printed, "Trainable parameters: 90624", "the run prints the parameter count")
    h.contains(printed, "T_out = T_in - 2*(Kt-1) = 12 - 4 = 8",
               "the run shows the time-axis arithmetic")

    artefact = json.loads((FILES.parent / "output" / "stconv_block.json").read_text())
    h.equal(artefact["output_shape"], [4, 8, 50, 64], "the artefact records the shape")
    h.equal(artefact["parameter_count"], 90624, "the artefact records the parameter count")
    h.check(artefact["input_gradient_norm"] > 0, "the artefact records a live gradient")

    h.write_json("stconv_block_exercise.json", {
        "output_shape": list(out.shape),
        "t_out": int(out.shape[1]),
        "parameter_count": parameters,
        "spectrum": [round(float(eigenvalues.min()), 6),
                     round(float(eigenvalues.max()), 6)],
        "input_gradient_norm": round(float(module.X_batch.grad.norm()), 6),
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (ST-Conv block)", FILES).crash())
