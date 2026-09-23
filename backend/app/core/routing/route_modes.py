from dataclasses import dataclass


@dataclass(frozen=True)
class RouteMode:
    name: str
    distance_weight: float
    terrain_weight: float


ROUTE_MODES = {
    "fastest": RouteMode(
        name="Fastest",
        distance_weight=1.0,
        terrain_weight=0.2,
    ),

    "balanced": RouteMode(
        name="Balanced",
        distance_weight=1.0,
        terrain_weight=1.0,
    ),

    "conservative": RouteMode(
        name="Conservative",
        distance_weight=1.0,
        terrain_weight=2.0,
    ),
}


def get_route_mode(mode: str) -> RouteMode:
    if mode not in ROUTE_MODES:
        raise ValueError(f"Unknown route mode: {mode}")

    return ROUTE_MODES[mode]