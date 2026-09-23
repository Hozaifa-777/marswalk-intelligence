import numpy as np


def create_blocked_mask(
    slope: np.ndarray,
    max_walkable_slope: float,
) -> np.ndarray:
    """
    Create a mask for terrain that should not be traversed.

    True  = blocked
    False = traversable

    The threshold is a configurable prototype parameter.
    It is not a validated astronaut-safety limit.
    """

    blocked = slope > max_walkable_slope

    return blocked


def apply_blocked_mask(
    cost_grid: np.ndarray,
    blocked_mask: np.ndarray,
) -> np.ndarray:
    """
    Convert blocked cells into infinite traversal cost.
    """

    result = cost_grid.copy()

    result[blocked_mask] = np.inf

    return result