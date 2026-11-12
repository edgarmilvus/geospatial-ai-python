"""Harness for exercise 5 — two tools, and a planner that has to use both.

The interesting failure of a two-tool agent is not a crash: it is a fluent answer
that skipped one of the tools. The harness drives the same loop with a scripted
model that calls the data tool, then the map tool, then answers — and asserts that
both observations were produced and that the map exists.
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

SCRIPT = [
    "Thought: I need the air quality value first.\n"
    "Action: external_data_fetcher\n"
    "Action Input: Air Quality Tokyo",
    "Thought: Now I can draw the map with that number in the title.\n"
    "Action: geo_pandas_executor\n"
    "Action Input: gdf.plot(column='value', legend=True); plt.title('Air quality 42.5')",
    "Thought: Both pieces are in place.\n"
    "Final Answer: Tokyo's air quality is 42.5 units, and the map of the two cities "
    "was drawn with that figure in its title.",
]


def main():
    # Assert the *code's* default, so the harness clears the three variables first:
    # a suite that reads them from the shell passes only on a machine that has never
    # exported a key.
    saved = {name: os.environ.pop(name, None)
             for name in ("OPENAI_COMPATIBLE_API_KEY", "OPENAI_COMPATIBLE_BASE_URL",
                          "OPENAI_COMPATIBLE_MODEL")}
    h = Harness("exercise 5 (tool orchestration)", FILES)
    with contextlib.redirect_stdout(io.StringIO()):
        module = load_listing(FILES / "01_tool_orchestration.py", "tool_orchestration")

    h.equal([tool.name for tool in module.TOOLS],
            ["external_data_fetcher", "geo_pandas_executor"],
            "the planner chooses between exactly two tools")
    h.check(module.build_llm() is None, "with no key exported, no client is built")
    h.contains(module.REACT_TEMPLATE, "Stop after Action Input",
               "the prompt forbids the model writing its own Observation")

    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    log = io.StringIO()
    executor = module.build_executor(FakeListChatModel(responses=list(SCRIPT)))
    with contextlib.redirect_stdout(log):
        result = executor.invoke({"input": module.COMPLEX_QUERY})
    printed = log.getvalue()
    answer = result["output"]

    h.contains(printed, "42.5 units", "the data tool's answer reached the transcript")
    h.contains(printed, "Map generated", "the map tool ran after the data tool")
    h.contains(answer, "42.5", "the final answer carries the number it fetched")

    produced = FILES.parent / "output" / "exercise_5_orchestration.png"
    h.check(produced.exists(), "the second tool wrote the map")
    if produced.exists():
        h.check(produced.stat().st_size > 2_000,
                "the map is not an empty figure (%d bytes)" % produced.stat().st_size)

    # A single tool in isolation must still behave, so the loop's success is not
    # hiding a tool that only works when the other ran first.
    alone = module.geo_pandas_executor.invoke(
        {"code_snippet": "gdf.plot(column='value')"})
    h.contains(alone, "Map generated", "the map tool works on its own")

    for name, value in saved.items():
        if value is not None:
            os.environ[name] = value

    h.write_json("tool_orchestration.json", {
        "tools": [tool.name for tool in module.TOOLS],
        "answer": answer[:200],
        "map_bytes": produced.stat().st_size if produced.exists() else 0,
        "both_tools_used": "42.5 units" in printed and "Map generated" in printed,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (tool orchestration)", FILES).crash())
