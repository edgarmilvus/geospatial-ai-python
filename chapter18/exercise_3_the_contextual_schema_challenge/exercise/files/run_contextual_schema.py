"""Harness for exercise 3 — the schema reaches the prompt, and the answer is stored.

Two things can go wrong in this exercise and both are silent: the schema string is
built from a different frame than the one the agent gets, or the partial is applied
after the message is rendered, so the placeholder survives. The harness renders the
prompt and reads the columns out of it.
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
    h = Harness("exercise 3 (contextual schema)", FILES)
    # The listing guards its run behind `__main__`, so importing it writes
    # nothing: the harness has to make the call whose artefact it then checks.
    with contextlib.redirect_stdout(io.StringIO()):
        module = load_listing(FILES / "01_contextual_schema.py", "contextual_schema")
        module.main()

    frame = module.build_frame()
    h.equal(len(frame), 5, "the frame holds the five boroughs")
    h.contains(list(frame.columns), "BoroName",
               "the column whose name the model has to be told")

    schema_text = module.get_gdf_schema_string(frame)
    for column in frame.columns:
        h.contains(schema_text, column, "the schema names %s" % column)
    h.contains(schema_text, "Pop2020", "the density's source column is in the schema")

    prompt = module.build_prompt(frame)
    messages = prompt.format_messages(input="map the density")
    system = messages[0].content
    h.contains(system, "BoroName", "the rendered prompt carries the real column name")
    h.check("{gdf_schema}" not in system,
            "the placeholder was filled before the prompt was rendered")
    h.contains(messages[1].content, "map the density",
               "the question is the user message, not the system one")

    # The listing writes what it rendered: an artefact a reader can open.
    produced = FILES.parent / "output" / "rendered_prompt.txt"
    h.check(produced.exists(), "the listing saved the rendered prompt")
    if produced.exists():
        text = produced.read_text(encoding="utf-8")
        h.contains(text, "BoroName", "the saved prompt holds the schema")
        h.contains(text, "[system]", "the saved prompt keeps the message roles")

    h.write_json("contextual_schema.json", {
        "columns": list(frame.columns),
        "prompt_bytes": produced.stat().st_size if produced.exists() else 0,
        "placeholder_filled": "{gdf_schema}" not in system,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 3 (contextual schema)", FILES).crash())
