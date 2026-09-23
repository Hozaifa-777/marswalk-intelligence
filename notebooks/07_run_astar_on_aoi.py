import matplotlib

matplotlib.use("Agg")

import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio

# Allow importing from backend/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.routing.astar import astar
from app.core.routing.route_modes import get_route_mode
from app.core.routing.cost_function import weighted_terrain_cost, slope_cost

# ============================================================
# Paths
# ============================================================

DEM_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "terrain"
    / "jezero_aoi_ctx_dem_20m.tif"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "sample"
    / "jezero_aoi_astar_route.png"
)


# ============================================================
# Load DEM
# ============================================================

with rasterio.open(DEM_PATH) as src:

    dem = src.read(1).astype(np.float64)

    transform = src.transform
    resolution = src.res[0]
    nodata = src.nodata

    bounds = src.bounds

    print("DEM loaded successfully")
    print("Grid size:", dem.shape)
    print("Resolution:", resolution)
    print("Bounds:", bounds)
    print("NoData:", nodata)


# ============================================================
# Create valid mask
# ============================================================

valid_mask = dem != nodata

dem_clean = dem.copy()
dem_clean[~valid_mask] = np.nan


# ============================================================
# Calculate slope
# ============================================================

dy, dx = np.gradient(
    dem_clean,
    resolution,
    resolution,
)

slope_radians = np.arctan(
    np.hypot(dx, dy)
)

slope_degrees = np.degrees(
    slope_radians
)

slope_degrees[~valid_mask] = np.nan


# ============================================================
# Create terrain cost
# ============================================================

from app.core.terrain.hazard import (
    create_blocked_mask,
    apply_blocked_mask,
)

reference_slope = np.nanpercentile(
    slope_degrees,
    95,
)

terrain_cost = slope_cost(
    slope_degrees,
    reference_slope,
)

terrain_cost[~valid_mask] = np.inf

# Prototype hazard threshold
MAX_WALKABLE_SLOPE = 20.0

blocked_mask = create_blocked_mask(
    slope_degrees,
    max_walkable_slope=MAX_WALKABLE_SLOPE,
)

terrain_cost = apply_blocked_mask(
    terrain_cost,
    blocked_mask,
)

# Keep NoData cells blocked
terrain_cost[~valid_mask] = np.inf

print("Hazard Layer")
print(f"Max walkable slope: {MAX_WALKABLE_SLOPE} degrees")
print(f"Blocked cells: {np.sum(blocked_mask)}")
print(f"Traversable cells: {np.sum(np.isfinite(terrain_cost))}")

print("\nTerrain Cost")
print("Reference slope:", reference_slope)
print(
    "Minimum cost:",
    np.min(terrain_cost[np.isfinite(terrain_cost)])
)
print(
    "Maximum cost:",
    np.max(terrain_cost[np.isfinite(terrain_cost)])
)


# ============================================================
# Select Start and Goal
# ============================================================

rows, cols = terrain_cost.shape

# Prototype positions.
# We will later replace these with user-selected
# projected coordinates from the frontend.

start = (50, 50)
goal = (450, 450)


# ============================================================
# Validate Start / Goal
# ============================================================

if not np.isfinite(terrain_cost[start]):
    raise ValueError("Start cell is not traversable.")

if not np.isfinite(terrain_cost[goal]):
    raise ValueError("Goal cell is not traversable.")

# ============================================================
# Run A* for all route modes
# ============================================================

modes = ["fastest", "balanced", "conservative"]

results = {}

