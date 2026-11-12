"""Harness for exercise 5 — the vectorized buildings as rows an agent can query.

The assertion that matters is the one an agent makes: "which building is largest?"
is answered by SQL against the table, not by scanning the GeoPackage. The geometry
is stored as WKT, so it must survive the round trip through text and parse back to
the same area.
"""
import pathlib
import sys

FILES = pathlib.Path(__file__).resolve().parent
ROOT = FILES.parents[3]
sys.path.insert(0, str(ROOT / "tools"))

from harness import Harness, load_listing  # noqa: E402


def main():
    h = Harness("exercise 5 (building database)", FILES)
    module = load_listing(FILES / "building_database.py", "building_database")
    measured = module.main()

    # --- three footprints, 200 + 450 + 1 200 m² ---
    h.equal(measured["areas"], [200.0, 450.0, 1200.0],
            "the three rectangles vectorize to 200, 450 and 1 200 m²")
    h.equal(measured["stored"], 3, "the tool returns the three rows it wrote")
    h.equal(measured["rows"], 3, "the table holds three rows")
    h.close(measured["area_sum"], 1850.0, "the table's areas sum to 1 850 m²")
    h.close(measured["largest_area"], 1200.0, "the largest building is the warehouse")
    h.equal(measured["largest_wkt_prefix"], "POLYGON",
            "the geometry is stored as a WKT POLYGON, not a blob")

    # --- the rows outlive the session ---
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(f"sqlite:///{module.DB_PATH}")
    session = sessionmaker(bind=engine)()
    h.check(module.DB_PATH.exists(), "the database file is written under output/")
    rechecked = session.query(func.count(module.Building.id)).scalar()
    h.equal(rechecked, 3, "a second connection sees the three committed rows")

    # --- the WKT parses back to the same shape ---
    from shapely import wkt
    rows = session.query(module.Building).order_by(module.Building.area_sqm).all()
    parsed = [wkt.loads(row.wkt_geometry).area for row in rows]
    h.check(all(abs(a - row.area_sqm) < 1e-6 for a, row in zip(parsed, rows)),
            "each stored WKT parses back to the area in its column")
    h.equal([round(value, 1) for value in parsed], [200.0, 450.0, 1200.0],
            "the WKT areas are 200, 450 and 1 200 m² in order")
    h.check(all("Building(id=" in repr(row) and "sqm" in repr(row) for row in rows),
            "the model's __repr__ names the id and the area")

    centroids_inside = all(
        abs(wkt.loads(row.wkt_geometry).centroid.x - row.centroid_x) < 1e-6
        for row in rows)
    h.check(centroids_inside, "the stored centroid is the polygon's own centroid")

    # --- the empty frame is a zero, not an exception ---
    h.equal(measured["empty_stored"], 0, "an empty frame stores nothing")
    still = session.query(func.count(module.Building.id)).scalar()
    h.equal(still, 3, "the empty call does not disturb the rows already committed")
    session.close()

    # --- the table is the one the exercise names ---
    h.equal(module.Building.__tablename__, "detected_buildings",
            "the model maps to the detected_buildings table")
    column_names = [column.name for column in module.Building.__table__.columns]
    h.equal(column_names, ["id", "area_sqm", "centroid_x", "centroid_y", "wkt_geometry"],
            "the five columns an agent queries are all present")

    h.write_json("building_database.json", {
        "table": module.Building.__tablename__,
        "columns": column_names,
        "rows": measured["rows"],
        "areas_sqm": measured["areas"],
        "area_sum_sqm": measured["area_sum"],
        "largest_area_sqm": measured["largest_area"],
        "geometry_storage": "WKT",
        "wkt_round_trip_areas": [round(value, 1) for value in parsed],
        "empty_frame_rows": measured["empty_stored"],
        "database": measured["db"],
        "crs": measured["crs"],
    })
    return h.report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(Harness("exercise 5 (building database)", FILES).crash())
