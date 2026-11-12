# Exercise 5 — the polygons as rows an agent can query

## What it does

Defines the SQLAlchemy model the exercise asks for — id, area, centroid, WKT geometry —
stores the vectorized buildings in SQLite as an agent tool, and answers the question the
tool exists for: which building is largest. The WKT is parsed back to check that the
geometry survived the trip through text.

## The listings

| file | what it is |
| --- | --- |
| `building_database.py` | the solution: mask, vectorize, model, tool, queries |
| `run_building_database.py` | the harness: rows, areas, WKT round trip, empty frame |

## Run it

```bash
cd chapter16/exercise_5_geoai_agent_tooling_and_database_i/exercise/files
python3 building_database.py
```

It vectorizes three footprints, writes `output/buildings.db`, and prints the row count, the
largest building, the total area and the tool's answer for an empty frame.
`run_building_database.py` asserts that 200 + 450 + 1 200 m² reach the table, that a second
connection sees them, and that each WKT parses back to its own area; it exits non-zero when a
geometry or an area changes on the way through text.

```text
3 polygons vectorized, 1850 m² in total
Successfully stored 3 building records.
Rows written: 3

Rows in the table: 3
Largest building: <Building(id=3, area=1200.00 sqm)>
Total footprint in the table: 1850 m²
WKT of the largest: POLYGON ((400010 4499920, 400010 4499890, 400050 4499890, 40...
No records to store.
Empty frame stored 0 rows
```

## What it produces

| path | what it is |
| --- | --- |
| `output/buildings.db` | the SQLite database, three rows in `detected_buildings` |
| `output/database_mask.tif` | the mask the three polygons came from |
| `output/building_database.json` | the columns, areas, WKT round trip and counts |

## Notes

- The draft imported `declarative_base` from `sqlalchemy.ext.declarative`, which is a
  deprecated path in SQLAlchemy 2.0; the listing uses `sqlalchemy.orm`. It also imported
  `create_engine` and never created an engine, and left the call to the tool commented out —
  so the model was never actually asked to store anything.
- The database is a file, not `:memory:`, and it is deleted at the start of every run: a
  table that cannot be re-opened by a second connection has not been tested.
- The three rectangles do not even share a corner. `connectivity=8` fuses anything that
  touches, and two of the draft rectangles produced one 1 650 m² polygon where three were
  meant.
- An empty frame returns 0 and leaves the committed rows alone; an agent tool that raises on
  "nothing found" is a tool the agent learns to avoid.
- No torch, no network, under half a second.
