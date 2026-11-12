"""Harness for exercise 4 — failure must come back as something the agent can use.

The graded behaviour is not "it catches exceptions". It is that the observation
names the failing column, that a recovery is possible on the next call, and that
the tool stops instead of looping for ever once it has failed enough times.
"""
import contextlib
import io
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 4 (execution safety)", FILES)
    with contextlib.redirect_stdout(io.StringIO()):
        module = load_listing(FILES / "01_execution_safety.py", "execution_safety")

    tool = module.robust_geo_pandas_executor
    h.contains(list(module.GDF.columns), "value", "the frame the model sees is ready")

    first = tool.invoke({"code_snippet": "gdf.plot(column='populaton', legend=True)"})
    h.contains(first, "OBSERVATION", "a failure is labelled as an observation")
    h.contains(first, "KeyError", "the observation names the error type")
    h.contains(first, "populaton", "the observation quotes the column that failed")
    h.contains(first, "FIX:", "the observation tells the model what to change")

    second = tool.invoke({"code_snippet": "gdf.plot(column='value', legend=True)"})
    h.contains(second, "Success", "the corrected call succeeds")
    produced = FILES.parent / "output" / "exercise_4_recovery.png"
    h.check(produced.exists(), "the recovered run wrote its map")
    h.equal(module.STATE["failures"], 0, "a success resets the failure counter")

    # Three failures in a row have to stop the loop rather than invite a fourth.
    for _ in range(module.MAX_FAILURES):
        last = tool.invoke({"code_snippet": "gdf.plot(column='still_wrong')"})
    h.contains(last, "Giving up", "the tool refuses to retry indefinitely")
    h.contains(last, "still_wrong", "the last error is still reported")

    summary = module.summarise_traceback(
        "Traceback (most recent call last):\n  File x\n  File y\nKeyError: 'a'\n")
    h.contains(summary, "KeyError", "the traceback summary keeps the failing line")
    h.check(len(summary.splitlines()) <= 3, "the summary is short enough to paste back")

    h.write_json("execution_safety.json", {
        "failure_observation": first.splitlines()[0],
        "recovered": "Success" in second,
        "gave_up": "Giving up" in last,
        "max_failures": module.MAX_FAILURES,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (execution safety)", FILES).crash())
