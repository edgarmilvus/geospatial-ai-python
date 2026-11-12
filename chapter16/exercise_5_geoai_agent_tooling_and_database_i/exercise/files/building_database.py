import numpy as np
import rasterio
from pathlib import Path
from shapely.geometry import shape
from rasterio.features import shapes
from rasterio.transform import Affine
from sqlalchemy import Column, Float, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker

# --- Configuration ---
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
DB_PATH = OUTPUT_DIR / "buildings.db"
MASK_PATH = OUTPUT_DIR / "database_mask.tif"

ROWS, COLS, CELL = 110, 110, 1.0
TRANSFORM = Affine(CELL, 0.0, 400000.0, 0.0, -CELL, 4500000.0)
CRS = "EPSG:32617"

# (row_start, row_stop, col_start, col_stop): 200 m², 450 m² and a 1 200 m² warehouse.
# The rectangles do not even share a corner: connectivity=8 fuses anything that touches.
BUILDINGS = [(20, 30, 20, 40), (60, 75, 50, 80), (80, 110, 10, 50)]

# 1. Define the Base
Base = declarative_base()


# --- The Model ---
class Building(Base):
    """SQLAlchemy model mapping to a building detection table."""

    __tablename__ = 'detected_buildings'

    id = Column(Integer, primary_key=True)
    area_sqm = Column(Float, nullable=False)
    centroid_x = Column(Float)
    centroid_y = Column(Float)
    # WKT, not a geometry column: PostGIS can parse it, and so can SQLite without
    # an extension. A real deployment adds a spatial index on top.
    wkt_geometry = Column(String, nullable=False)

    def __repr__(self):
        return f"<Building(id={self.id}, area={self.area_sqm:.2f} sqm)>"


# --- The Vector Output the Previous Exercise Produces ---
def vectorize_mask(mask_path=MASK_PATH, buildings=BUILDINGS):
    """Write a mask, then turn it into a GeoDataFrame of buildings with attributes."""
    mask = np.zeros((ROWS, COLS), dtype=np.uint8)
    for row_start, row_stop, col_start, col_stop in buildings:
        mask[row_start:row_stop, col_start:col_stop] = 1

    MASK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(mask_path, "w", driver="GTiff", height=ROWS, width=COLS,
                       count=1, dtype="uint8", crs=CRS, transform=TRANSFORM,
                       nodata=0, compress="deflate") as dst:
        dst.write(mask, 1)

    rows = []
    with rasterio.open(mask_path) as src:
        for geometry, value in shapes(src.read(1), transform=src.transform,
                                      connectivity=8):
            if value != 1:
                continue
            polygon = shape(geometry)
            centroid = polygon.centroid
            rows.append({"geometry": polygon,
                         "area_sqm": round(polygon.area, 2),
                         "centroid_x": round(centroid.x, 2),
                         "centroid_y": round(centroid.y, 2)})

    # Imported here so the module reads top to bottom: the model above, the data here.
    import geopandas as gpd
    return gpd.GeoDataFrame(rows, crs=CRS)


# --- The Tool an Agent Calls ---
def store_buildings_in_db(geodataframe, session):
    """Persist the vectorized buildings and return how many rows were written.

    This is the shape an agent tool needs: one call, one integer, no session
    management leaking into the caller.
    """
    records = []
    for _, row in geodataframe.iterrows():
        records.append(Building(
            area_sqm=float(row["area_sqm"]),
            centroid_x=float(row["centroid_x"]),
            centroid_y=float(row["centroid_y"]),
            wkt_geometry=row.geometry.wkt,      # Shapely geometry -> text
        ))

    if not records:
        print("No records to store.")
        return 0

    session.add_all(records)
    session.commit()
    print(f"Successfully stored {len(records)} building records.")
    return len(records)


# --- Execution ---
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)          # a fresh database on every run

    gdf = vectorize_mask()
    print(f"{len(gdf)} polygons vectorized, {gdf['area_sqm'].sum():.0f} m² in total")

    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    stored = store_buildings_in_db(gdf, session)
    print(f"Rows written: {stored}")

    # The questions an agent asks of the table, not of the file.
    total = session.query(func.count(Building.id)).scalar()
    largest = session.query(Building).order_by(Building.area_sqm.desc()).first()
    area_sum = session.query(func.sum(Building.area_sqm)).scalar()
    print(f"\nRows in the table: {total}")
    print(f"Largest building: {largest}")
    print(f"Total footprint in the table: {area_sum:.0f} m²")
    print(f"WKT of the largest: {largest.wkt_geometry[:60]}...")

    # The empty case: the tool must answer zero, not raise.
    from geopandas import GeoDataFrame
    empty = GeoDataFrame({"area_sqm": [], "centroid_x": [], "centroid_y": []},
                         geometry=[], crs=CRS)
    empty_count = store_buildings_in_db(empty, session)
    print(f"Empty frame stored {empty_count} rows")
    session.close()

    return {
        "stored": stored,
        "rows": int(total),
        "largest_area": float(largest.area_sqm),
        "largest_wkt_prefix": largest.wkt_geometry[:7],
        "area_sum": float(area_sum),
        "areas": sorted(float(value) for value in gdf["area_sqm"]),
        "empty_stored": empty_count,
        "db": DB_PATH.name,
        "crs": gdf.crs.to_string(),
    }


if __name__ == "__main__":
    main()
