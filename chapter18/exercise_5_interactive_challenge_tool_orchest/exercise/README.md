# Exercise 5 — two tools, one planner

## What it does

Gives the agent a data tool that answers with a number and a map tool that draws the
frame, then asks a question that needs both in order: fetch Tokyo's air quality, then
put that number on the map. The planner is a ReAct loop over the two.

## The listings

| file | what it is |
| --- | --- |
| `01_tool_orchestration.py` | the solution: two tools, the prompt, the executor |
| `run_tool_orchestration.py` | the harness: a scripted model that uses both tools |

## Run it

```bash
cd chapter18/exercise_5_interactive_challenge_tool_orchest/exercise/files
python3 01_tool_orchestration.py
```

It prints both tools, calls each one on its own, and — when a key is exported — runs
the planner on the complex query. `run_tool_orchestration.py` drives the loop with a
scripted model that calls the data tool, then the map tool, then answers; it asserts
that both observations appeared and that the map exists, and exits non-zero if the
planner answers after using only one.

## What it produces

Written by the run, and checked by the harness:

| path | what it is |
| --- | --- |
| `output/exercise_5_orchestration.png` | the map the second tool drew |

Written by the harness:

| path | what it is |
| --- | --- |
| `output/tool_orchestration.json` | the tool names, the answer, whether both tools ran |

## Notes

- `initialize_agent` and `AgentType` are gone from current LangChain; the same
  orchestration is written with `create_react_agent` and an explicit tool list.
- The data tool returns a fixed number on purpose: the exercise grades the planner's
  choice of tool, not the availability of a weather service.