for mode_name in modes:

    mode = get_route_mode(mode_name)

    print()
    print(f"===== {mode.name} =====")

    # Apply route mode to terrain cost
    weighted_cost = weighted_terrain_cost(
        terrain_cost,
        mode.terrain_weight,
    )

    # Keep blocked cells blocked
    weighted_cost = apply_blocked_mask(
        weighted_cost,
        blocked_mask,
    )

    # Keep NoData cells blocked
    weighted_cost[~valid_mask] = np.inf

    # Run A*
    path = astar(
        cost_grid=weighted_cost,
        start=start,
        goal=goal,
        cell_size=resolution,
    )

    if path is None:
        print("No route found.")
        continue

    # --------------------------------------------------------
    # Route distance
    # --------------------------------------------------------

    route_distance = 0.0

    for i in range(1, len(path)):

        previous = path[i - 1]
        current = path[i]

        row1, col1 = previous
        row2, col2 = current

        row_distance = abs(row2 - row1)
        col_distance = abs(col2 - col1)

        movement_cells = math.sqrt(
            row_distance ** 2
            + col_distance ** 2
        )

        movement_distance = (
            movement_cells * resolution
        )

        route_distance += movement_distance

    # --------------------------------------------------------
    # Raw terrain statistics
    # --------------------------------------------------------

    raw_route_costs = np.array(
        [
            terrain_cost[row, col]
            for row, col in path
        ]
    )

    raw_accumulated_cost = np.sum(raw_route_costs)
    raw_average_cost = np.mean(raw_route_costs)

    # --------------------------------------------------------
    # Weighted optimization cost
    # --------------------------------------------------------

    weighted_route_costs = np.array(
        [
            weighted_cost[row, col]
            for row, col in path
        ]
    )

    weighted_accumulated_cost = np.sum(
        weighted_route_costs
    )

    weighted_average_cost = np.mean(
        weighted_route_costs
    )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    results[mode_name] = {
        "mode": mode.name,
        "path": path,
        "distance_km": route_distance / 1000,
        "raw_accumulated_cost": raw_accumulated_cost,
        "raw_average_cost": raw_average_cost,
        "weighted_accumulated_cost": weighted_accumulated_cost,
        "weighted_average_cost": weighted_average_cost,
    }

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("Route cells:", len(path))
    print(
        f"Route distance: "
        f"{route_distance / 1000:.3f} km"
    )

    print(
        f"Raw terrain cost: "
        f"{raw_accumulated_cost:.2f}"
    )

    print(
        f"Average raw terrain cost: "
        f"{raw_average_cost:.4f}"
    )

    print(
        f"Weighted optimization cost: "
        f"{weighted_accumulated_cost:.2f}"
    )

    print(
        f"Weighted average cost: "
        f"{weighted_average_cost:.4f}"
    )

# ============================================================
# Route Elevation Statistics
# ============================================================

route_elevations = np.array(
    [
        dem[row, col]
        for row, col in path
    ]
)

print(
    f"Minimum route elevation: "
    f"{np.min(route_elevations):.2f} m"
)

print(
    f"Maximum route elevation: "
    f"{np.max(route_elevations):.2f} m"
)

print(
    f"Average route elevation: "
    f"{np.mean(route_elevations):.2f} m"
)

# ============================================================
# Plot all route modes
# ============================================================

fig, ax = plt.subplots(
    figsize=(10, 8)
)

terrain_image = np.where(
    valid_mask,
    terrain_cost,
    np.nan,
)

image = ax.imshow(
    terrain_image,
    origin="upper",
)

fig.colorbar(
    image,
    ax=ax,
    label="Terrain Cost",
)

# Plot each route
for mode_name, result in results.items():

    path = result["path"]

    path_rows = np.array(
        [point[0] for point in path]
    )

    path_cols = np.array(
        [point[1] for point in path]
    )

    ax.plot(
        path_cols,
        path_rows,
        linewidth=2,
        label=result["mode"],
    )


# Start point
ax.scatter(
    start[1],
    start[0],
    s=80,
    marker="o",
    label="Start",
)

# Goal point
ax.scatter(
    goal[1],
    goal[0],
    s=80,
    marker="x",
    label="Goal",
)

ax.set_title(
    "MarsWalk Intelligence - Route Mode Comparison"
)

ax.set_xlabel("Column")
ax.set_ylabel("Row")

ax.legend()

plt.tight_layout()

plt.savefig(
    OUTPUT_PATH,
    dpi=150,
)

plt.close()

print(
    "\nComparison image saved successfully:"
)

print(OUTPUT_PATH)