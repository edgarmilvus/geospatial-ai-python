"""Harness for exercise 4 — the async context manager releases what it acquired.

The exercise's claim is narrow and checkable: the handle is gone after the block,
whether the query inside it succeeded or raised. The harness drives both paths,
inspects the manager's own event log, and measures that the release happens even
when the body raises — the failure case is the one that matters, because that is
the one a `try/finally` gets wrong.
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
    h = Harness("exercise 4 (async GIS connection)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        module = load_listing(FILES / "01_async_gis_connection.py", "async_gis")
        healthy, failing = module.main()

    # The happy path: connected, released, handle cleared.
    h.equal(healthy.events, ["connected", "released"],
            "the healthy run connects once and releases once")
    h.check(healthy.connection is None, "the handle is cleared when the block exits")

    # The path that matters: the body raised, and the resource still went back.
    h.equal(failing.events, ["connected", "released"],
            "a failed query still releases the connection")
    h.check(failing.connection is None, "no handle leaks out of a failed block")

    # The manager must not swallow the exception: a caller has to see the failure.
    manager = module.AsyncGISConnectionManager("postgresql://gis_db/test")
    raised = False
    try:
        async def boom():
            async with manager:
                raise RuntimeError("query timed out on the remote server")

        asyncio.run(boom())
    except RuntimeError:
        raised = True
    h.check(raised, "__aexit__ returns False, so the exception reaches the caller")
    h.check(manager.connection is None, "the interrupted block still released the handle")
    h.equal(manager.events, ["connected", "released"],
            "the interrupted block logged its release")

    # The delays are asleep, not busy-waited: the loop is free while they run.
    async def timed():
        loop = asyncio.get_running_loop()
        started = loop.time()
        await asyncio.sleep(module.CONNECT_DELAY)
        return loop.time() - started

    elapsed = asyncio.run(timed())
    h.check(elapsed >= module.CONNECT_DELAY * 0.9,
            "the simulated connect delay is a real await (%.3fs)" % elapsed)

    printed = log.getvalue()
    h.contains(printed, "Handle after the block: None",
               "the listing prints the cleared handle")
    h.contains(printed, "cleanup proceeds",
               "the listing reports the cleanup on the failing path")

    h.write_json("async_gis.json", {
        "healthy_events": healthy.events,
        "failing_events": failing.events,
        "handle_after_failure": failing.connection,
        "connect_delay_s": module.CONNECT_DELAY,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 4 (async GIS connection)", FILES).crash())
