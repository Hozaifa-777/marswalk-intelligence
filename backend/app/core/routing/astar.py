import heapq
import math
from typing import Optional

import numpy as np


# 8 possible movements:
# (row_change, col_change, movement_distance)
MOVEMENTS = [
    (-1, 0, 1.0),              # Up
    (1, 0, 1.0),               # Down
    (0, -1, 1.0),              # Left
    (0, 1, 1.0),               # Right
    (-1, -1, math.sqrt(2)),     # Up-left
    (-1, 1, math.sqrt(2)),      # Up-right
    (1, -1, math.sqrt(2)),      # Down-left
    (1, 1, math.sqrt(2)),       # Down-right
]


def heuristic(
    current: tuple[int, int],
    goal: tuple[int, int],
    cell_size: float,
    minimum_cost: float = 1.0,
) -> float:
    """
    Octile-distance heuristic for an 8-direction grid.

    The heuristic estimates the cheapest possible remaining
    distance while respecting the minimum possible terrain cost.
    """

    row, col = current
    goal_row, goal_col = goal

    dr = abs(goal_row - row)
    dc = abs(goal_col - col)

    diagonal = min(dr, dc)
    straight = max(dr, dc) - diagonal

    distance = (
        diagonal * math.sqrt(2)
        + straight
    ) * cell_size

    return distance * minimum_cost


def astar(
    cost_grid: np.ndarray,
    start: tuple[int, int],
    goal: tuple[int, int],
    cell_size: float = 20.0,
) -> Optional[list[tuple[int, int]]]:
    """
    Find a minimum-cost route using A*.

    Parameters
    ----------
    cost_grid:
        2D array containing the traversal cost of each cell.
        np.inf represents an impassable cell.

    start:
        (row, column) of the starting cell.

    goal:
        (row, column) of the destination cell.

    cell_size:
        Size of one grid cell in meters.

    Returns
    -------
    list[(row, column)] or None
        The route from start to goal.
    """

    rows, cols = cost_grid.shape

    # -------------------------
    # Validate start and goal
    # -------------------------

    for name, position in [
        ("start", start),
        ("goal", goal),
    ]:
        row, col = position

        if not (0 <= row < rows and 0 <= col < cols):
            raise ValueError(
                f"{name} position is outside the grid."
            )

        if not np.isfinite(cost_grid[row, col]):
            raise ValueError(
                f"{name} cell is not traversable."
            )

    # -------------------------
    # Minimum terrain cost
    # -------------------------

    finite_costs = cost_grid[np.isfinite(cost_grid)]

    if finite_costs.size == 0:
        return None

    minimum_cost = float(np.min(finite_costs))

    # -------------------------
    # Priority queue
    # -------------------------

    open_set = []

    start_h = heuristic(
        start,
        goal,
        cell_size,
        minimum_cost,
    )

    heapq.heappush(
        open_set,
        (start_h, start),
    )

    # Cost from start to each cell
    g_score = {
        start: 0.0
    }

    # Used to reconstruct the final route
    came_from = {}

    # -------------------------
    # A* search
    # -------------------------

    while open_set:

        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(
                came_from,
                current,
            )

        current_row, current_col = current

        for dr, dc, movement_multiplier in MOVEMENTS:

            neighbor_row = current_row + dr
            neighbor_col = current_col + dc

            # Outside grid
            if not (
                0 <= neighbor_row < rows
                and 0 <= neighbor_col < cols
            ):
                continue

            neighbor = (
                neighbor_row,
                neighbor_col,
            )

            neighbor_cost = cost_grid[
                neighbor_row,
                neighbor_col,
            ]

            # NoData / blocked cell
            if not np.isfinite(neighbor_cost):
                continue

            # Physical distance of this movement
            movement_distance = (
                cell_size * movement_multiplier
            )

            # Traversal cost
            movement_cost = (
                movement_distance * neighbor_cost
            )

            tentative_g = (
                g_score[current]
                + movement_cost
            )

            previous_g = g_score.get(
                neighbor,
                float("inf"),
            )

            if tentative_g < previous_g:

                came_from[neighbor] = current

                g_score[neighbor] = tentative_g

                f_score = (
                    tentative_g
                    + heuristic(
                        neighbor,
                        goal,
                        cell_size,
                        minimum_cost,
                    )
                )

                heapq.heappush(
                    open_set,
                    (f_score, neighbor),
                )

    # No route found
    return None


def reconstruct_path(
    came_from: dict,
    current: tuple[int, int],
) -> list[tuple[int, int]]:
    """
    Reconstruct the route after A* reaches the goal.
    """

    path = [current]

    while current in came_from:
        current = came_from[current]
        path.append(current)

    path.reverse()

    return path