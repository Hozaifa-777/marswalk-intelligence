from app.core.routing.route_modes import (
    get_route_mode,
)


def test_route_modes():
    fastest = get_route_mode("fastest")
    balanced = get_route_mode("balanced")
    conservative = get_route_mode("conservative")

    assert fastest.name == "Fastest"
    assert balanced.name == "Balanced"
    assert conservative.name == "Conservative"

    assert fastest.terrain_weight < balanced.terrain_weight
    assert balanced.terrain_weight < conservative.terrain_weight