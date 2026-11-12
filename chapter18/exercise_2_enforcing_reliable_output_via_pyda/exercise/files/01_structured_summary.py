"""Chapter 18, exercise 2 — forcing the agent's summary into a schema.

A ReAct agent ends with prose. A pipeline that has to file that prose in a
database cannot use prose, so the final answer is constrained to a Pydantic model:
the chapter's four fields, one of them optional. The listing defines the schema
and validates both a complete answer and a broken one, which is the whole point —
`model_validate_json` is what turns "the model promised" into "the parser checked".

Chapters 18 and 20 use the same technique and the same environment variables; no
model is called here, so the contract can be read and tested without a key.
"""

import json

from pydantic import BaseModel, Field, ValidationError, field_validator


class MapGenerationSummary(BaseModel):
    """What the agent must report after it produces a map."""

    column_mapped: str = Field(description="The column used for colour, exactly as it appears in the frame")
    cmap_used: str = Field(description="The Matplotlib colormap name, e.g. 'viridis'")
    map_title: str = Field(description="The title written on the map")
    classification_scheme: str | None = Field(
        default=None,
        description="'quantiles', 'equal_interval', ... when the map classifies, else null")

    @field_validator("column_mapped")
    @classmethod
    def column_is_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("column_mapped cannot be empty: name the column you plotted")
        return value.strip()

    @field_validator("cmap_used")
    @classmethod
    def cmap_is_a_name(cls, value: str) -> str:
        # A model likes to answer "viridis colormap" or "the viridis one".
        cleaned = value.strip().lower().replace(" colormap", "").replace("the ", "")
        return cleaned


# A well-formed answer, the shape the agent is asked to produce.
GOOD = {
    "column_mapped": "density",
    "cmap_used": "the viridis colormap",
    "map_title": "Municipal population density",
    "classification_scheme": "quantiles",
}

# The same answer with the one field that must never be blank left blank.
BAD = dict(GOOD, column_mapped="   ")


def validate(payload: str):
    """Parse and validate a model answer; return the object or the reason it failed."""
    try:
        return MapGenerationSummary.model_validate_json(payload), None
    except ValidationError as exc:
        return None, exc


def main():
    summary, error = validate(json.dumps(GOOD))
    print("--- Accepted answer ---")
    print(f"fields: {list(MapGenerationSummary.model_fields)}")
    print(f"column_mapped: {summary.column_mapped}")
    print(f"cmap_used: {summary.cmap_used}   (normalised by the validator)")
    print(f"classification_scheme: {summary.classification_scheme}")

    _, error = validate(json.dumps(BAD))
    print("\n--- Rejected answer ---")
    print(f"raised: {type(error).__name__}")
    print(f"reason: {error.errors()[0]['msg']}")

    print("\n--- JSON schema the model is shown ---")
    print(json.dumps(MapGenerationSummary.model_json_schema()["properties"],
                     indent=2)[:400])
    return summary


if __name__ == "__main__":
    main()
