# Exercise 4 — an async GIS connection that always closes

## What it does

Wraps a remote GIS session in an asynchronous context manager: acquiring is an
`await`, releasing is an `await`, and the release happens on the failing path too.
The listing runs the task twice — once healthy, once with the query raising — and
prints what the manager's event log says in each case.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_async_gis.py` | the task statement: the async context manager and what it must guarantee |
| `01_async_gis_connection.py` | the solution: `__aenter__`, `__aexit__`, the task, two runs |
| `run_async_gis.py` | the harness: both paths, the exception contract, the delay |

## Run it

```bash
cd chapter20/exercise_4_interactive_challenge_implementing/exercise/files
python3 01_async_gis_connection.py
```

It prints the connection log for both runs and the handle after each block — `None`
in both cases. `run_async_gis.py` asserts that the event log is `connected` then
`released` on both paths, that `__aexit__` returns `False` so the caller still sees
the exception, and that the simulated connect delay is a real `await`; it exits
non-zero if a failure starts leaking a handle.

## What it produces

Written by the harness:

| path | what it is |
| --- | --- |
| `output/async_gis.json` | both event logs, the handle after failure, the delay |

## Notes

- `return False` in `__aexit__` is the whole contract: `True` would swallow the
  exception and the caller would believe the query succeeded.
- The delays are `asyncio.sleep`, not `time.sleep`, so the loop stays free — which
  is the property a synchronous `with` cannot offer.
