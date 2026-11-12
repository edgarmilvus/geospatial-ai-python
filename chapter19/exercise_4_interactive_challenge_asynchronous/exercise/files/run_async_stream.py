"""Harness for chapter 19, exercise 4 — the loop, its order, and its teardown.

A failing pipeline still ends with the connection closed, and a working one shows
the health check ticking between two batches. Those are the two behaviours the
exercise is about, so they are what this file asserts, in the order they appear
in the log.
"""
import asyncio
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 4 (asynchronous stream)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_async_stream.py", "async_stream")
        batches, outcome = module.main()
    printed = log.getvalue()

    h.equal(module.BATCH_COUNT, 5, "the simulated feed carries five batches")
    h.equal(batches, 5, "every batch the stream produced was processed")

    # --- the order the reader needs to see ---
    connect = printed.index("Connected successfully.")
    first_batch = printed.index("Processing Batch_0")
    last_disconnect = printed.index("Disconnected.")
    last_batch = printed.index("Processing Batch_4")
    h.check(connect < first_batch,
            "the connection is established before the first batch is read")
    h.check(last_batch < last_disconnect,
            "the connection is released after the last batch")
    h.equal(printed.count("[Inference] Prediction complete"), 5,
            "inference ran once per batch")
    h.equal(printed.count("[Map Display] Finished rendering"), 5,
            "the map task rendered once per batch")

    # --- concurrency: the health check runs while the loop waits for data ---
    health_one = printed.index("[Health Check] System operational. Cycle 1.")
    health_three = printed.index("[Health Check] System operational. Cycle 3.")
    h.check(health_one < first_batch,
            "the first health check completes while the connection is being opened")
    h.check(height_between(health_three, printed, first_batch),
            "the third health check falls between the first batch and the last")
    h.equal(printed.count("[Health Check]"), 3, "the health check ran its three cycles")

    # --- the failing stream ---
    failing = printed[printed.index("Now with a stream that fails"):]
    h.contains(failing, "Exception encountered: sensor feed died mid-batch",
               "the context manager sees the exception as it unwinds")
    h.contains(failing, "Disconnected.", "the connection is released anyway")
    h.equal(failing.count("Disconnected."), 1,
            "teardown runs once, not once per failed batch")
    h.equal(outcome, "halted", "the failing run reports that it halted")
    h.check(failing.index("Disconnecting...") < failing.index("Pipeline halted"),
            "teardown happens before the error reaches the caller")

    # --- the artefact ---
    artefact = FILES.parent / "output" / "async_stream.txt"
    h.check(artefact.exists(), "the run wrote its small artefact")
    if artefact.exists():
        h.contains(artefact.read_text(), "batches processed: 5",
                   "the artefact records five batches")

    h.write_json("async_stream_exercise.json", {
        "batches": batches,
        "failing_outcome": outcome,
        "inference_calls": printed.count("[Inference] Processing"),
        "map_updates": printed.count("[Map Display] Finished rendering"),
        "health_checks": printed.count("[Health Check]"),
        "teardowns": printed.count("Disconnected."),
    })
    return h.report()


def height_between(needle_index, printed, first_batch):
    """True when the health-check line sits after the first batch line and before
    the last one — i.e. it ran while the stream was still open."""
    return first_batch < needle_index < printed.rindex("Processing Batch_4")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (asynchronous stream)", FILES).crash())
