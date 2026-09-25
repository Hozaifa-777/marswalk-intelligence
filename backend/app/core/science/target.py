from dataclasses import dataclass


@dataclass(frozen=True)
class ScienceTarget:
    id: str
    name: str
    target_type: str
    source: str
    science_value: float
    x: float
    y: float

    def __post_init__(self):
        if not 0.0 <= self.science_value <= 1.0:
            raise ValueError(
                "science_value must be between 0 and 1"
            )