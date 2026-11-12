# Interactive Challenge — the prompt, and where its solution lives

## What it does

Holds the code block the book prints as the challenge's starting point: a `Building` model
with five columns, and an empty `store_buildings_in_db(geodataframe, session)` meant to be
the tool a GeoAI agent calls.

## The listings

| file | what it is |
| --- | --- |
| `prompt_sketch_interactive_challenge.py` | the prompt sketch, exactly as the challenge prints it — not a program |
| `../exercise_5_geoai_agent_tooling_and_database_i/exercise/files/building_database.py` | the worked solution, one folder over |

## Run it

```bash
cd chapter16/exercise_5_geoai_agent_tooling_and_database_i/exercise/files
python3 building_database.py
```

The sketch beside this README defines a model and a signature, so there is nothing to run:
the runnable version, its harness and the measured numbers live in the sibling
`exercise_5_geoai_agent_tooling_and_database_i/` project. That harness asserts 16 facts about
the table, the WKT round trip and the empty frame, and exits non-zero if a row or an area
changes.

```text
3 polygons vectorized, 1850 m² in total
Rows in the table: 3
Largest building: <Building(id=3, area=1200.00 sqm)>
```

## What it produces

Nothing. It is a prompt: the output belongs to the solution folder.

## Notes

- The sketch keeps the book's import of `declarative_base` but points it at
  `sqlalchemy.orm`, the supported path in SQLAlchemy 2.0. The deprecated
  `sqlalchemy.ext.declarative` alias still imports here, and a student on 2.1 would not.
- This folder has no harness and no `output/`; `run_building_database.py` in the sibling is
  the grader.
