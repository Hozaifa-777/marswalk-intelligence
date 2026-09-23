import numpy as np

from app.services.route_service import calculate_route


def test_calculate_route_fastest():
    terrain_cost = np.ones((10, 10), dtype=float)
    blocked_mask = np.zeros((10, 10), dtype=bool)

    result = calculate_route(
        terrain_cost=terrain_cost,
        blocked_mask=blocked_mask,
        start=(0, 0),
        goal=(9, 9),
        resolution=20.0,
        mode_name="fastest",
    )

    assert result is not None
    assert result["mode"] == "Fastest"
    assert result["distance_km"] > 0
    assert len(result["path"]) > 0


def test_calculate_route_balanced():
    terrain_cost = np.ones((10, 10), dtype=float)
    blocked_mask = np.zeros((10, 10), dtype=bool)

    result = calculate_route(
        terrain_cost=terrain_cost,
        blocked_mask=blocked_mask,
        start=(0, 0),
        goal=(9, 9),
        resolution=20.0,
        mode_name="balanced",
    )

    assert result is not None
    assert result["mode"] == "Balanced"


def test_calculate_route_conservative():
    terrain_cost = np.ones((10, 10), dtype=float)
    blocked_mask = np.zeros((10, 10), dtype=bool)

    result = calculate_route(
        terrain_cost=terrain_cost,
        blocked_mask=blocked_mask,
        start=(0, 0),
        goal=(9, 9),
        resolution=20.0,
        mode_name="conservative",
    )

    assert result is not None
    assert result["mode"] == "Conservative"

def test_calculate_route_avoids_blocked_cells():
         
    terrain_cost = np.ones((10, 10), dtype=float)

    blocked_mask = np.zeros((10, 10), dtype=bool)

    # Block a vertical section
    blocked_mask[2:8, 5] = True

    result = calculate_route(
            terrain_cost=terrain_cost,
            blocked_mask=blocked_mask,
            start=(5, 0),
            goal=(5, 9),
            resolution=20.0,
            mode_name="balanced",
    )

    assert result is not None

    path = result["path"]

    for row, col in path:
        assert not blocked_mask[row, col]