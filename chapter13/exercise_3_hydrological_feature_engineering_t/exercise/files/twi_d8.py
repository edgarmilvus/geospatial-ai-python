import numpy as np
import rasterio
from pathlib import Path
from rasterio.transform import from_origin

# --- Flow routing without richDEM ---
# The book derives the Topographic Wetness Index from richDEM's FlowDirection and
# FlowAccumulation. richDEM has no installable wheel on current Python, so D8 is
# written out here: every cell drains to the single lowest of its eight neighbours
# (divided by the distance to it, so a diagonal step is not preferred for being
# longer), and the accumulation is one pass from the highest cell down to the
# lowest. That is exactly the algorithm richDEM runs under method='D8'.

SIZE = 128
CELL_SIZE = 5.0
SEED = None                 # the scene is a plane: no random term, nothing to seed
MIN_TAN_BETA = 0.001        # floor on tan(beta), about 0.057 degrees
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
OUTPUT_FILE = OUTPUT_DIR / "twi.tif"

# Row offset, column offset, and the distance multiplier (diagonals are sqrt(2)).
NEIGHBOURS = (
    (-1, -1, np.sqrt(2.0)), (-1, 0, 1.0), (-1, 1, np.sqrt(2.0)),
    (0, -1, 1.0),                         (0, 1, 1.0),
    (1, -1, np.sqrt(2.0)),  (1, 0, 1.0),  (1, 1, np.sqrt(2.0)),
)


def synthetic_dem(size=SIZE, cell=CELL_SIZE, drop_per_metre=0.15):
    """A uniform hillslope falling to the east at 0.15 m per metre.

    A real DEM is not a plane, but a plane is what makes every number in this
    listing checkable by hand: every cell drains east, so the accumulation of
    column j is j + 1 cells, and the index of that column follows from it.
    """
    columns = (size - 1 - np.arange(size)) * cell * drop_per_metre
    return np.tile(columns, (size, 1)).astype(np.float64)


def d8_receivers(dem, cell):
    """Index of the cell each cell drains to, and the drop it drains over.

    A cell with no strictly lower neighbour is a sink and keeps receiver -1.
    """
    rows, cols = dem.shape
    padded_dem = np.pad(dem, 1, mode="edge")
    padded_idx = np.pad(np.arange(rows * cols).reshape(rows, cols), 1, mode="edge")

    receiver = np.full((rows, cols), -1, dtype=np.int64)
    best_gradient = np.zeros((rows, cols), dtype=np.float64)

    for di, dj, step in NEIGHBOURS:
        neighbour = padded_dem[1 + di:1 + di + rows, 1 + dj:1 + dj + cols]
        gradient = (dem - neighbour) / (step * cell)
        # Strictly greater: equal-height neighbours never drain into each other.
        better = gradient > best_gradient
        receiver[better] = padded_idx[1 + di:1 + di + rows, 1 + dj:1 + dj + cols][better]
        best_gradient[better] = gradient[better]

    return receiver, best_gradient


def d8_flow_accumulation(dem, cell):
    """Cells draining through each cell, including itself."""
    receiver, _ = d8_receivers(dem, cell)
    order = np.argsort(-dem.ravel(), kind="stable")   # highest cell first
    receiver_flat = receiver.ravel()
    accumulation = np.ones(dem.size, dtype=np.int64)
    for index in order:
        downstream = receiver_flat[index]
        if downstream >= 0:
            accumulation[downstream] += accumulation[index]
    return accumulation.reshape(dem.shape)


def slope_tangent(dem, cell):
    """tan(beta): the gradient magnitude, in metres per metre."""
    dz_dy, dz_dx = np.gradient(dem, cell)
    return np.hypot(dz_dx, dz_dy)


def specific_catchment_area(dem, cell):
    """As: flow accumulation per unit contour width, in metres."""
    return d8_flow_accumulation(dem, cell) * cell


def topographic_wetness_index(dem, cell, min_tan_beta=MIN_TAN_BETA):
    """TWI = ln(As / tan(beta)), with the slope floored on flat ground."""
    area = specific_catchment_area(dem, cell)
    tan_beta = np.maximum(slope_tangent(dem, cell), min_tan_beta)
    return np.log(area / tan_beta)


dem_data = synthetic_dem()
receiver, gradient = d8_receivers(dem_data, CELL_SIZE)
accumulation = d8_flow_accumulation(dem_data, CELL_SIZE)
twi_array = topographic_wetness_index(dem_data, CELL_SIZE)

print("--- D8 Flow Routing ---")
print(f"Grid: {dem_data.shape} at {CELL_SIZE} m")
print(f"Sinks (no lower neighbour): {int((receiver < 0).sum())}")
print(f"Largest accumulation: {int(accumulation.max())} cells")
print(f"Accumulation at the west edge (column 0): {int(accumulation[:, 0].max())} cells")
print(f"Accumulation at the east edge (column {dem_data.shape[1] - 1}): "
      f"{int(accumulation[:, -1].max())} cells")

print("\n--- TWI Calculation Results ---")
print(f"TWI Min: {twi_array.min():.2f}")
print(f"TWI Max: {twi_array.max():.2f}")
print(f"TWI Mean: {twi_array.mean():.2f}")
print(f"Slope of the hillslope: {np.degrees(np.arctan(0.15)):.2f}° "
      f"(tan beta = 0.15)")

# The index is a product like any other terrain layer.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
profile = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'nodata': -9999.0,
    'width': dem_data.shape[1],
    'height': dem_data.shape[0],
    'count': 1,
    'crs': 'EPSG:32610',
    'transform': from_origin(500000.0, 4500000.0, CELL_SIZE, CELL_SIZE),
}
with rasterio.open(OUTPUT_FILE, 'w', **profile) as dst:
    dst.write(twi_array.astype('float32'), 1)
print(f"\nWrote TWI to: {OUTPUT_FILE.relative_to(OUTPUT_DIR.parent)}")
