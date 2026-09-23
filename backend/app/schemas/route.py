from typing import List, Literal, Tuple

from pydantic import BaseModel, Field


# ============================================================
# Request Models
# ============================================================

class RouteRequest(BaseModel):
    # Grid indices [row, col]
    start: Tuple[int, int] = Field(..., description="Start grid indices [row, col]")
    goal: Tuple[int, int] = Field(..., description="Goal grid indices [row, col]")
    
    # Selected route optimization mode
    mode: Literal["fastest", "balanced", "conservative"] = Field(
        "balanced", description="Selected route mode"
    )


# ============================================================
# Response Models (GeoJSON standard)
# ============================================================

class RouteProperties(BaseModel):
    mode: str
    distance_km: float
    raw_terrain_cost: float
    average_raw_terrain_cost: float
    optimization_cost: float
    average_optimization_cost: float


class GeoJSONGeometry(BaseModel):
    # GIS standard format
    type: Literal["LineString"] = "LineString"
    coordinates: List[Tuple[float, float]]


class GeoJSONFeature(BaseModel):
    # Feature container
    type: Literal["Feature"] = "Feature"
    properties: RouteProperties
    geometry: GeoJSONGeometry


class GeoJSONResponse(BaseModel):
    # Final feature collection response
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature]

