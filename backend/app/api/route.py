from unittest import result

from fastapi import APIRouter, HTTPException, status

from app.schemas.route import RouteRequest, GeoJSONResponse
from app.core.terrain.geotiff import load_terrain, grid_to_map

# Adjust import path if route_service is located in app.core.route_service
from app.services.route_service import calculate_route


router = APIRouter()

# ============================================================
# Navigation Endpoint
# ============================================================

@router.post(
    "/navigate",
    response_model=GeoJSONResponse,
    status_code=status.HTTP_200_OK,
)
def navigate(request: RouteRequest):
    """
    Calculates the optimal route and returns a GeoJSON response.
    """
    
    terrain = load_terrain()
    

    terrain_cost = terrain["terrain_cost"]
    blocked_mask = terrain["blocked_mask"]
    resolution = terrain["resolution"]
    transform = terrain["transform"]

    rows, cols = terrain_cost.shape
    start_row, start_col = request.start
    goal_row, goal_col = request.goal

    # Validate start bounds
    if not (0 <= start_row < rows and 0 <= start_col < cols):
        raise HTTPException(
            status_code=400, 
            detail="Start coordinates out of bounds."
        )

    # Validate goal bounds
    if not (0 <= goal_row < rows and 0 <= goal_col < cols):
        raise HTTPException(
            status_code=400, 
            detail="Goal coordinates out of bounds."
        )

    # Execute route calculation
    result = calculate_route(
        terrain_cost=terrain_cost,
        blocked_mask=blocked_mask,
        start=request.start,
        goal=request.goal,
        resolution=resolution,
        mode_name=request.mode,
    )

    # Handle unreachable goal
    if result is None:
        raise HTTPException(
            status_code=404, 
            detail="No valid route found."
        )

    # Convert grid coordinates (row, col)
# to projected Mars map coordinates using the GeoTIFF transform
    gis_path = [
        grid_to_map(row, col, transform)
        for row, col in result["path"]
]
 
    # Construct GeoJSON properties
    geojson_feature = {
        "type": "Feature",
        "properties": {
            "mode": result["mode"],
            "distance_km": round(result["distance_km"], 3),
            "raw_terrain_cost": round(result["raw_terrain_cost"], 2),
            "average_raw_terrain_cost": round(result["average_raw_terrain_cost"], 4),
            "optimization_cost": round(result["optimization_cost"], 2),
            "average_optimization_cost": round(result["average_optimization_cost"], 4),
        },
        "geometry": {
            "type": "LineString",
            "coordinates": gis_path,
        },
    }

    # Return valid GeoJSON response
    return {
        "type": "FeatureCollection", 
        "features": [geojson_feature]
    }

