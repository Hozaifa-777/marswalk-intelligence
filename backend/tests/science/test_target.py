import pytest

from app.core.science.target import ScienceTarget


def test_valid_target():

    target = ScienceTarget(
        id="test_01",
        name="Test Target",
        target_type="carbonate",
        source="CRISM",
        science_value=0.8,
        x=4355000,
        y=1095000,
    )

    assert target.science_value == 0.8


def test_invalid_science_value():

    with pytest.raises(ValueError):

        ScienceTarget(
            id="test_01",
            name="Test Target",
            target_type="carbonate",
            source="CRISM",
            science_value=1.5,
            x=4355000,
            y=1095000,
        )