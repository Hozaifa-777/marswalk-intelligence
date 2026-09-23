from pathlib import Path

import numpy as np
import rasterio

from app.core.routing.cost_function import slope_cost
from app.core.terrain.hazard import create_blocked_mask

PROJECT_ROOT = Path(__file__).resolve().parents[4]

DEM_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "terrain"
    / "jezero_aoi_ctx_dem_20m.tif"
)

MAX_WALKABLE_SLOPE = 20.0


def load_terrain():
    with rasterio.open(DEM_PATH) as src:
        dem = src.read(1)
        resolution = src.res[0]
        nodata = src.nodata
        transform = src.transform

    valid_mask = np.isfinite(dem)

    if nodata is not None:
        valid_mask &= dem != nodata

    dem = dem.astype(float)
    dem[~valid_mask] = np.nan

    dy, dx = np.gradient(
        dem,
        resolution,
        resolution,
    )

    slope_radians = np.arctan(
        np.hypot(dx, dy)
    )

    slope_degrees = np.degrees(slope_radians)

    valid_slopes = slope_degrees[np.isfinite(slope_degrees)]

    reference_slope = float(
        np.percentile(valid_slopes, 95)
    )

    terrain_cost = slope_cost(
        slope_degrees,
        reference_slope,
    )

    blocked_mask = create_blocked_mask(
        slope_degrees,
        MAX_WALKABLE_SLOPE,
    )

    blocked_mask |= ~valid_mask

    terrain_cost[~valid_mask] = np.inf

    return {
        "dem": dem,
        "slope": slope_degrees,
        "terrain_cost": terrain_cost,
        "blocked_mask": blocked_mask,
        "resolution": resolution,
        "reference_slope": reference_slope,
        "transform": transform,
    }

def grid_to_map(row, col, transform):
    x, y = rasterio.transform.xy(
        transform,
        row,
        col,
        offset="center"
    )

    return float(x), float(y)

