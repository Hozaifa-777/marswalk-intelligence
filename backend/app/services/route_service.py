import math

import numpy as np

from app.core.routing.astar import astar
from app.core.routing.cost_function import weighted_terrain_cost
from app.core.routing.route_modes import get_route_mode
from app.core.terrain.hazard import apply_blocked_mask


def calculate_route(
    terrain_cost: np.ndarray,
    blocked_mask: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    resolution: float,
    mode_name: str,
):
    """
    Calculate a route using A* and a selected route mode.
    """

    # Get route mode configuration
    mode = get_route_mode(mode_name)

    # Apply mode-specific terrain weighting
    weighted_cost = weighted_terrain_cost(
        terrain_cost,
        mode.terrain_weight,
    )

    # Apply blocked terrain
    weighted_cost = apply_blocked_mask(
        weighted_cost,
        blocked_mask,
    )

    # Run A*
    path = astar(
        cost_grid=weighted_cost,
        start=start,
        goal=goal,
        cell_size=resolution,
    )

    if path is None:
        return None

    # Calculate route distance
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

        route_distance += (
            movement_cells * resolution
        )

    # Raw terrain cost along route
    route_costs = np.array(
        [
            terrain_cost[row, col]
            for row, col in path
        ]
    )

    raw_accumulated_cost = float(
        np.sum(route_costs)
    )

    raw_average_cost = float(
        np.mean(route_costs)
    )

    # Weighted optimization cost
    weighted_route_costs = np.array(
        [
            weighted_cost[row, col]
            for row, col in path
        ]
    )

    weighted_accumulated_cost = float(
        np.sum(weighted_route_costs)
    )

    weighted_average_cost = float(
        np.mean(weighted_route_costs)
    )

    return {
        "mode": mode.name,
        "path": path,
        "distance_km": route_distance / 1000,
        "raw_terrain_cost": raw_accumulated_cost,
        "average_raw_terrain_cost": raw_average_cost,
        "optimization_cost": weighted_accumulated_cost,
        "average_optimization_cost": weighted_average_cost,
    }