import numpy as np

from app.core.terrain.hazard import (
    create_blocked_mask,
    apply_blocked_mask,
)


def test_create_blocked_mask():

    slope = np.array([
        5.0,
        10.0,
        15.0,
        25.0,
    ])

    blocked = create_blocked_mask(
        slope,
        max_walkable_slope=20.0,
    )

    expected = np.array([
        False,
        False,
        False,
        True,
    ])

    assert np.array_equal(
        blocked,
        expected,
    )


def test_apply_blocked_mask():

    cost = np.array([
        1.0,
        1.5,
        2.0,
    ])

    blocked = np.array([
        False,
        True,
        False,
    ])

    result = apply_blocked_mask(
        cost,
        blocked,
    )

    assert result[0] == 1.0
    assert np.isinf(result[1])
    assert result[2] == 2.0