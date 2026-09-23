import numpy as np

from app.core.routing.astar import astar


def test_astar_finds_route():

    cost_grid = np.ones((10, 10))

    start = (0, 0)
    goal = (9, 9)

    path = astar(
        cost_grid,
        start,
        goal,
        cell_size=20.0,
    )

    assert path is not None
    assert path[0] == start
    assert path[-1] == goal


def test_astar_avoids_blocked_cells():

    cost_grid = np.ones((5, 5))

    # Block the center
    cost_grid[2, 2] = np.inf

    start = (0, 0)
    goal = (4, 4)

    path = astar(
        cost_grid,
        start,
        goal,
        cell_size=20.0,
    )

    assert path is not None
    assert (2, 2) not in path


def test_astar_no_route():

    cost_grid = np.ones((3, 3))

    # Block everything around the start
    cost_grid[0, 1] = np.inf
    cost_grid[1, 0] = np.inf
    cost_grid[1, 1] = np.inf

    start = (0, 0)
    goal = (2, 2)

    path = astar(
        cost_grid,
        start,
        goal,
        cell_size=20.0,
    )

    assert path is None