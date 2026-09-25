from .aoi import point_in_aoi
from .target import ScienceTarget


class ScienceTargetRegistry:

    def __init__(self):
        self._targets: list[ScienceTarget] = []

    def add(self, target: ScienceTarget) -> None:
        """
        Add a target only if it belongs to the active AOI.
        """

        if not point_in_aoi((target.x, target.y)):
            return

        self._targets.append(target)

    def get_all(self) -> list[ScienceTarget]:
        return list(self._targets)

    def get_by_type(
        self,
        target_type: str,
    ) -> list[ScienceTarget]:

        return [
            target
            for target in self._targets
            if target.target_type == target_type
        ]

    def clear(self) -> None:
        self._targets.clear()