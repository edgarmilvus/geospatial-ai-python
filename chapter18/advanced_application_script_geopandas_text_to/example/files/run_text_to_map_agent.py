"""Harness for example 2 — the Text-to-Map loop, driven by a scripted model.

The listing cannot be graded by running it against a real endpoint: the suite is
offline and costs nothing. So the model — the only boundary in the pipeline — is
replaced by a scripted chat model that answers exactly what a working model would:
one Action that sends GeoPandas code to the tool, then a Final Answer. Everything
else is the book's code: the frame, the schema, the prompt, the tool, the executor.
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

GENERATED_CODE = (
    "GDF_CONTEXT.plot(column='density', cmap='viridis', legend=True, "
    "edgecolor='black')"
)

SCRIPT = [
    "Thought: I need to draw the density column with the viridis colormap.\n"
    "Action: execute_geopandas_code\n"
    f"Action Input: {GENERATED_CODE}",
    "Thought: The map was written, so the question is answered.\n"
    "Final Answer: A choropleth of population density across five municipalities, "
    "saved as a PNG with the viridis colormap and a visible legend.",
]


def main():
    # Assert the *code's* default, so the harness clears the three variables first:
    # a suite that reads them from the shell passes only on a machine that has never
    # exported a key.
    saved = {name: os.environ.pop(name, None)
             for name in ("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL",
                          "OPENAI_COMPATIBLE_MODEL")}
    h = Harness("example 2 (text-to-map agent)", FILES)
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        module = load_listing(FILES / "01_text_to_map_agent.py", "text_to_map_agent")

    # The frame, the schema and the prompt exist without a model.
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    frame = module.GDF_CONTEXT
    h.equal(len(frame), 5, "five municipalities in the frame")
    h.equal(frame.crs.to_epsg(), 4326, "the frame carries a CRS")
    h.check(frame.geometry.is_valid.all(), "every polygon is valid geometry")
    h.equal(list(frame["density"].round(2))[:2], [1000.0, 333.33],
            "density is population over area, computed before the agent starts")
    h.contains(module.SCHEMA_CONTEXT, "density", "the schema shown to the model names the column")
    h.contains(module.SCHEMA_CONTEXT, "municipality_id", "the schema lists every column")
    # The prompt must tell the model not to write the Observation itself: a model
    # that continues the transcript breaks the parser.
    h.contains(module.REACT_TEMPLATE, "Stop after the Action Input line",
               "the prompt forbids continuing past Action Input")
    h.check(module.build_llm() is None, "with no key exported, no client is built")

    # The loop, with the model replaced by the script.
    fake = FakeListChatModel(responses=list(SCRIPT))
    executor = module.build_executor(fake)
    with contextlib.redirect_stdout(log):
        result = executor.invoke({"input": module.USER_QUERY})
    answer = result["output"]
    printed = log.getvalue()

    h.contains(printed, "[AGENT ACTION] Executing GeoPandas code",
               "the agent reached the execution tool")
    h.contains(answer, "choropleth", "the agent answered with what it produced")

    produced = FILES.parent / "output" / "geo_agent_density_map.png"
    h.check(produced.exists(), "the tool wrote the map it reported")
    if produced.exists():
        h.check(produced.stat().st_size > 3_000,
                "the PNG has real content (%d bytes)" % produced.stat().st_size)
        header = produced.read_bytes()[:8]
        h.equal(header, b"\x89PNG\r\n\x1a\n", "the artefact is a PNG, not an empty file")

    # A failing snippet must come back as an observation, not an exception: that
    # is what makes the second turn possible.
    bad = module.execute_geopandas_code.invoke(
        {"code_string": "GDF_CONTEXT.plot(column='nope')"})
    h.contains(bad, "Execution Error", "a bad column returns an error observation")

    for name, value in saved.items():
        if value is not None:
            os.environ[name] = value

    h.write_json("text_to_map.json", {
        "municipalities": int(len(frame)),
        "columns": list(frame.columns),
        "density_first_two": [round(float(v), 2) for v in frame["density"][:2]],
        "map_bytes": produced.stat().st_size if produced.exists() else 0,
        "agent_answer": answer[:200],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("example 2 (text-to-map agent)", FILES).crash())
