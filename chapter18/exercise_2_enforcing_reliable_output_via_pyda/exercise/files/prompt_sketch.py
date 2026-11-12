# Pydantic Schema Definition
from pydantic import BaseModel, Field
from typing import Optional

class MapGenerationSummary(BaseModel):
    """
    Structured output schema for summarizing the generated map parameters.
    """
    column_mapped: str = Field(..., description="The exact column name used for coloring the map.")
    cmap_used: str = Field(..., description="The Matplotlib colormap string used (e.g., 'plasma').")
    # ... (Other fields defined here)
    pass 
