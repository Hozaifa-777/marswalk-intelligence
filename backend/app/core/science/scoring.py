from .target import ScienceTarget


def science_score(target: ScienceTarget) -> float:
    """
    Return the normalized scientific value of a target.
    """

    return max(
        0.0,
        min(1.0, target.science_value)
    )