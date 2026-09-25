from app.core.science.registry import ScienceTargetRegistry
from app.core.science.target import ScienceTarget


def test_registry_accepts_target_inside_aoi():

    registry = ScienceTargetRegistry()

    target = ScienceTarget(
        id="target_inside",
        name="Test Target Inside",
        target_type="carbonate",
        source="CRISM",
        science_value=0.8,
        x=4355000,
        y=1095000,
    )

    registry.add(target)

    targets = registry.get_all()

    assert len(targets) == 1
    assert targets[0].id == "target_inside"


def test_registry_rejects_target_outside_aoi():

    registry = ScienceTargetRegistry()

    target = ScienceTarget(
        id="target_outside",
        name="Test Target Outside",
        target_type="carbonate",
        source="CRISM",
        science_value=0.8,
        x=4400000,
        y=1120000,
    )

    registry.add(target)

    assert registry.get_all() == []


def test_registry_filters_by_type():

    registry = ScienceTargetRegistry()

    registry.add(
        ScienceTarget(
            id="carbonate_01",
            name="Carbonate Target",
            target_type="carbonate",
            source="CRISM",
            science_value=0.9,
            x=4355000,
            y=1095000,
        )
    )

    registry.add(
        ScienceTarget(
            id="olivine_01",
            name="Olivine Target",
            target_type="olivine",
            source="CRISM",
            science_value=0.7,
            x=4356000,
            y=1096000,
        )
    )

    carbonate_targets = registry.get_by_type("carbonate")

    assert len(carbonate_targets) == 1
    assert carbonate_targets[0].id == "carbonate_01"