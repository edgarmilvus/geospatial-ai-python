# Exercise 4 — an executor that turns failure into instruction

## What it does

Catches what the generated code raises, keeps the last frames of the traceback, and
returns them as an observation with a `FIX:` line naming the columns that do exist.
It counts consecutive failures and stops after three, so a loop cannot spend an
afternoon retrying the same typo.

## The listings

| file | what it is |
| --- | --- |
| `01_execution_safety.py` | the solution: the tool, the traceback summary, the failure counter |
| `run_execution_safety.py` | the harness: failure, recovery, and the give-up path |

## Run it

```bash
cd chapter18/exercise_4_execution_environment_and_safety_m/exercise/files
python3 01_execution_safety.py
```

It sends one misspelled column and then the corrected one, printing both
observations and the counter. `run_execution_safety.py` asserts that the failure
names the error type and the bad column, that the corrected call writes a map, that a
success resets the counter, and that three failures end the loop.

## What it produces

Written by the listing, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/exercise_4_recovery.png` | the map drawn after the recovery |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/execution_safety.json` | the first observation, recovery and give-up outcomes |

## Notes

- The traceback the tool returns is truncated to its last three lines: the frames
  the model wrote are the useful part, the library frames above them are not.
- No network and no key.
