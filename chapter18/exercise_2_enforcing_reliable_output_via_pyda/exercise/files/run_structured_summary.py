"""Harness for exercise 2 — a summary the pipeline can file.

The schema is only worth having if it rejects. The harness validates a complete
answer and a broken one, checks that the validator normalises the colormap name a
model usually embellishes, and checks that the optional field really is optional.
"""
import contextlib
import io
import json
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 2 (structured summary)", FILES)
    with contextlib.redirect_stdout(io.StringIO()):
        module = load_listing(FILES / "01_structured_summary.py", "structured_summary")

    model = module.MapGenerationSummary
    h.equal(list(model.model_fields),
            ["column_mapped", "cmap_used", "map_title", "classification_scheme"],
            "the schema carries the four fields the exercise asks for")
    h.check(model.model_fields["classification_scheme"].default is None,
            "the classification scheme is optional and defaults to null")

    summary, error = module.validate(json.dumps(module.GOOD))
    h.check(error is None, "a complete answer validates")
    h.equal(summary.column_mapped, "density", "the column survives validation")
    h.equal(summary.cmap_used, "viridis",
            "the validator strips 'the ... colormap' from the model's answer")

    _, error = module.validate(json.dumps(module.BAD))
    h.check(error is not None, "a blank column name is rejected")
    h.contains(str(error), "column_mapped", "the rejection names the field")

    # Missing the optional field must pass; missing a required one must not.
    optional_gone = {k: v for k, v in module.GOOD.items() if k != "classification_scheme"}
    filled, _ = module.validate(json.dumps(optional_gone))
    h.check(filled is not None and filled.classification_scheme is None,
            "an answer without the optional field is accepted")
    required_gone = {k: v for k, v in module.GOOD.items() if k != "map_title"}
    _, error = module.validate(json.dumps(required_gone))
    h.check(error is not None, "an answer without a required field is rejected")

    schema = model.model_json_schema()["properties"]
    h.contains(schema["cmap_used"]["description"], "colormap",
               "the JSON schema explains the field to the model")

    h.write_json("structured_summary.json", {
        "fields": list(model.model_fields),
        "accepted": summary.model_dump(),
        "rejected_reason": error.errors()[0]["msg"] if error else None,
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 2 (structured summary)", FILES).crash())
