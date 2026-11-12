import numpy as np

# Simulated 5x5 array data (example values)
# Values scaled 0-1000 for simplicity
red_band = np.array([
    [100, 150, 200, 120, 180],
    [110, 160, 210, 130, 190],
    [120, 170, 220, 140, 200],
    [130, 180, 230, 150, 210],
    [140, 190, 240, 160, 220]
], dtype=np.float32)

nir_band = np.array([
    [500, 600, 700, 550, 650],
    [510, 610, 710, 560, 660],
    [520, 620, 720, 570, 670],
    [530, 630, 730, 580, 680],
    [540, 640, 740, 590, 690]
], dtype=np.float32)
