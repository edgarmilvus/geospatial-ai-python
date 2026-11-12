"""Harness for chapter 20, example 1 — the tool, its schema, and a scripted agent.

The model is the only part of the pipeline that cannot run offline, so it is
replaced by `FakeListChatModel` answering exactly what a working model would: one
JSON action that calls the distance tool, then a JSON final answer. Everything else
is the book's code — the Pydantic schema, the decorated tool, the prompt, the
executor — and that is what the assertions are about.
"""
import contextlib
import io
import os
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402

def main():
    # Assert the *code's* default, so the harness clears the three variables first:
    # a suite that reads them from the shell passes only on a machine that has never
    # exported a key.
    saved = {name: os.environ.pop(name, None)
             for name in ("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL",
                          "OPENAI_COMPATIBLE_MODEL")}
    h = Harness("example 1 (custom GeoAI tool)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_geo_distance_tool.py", "geo_distance_tool")
    printed = log.getvalue()

    tool = module.calculate_euclidean_distance

    # --- the contract the model reads ---
    schema = tool.args
    h.equal(sorted(schema), ["lat1", "lat2", "lon1", "lon2"],
            "the schema has the four coordinates as named fields")
    h.contains(schema["lat1"]["description"], "Latitude of the first point",
               "lat1 explains which point it belongs to")
    h.contains(schema["lon2"]["description"], "Longitude", "lon2 is labelled as a longitude")
    h.check(all(field.get("description") for field in schema.values()),
            "every field carries a description: none of them is a bare number")
    h.contains(tool.description, "straight-line",
               "the tool's own description names the metric it computes")
    h.contains(tool.description, "degrees",
               "the description states the unit, which is the pitfall of the section")

    # --- the arithmetic, which is the one number a model must not do by hand ---
    distance = tool.invoke({"lat1": 34.0, "lon1": -118.0, "lat2": 34.1, "lon2": -118.1})
    h.close(distance, 0.141421356237, tol=1e-9,
            message="the tool computes sqrt(0.1^2 + 0.1^2) without rounding")
    h.close(tool.invoke({"lat1": 34.0, "lon1": -118.0, "lat2": 34.0, "lon2": -118.0}),
            0.0, "a point is at distance zero from itself")

    # --- the three variables ---
    h.check(module.build_llm() is None, "with no key exported, no client is built")
    h.equal(module.BASE_URL_DEFAULT, "https://openrouter.ai/api/v1",
            "the endpoint has a default in the code")
    h.check("gpt" not in (module.SYSTEM_PROMPT or "").lower(),
            "no provider-specific model is named in the prompt")
    h.equal(module.MODEL_DEFAULT, "~deepseek/deepseek-flash-latest",
            "the model has a default in the code, and the reader can override it")

    # --- the loop, with the model replaced by the script ---
    # A tool-calling agent is driven by tool calls, not by text: the scripted model
    # returns the same structured call a real model would, then the final answer.
    sys.path.insert(0, str(ROOT / "tools"))
    from fake_tool_calling import ScriptedToolCallingModel

    fake = ScriptedToolCallingModel(
        [("calculate_euclidean_distance",
          {"lat1": 34.0, "lon1": -118.0, "lat2": 34.1, "lon2": -118.1})],
        final="The distance is about 0.1414 degrees: 0.1 in latitude and 0.1 in longitude.",
    )
    executor = module.build_executor(fake)
    with contextlib.redirect_stdout(log):
        result = executor.invoke({"input": module.QUERY_WITH_TOOL})
    answer = result["output"]
    trace = log.getvalue()

    h.contains(trace, "calculate_euclidean_distance",
               "the agent reached the distance tool")
    h.contains(trace, "0.141421356237",
               "the tool's exact result came back as the observation")
    h.contains(answer, "0.1414", "the agent answered with the number it was given")
    h.contains(trace, "> Finished chain", "the executor ran the loop to completion")

    for name, value in saved.items():
        if value is not None:
            os.environ[name] = value

    h.write_json("geo_distance_tool.json", {
        "tool": tool.name,
        "arguments": sorted(schema),
        "unit": "degrees",
        "distance_degrees": round(float(distance), 12),
        "agent_answer": answer[:160],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 1 (custom GeoAI tool)", FILES).crash())
