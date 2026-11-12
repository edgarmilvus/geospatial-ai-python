# Chapter 18 — Text-to-Map - Building a LangChain Agent that Generates GeoPandas Code

The chapter's code, one folder per section. Every folder holds the listing exactly as it appears in the book, a harness that drives it and asserts what happened, and an `output/` folder for what the harness produced.

| folder | listing | what it shows |
| --- | --- | --- |
| `advanced_application_script_geopandas_text_to/example/` | `01_text_to_map_agent.py` | Builds the whole pipeline in four pieces: a five-municipality GeoDataFrame with a computed density column, the schema of that frame as text for the model, one tool that executes the code the model writes against the frame, and a ReAct loop that alternates between them until a map exists. |
| `basic_code_example/example/` | `01_tool_schema.py` | Wraps a centroid calculation in the two things a language model needs before it can call anything: a Pydantic model that names and describes the argument, and a `StructuredTool` that binds that model to the function. |
| `exercise_1_defining_the_core_geospatial_tool/exercise/` | `01_executor_tool.py` | Defines the one tool a Text-to-Map agent is allowed to call. |
| `exercise_2_enforcing_reliable_output_via_pyda/exercise/` | `01_structured_summary.py` | Defines the four fields an agent must report after it makes a map, then validates one complete answer and one broken answer. |
| `exercise_3_the_contextual_schema_challenge/exercise/` | `01_contextual_schema.py` | Extracts a frame's columns and types as text and injects them into a chat prompt with `.partial()`, so a question about *borough names* can be answered against a column called `BoroName`. |
| `exercise_4_execution_environment_and_safety_m/exercise/` | `01_execution_safety.py` | Catches what the generated code raises, keeps the last frames of the traceback, and returns them as an observation with a `FIX:` line naming the columns that do exist. |
| `exercise_5_interactive_challenge_tool_orchest/exercise/` | `01_tool_orchestration.py` | Gives the agent a data tool that answers with a number and a map tool that draws the frame, then asks a question that needs both in order: fetch Tokyo's air quality, then put that number on the map. |

## Run the chapter

```bash
source .venv/bin/activate
./chapter18/run_offline.sh
```

`run_offline.sh` runs the 7 harnesses and prints one line per harness;
the log is written to `chapter18/output/run_18.log`. Any harness that fails makes
the suite exit 1. No API key and no network are needed: every listing generates the
data it reads, and anything that would call a model is driven through the scripted
model in `tools/` or skipped with the command to install what is missing.
