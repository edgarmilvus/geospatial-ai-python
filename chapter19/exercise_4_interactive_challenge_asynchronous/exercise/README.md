# Exercise 4 — the asynchronous stream

## What it does

Consumes a simulated live traffic feed with `async with` and `async for`, predicts on
each batch, and renders the result while the stream is idle. A second run uses a
feed that raises on its third batch, so the teardown path is demonstrated and not
just described.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_async_stream.py` | the skeleton the exercise hands the student: the stream and three empty functions |
| `01_async_stream.py` | the solution: the context manager, the loop, the concurrent tasks, the failing feed |
| `run_async_stream.py` | the harness: the order of the log, the batch count, the teardown on error |

## Run it

```bash
cd chapter19/exercise_4_interactive_challenge_asynchronous/exercise/files
python3 01_async_stream.py
```

It connects, processes five batches, prints the interleaved health checks that prove
the loop is not blocking, disconnects, then repeats the run against a feed that fails
so the connection is released anyway. `run_async_stream.py` asserts that order, that
inference and rendering ran once per batch, and exits non-zero if the failing feed
stops closing its connection.

```text
Starting GeoAI Deployment Simulation...
[Highway_101_Feed] Stream initialized.
[Highway_101_Feed] Attempting connection...
[Health Check] System operational. Cycle 1.
[Highway_101_Feed] Connected successfully.
    [Inference] Processing Batch_0...
...
[Highway_101_Feed] Disconnecting...
[Highway_101_Feed] Disconnected.
Deployment simulation finished.

--- Now with a stream that fails on its third batch ---
...
[Highway_101_Feed] Exception encountered: sensor feed died mid-batch
[Highway_101_Feed] Disconnected.
Pipeline halted: sensor feed died mid-batch
Outcome: halted
```

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/async_stream.txt` | the batch count and the outcome of the failing run |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/async_stream_exercise.json` | batch, inference, render, health-check and teardown counts |

## Notes

- The delays are milliseconds, not the seconds of the first draft: 0.5 s to connect
  and 0.2 s per batch made a test suite wait three seconds to prove a point that a
  log line proves.
- `asyncio.gather` returns the results in the order of its arguments, which is why
  the batch count can be read straight out of it.
- The failing feed subclasses the healthy one and raises inside `stream_data`. The
  exception is caught outside the `async with`, so `__aexit__` has already run by the
  time the caller sees it — that ordering is one of the assertions.
