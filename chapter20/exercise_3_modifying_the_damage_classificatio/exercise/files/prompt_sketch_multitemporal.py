# Setup for Exercise 3: Agent Modification
import rasterio
from shapely.geometry import shape
from typing import Dict

class DamageClassificationAgent:
    
    def __init__(self, structural_loss_threshold: float = 0.20):
        self.structural_loss_threshold = structural_loss_threshold
        self.ndvi_change_threshold = 0.4

    def calculate_ndvi_proxy(self, raster_path: str, geometry: dict, 
                             nir_band_idx: int = 4, red_band_idx: int = 3) -> float:
        """
        Calculates the mean NDVI proxy within the geometry bounds using rasterio's context manager.
        """
        # Implementation must safely open the raster using 'with rasterio.open(raster_path) as src:'
        # and perform the spatial extraction and calculation.
        pass

    def calculate_structural_loss(self, pre_area: float, post_area: float) -> float:
        """Mock calculation for structural loss percentage."""
        # Assume this function is provided/mocked for testing the classification logic.
        return (pre_area - post_area) / pre_area if pre_area > 0 else 0.0

    def classify_damage(self, pre_raster_path: str, post_raster_path: str, 
                        building_footprint: Dict, pre_area: float, post_area: float) -> Dict:
        """
        Core classification logic incorporating both structural loss and spectral change.
        """
        # 1. Calculate structural loss.
        # 2. Calculate pre_ndvi and post_ndvi using the helper function.
        # 3. Calculate NDVI change magnitude.
        # 4. Apply the new classification rule (Major Damage heuristic).
        
        updated_feature = building_footprint.copy()
        # ... logic to determine damage_class and ndvi_change_magnitude ...
        
        return updated_feature

# The focus is on integrating the multi-temporal data sources securely and efficiently 
# within the agent's methods.
