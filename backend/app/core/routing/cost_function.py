import numpy as np


def normalize_feature(
    feature: np.ndarray,
    reference: float,
) -> np.ndarray:
    """
    Normalize a feature using a reference value.

    Values above the reference are clipped to 1.
    """

    normalized = feature / reference

    return np.clip(normalized, 0.0, 1.0)


def slope_cost(
    slope: np.ndarray,
    reference_slope: float,
) -> np.ndarray:
    """
    Convert slope into a terrain cost.

    Current prototype:
        cost = 1 + normalized_slope^2

    Minimum cost = 1
    Maximum cost = 2
    """

    normalized_slope = normalize_feature(
        slope,
        reference_slope,
    )

    return 1.0 + normalized_slope ** 2

def weighted_terrain_cost(
    terrain_cost: np.ndarray,
    terrain_weight: float,
) -> np.ndarray:
    terrain_penalty = terrain_cost - 1.0

    return 1.0 + terrain_weight * terrain_penalty

def combine_costs(
    base_cost: np.ndarray,
    *,
    distance_cost: np.ndarray | None = None,
    hazard_cost: np.ndarray | None = None,
    science_reward: np.ndarray | None = None,
) -> np.ndarray:
    """
    Combine routing features into one final cost surface.

    Optional features are intentionally separated so new
    NASA-derived features can be added later.
    """

    total_cost = base_cost.copy()

    if distance_cost is not None:
        total_cost += distance_cost

    if hazard_cost is not None:
        total_cost += hazard_cost

    if science_reward is not None:
        total_cost -= science_reward

    return total_cost