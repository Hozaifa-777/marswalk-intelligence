import numpy as np

from app.core.routing.cost_function import (
    slope_cost,
    combine_costs,
)


def test_slope_cost():

    slope = np.array([
        0.0,
        5.0,
        10.0,
    ])

    costs = slope_cost(
        slope,
        reference_slope=10.0,
    )

    assert costs[0] == 1.0
    assert costs[-1] == 2.0


def test_combine_costs():

    base = np.array([1.0, 2.0])

    hazard = np.array([0.1, 0.2])

    science = np.array([0.2, 0.5])

    result = combine_costs(
        base,
        hazard_cost=hazard,
        science_reward=science,
    )

    expected = np.array([
        0.9,
        1.7,
    ])

    assert np.allclose(result, expected)