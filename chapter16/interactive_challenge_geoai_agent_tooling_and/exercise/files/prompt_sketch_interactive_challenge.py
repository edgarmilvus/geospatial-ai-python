# Required structure for the Interactive Challenge.
# A sketch, not a program: the model and the insert function are the interface to fill in.
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker
import geopandas as gpd

# 1. Define the Base
Base = declarative_base()


class Building(Base):
    """SQLAlchemy Model mapping to a building detection table."""
    __tablename__ = 'detected_buildings'

    id = Column(Integer, primary_key=True)
    area_sqm = Column(Float)
    centroid_x = Column(Float)
    centroid_y = Column(Float)
    wkt_geometry = Column(String)  # Store geometry as WKT string

    # Define __repr__
    pass


def store_buildings_in_db(geodataframe: gpd.GeoDataFrame, session):
    """
    Tool function for a GeoAI Agent: Persists vectorized building data
    to the SQL database.
    """
    # 1. Iterate through the GeoDataFrame rows.
    # 2. Create Building objects, converting Shapely geometry to WKT.
    # 3. Add objects to the session and commit.
    pass
