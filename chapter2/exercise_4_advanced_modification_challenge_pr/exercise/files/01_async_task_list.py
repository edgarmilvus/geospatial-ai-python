"""Chapter 2, exercise 4 — define the reads now, execute them later.

The task: turn the sequential reader into a queue of tasks. functools.partial
binds a function to its argument without calling it, so the list holds work that
is ready, not results that already cost I/O time.

The listing writes four one-degree GeoJSON tiles under output/tiles/ and then
builds the queue over those real paths, so it is self-contained and the task
objects have something true to point at.
"""
import pathlib
from functools import partial

import geopandas as gpd
from shapely.geometry import Polygon

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "output"
TILE_DIR = OUTPUT_DIR / "tiles"
TILE_DIR.mkdir(parents=True, exist_ok=True)


def write_tile(path, index):
    """One satellite tile footprint: a one-degree square, seeded by its index."""
    corner = (float(index * 2), float(index))
    tile = gpd.GeoDataFrame(
        {'tile_id': [index], 'source': ['imagery']},
        geometry=[Polygon([
            corner,
            (corner[0] + 1.0, corner[1]),
            (corner[0] + 1.0, corner[1] + 1.0),
            (corner[0], corner[1] + 1.0),
        ])],
        crs='EPSG:4326',
    )
    tile.to_file(path, driver='GeoJSON')


# 1. Define Input
# Four tiles that exist on disk before the queue is built.
file_paths = []
for number in range(1, 5):
    path = TILE_DIR / f"tile_{number:02d}.geojson"
    write_tile(path, number)
    file_paths.append(path)
print("1. Tiles on disk:")
for path in file_paths:
    print(f"   {path.name}")


# 2. Define the Task Function
def load_single_tile(path):
    """
    Conceptual function representing the I/O operation.
    In a real async pipeline, this might be wrapped in run_in_executor.
    """
    # Here the work is the real read; the point of the exercise is *when* it runs.
    return gpd.read_file(path)


# 3. Generate Awaitables (Conceptual Tasks)
# We use functools.partial to create callable objects (tasks)
# that are pre-bound with their arguments, ready for deferred execution.
# This structure is conceptually similar to creating Futures/Awaitables.
async_tasks = [partial(load_single_tile, path) for path in file_paths]

# 4. Verification
print("\nType of generated task list:", type(async_tasks))
print("\nContents of async_tasks (Conceptual Awaitables):")
# Displaying the first task to show it's a partial object, not a result.
# The argument is printed by name only, so the output does not depend on where
# the tree lives.
first = async_tasks[0]
print(f"   functools.partial({first.func.__name__}, "
      f"{first.args[0].name!r}), no arguments free")
print(f"   tasks defined: {len(async_tasks)}")
print("   tasks executed so far: 0 — partial() binds, it does not call")

print("\nExecuting the queue (what the event loop would do):")
for task in async_tasks:
    tile_gdf = task()
    print(f"   {task.args[0].name} -> {len(tile_gdf)} feature(s), "
          f"CRS {tile_gdf.crs.to_string()}, source {tile_gdf['source'].iloc[0]}")
print("   all four tasks executed: 4")
