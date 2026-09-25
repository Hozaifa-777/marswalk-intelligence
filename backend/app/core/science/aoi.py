import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[4]

AOI_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "jezero"
    / "jezero_aoi_boundary.geojson"
)


def load_aoi() -> dict[str, Any]:
    """
    Load the active Area of Interest (AOI) GeoJSON.
    """
    with AOI_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def point_in_polygon(
    point: tuple[float, float],
    polygon: list[tuple[float, float]],
) -> bool:
    """
    Check whether a 2D point is inside or on the boundary
    of a polygon.
    """

    x, y = point

    if len(polygon) < 3:
        return False

    inside = False

    for index in range(len(polygon)):
        x1, y1 = polygon[index]
        x2, y2 = polygon[(index + 1) % len(polygon)]

        # Point on boundary
        cross = (
            (x - x1) * (y2 - y1)
            - (y - y1) * (x2 - x1)
        )

        if abs(cross) < 1e-9:
            if (
                min(x1, x2) - 1e-9 <= x <= max(x1, x2) + 1e-9
                and
                min(y1, y2) - 1e-9 <= y <= max(y1, y2) + 1e-9
            ):
                return True

        # Ray-casting test
        intersects = (
            (y1 > y) != (y2 > y)
            and
            x < (x2 - x1) * (y - y1) / (y2 - y1) + x1
        )

        if intersects:
            inside = not inside

    return inside


def point_in_aoi(
    point: tuple[float, float],
) -> bool:
    """
    Check whether a point belongs to the active AOI.
    """

    aoi = load_aoi()

    geometry = aoi["features"][0]["geometry"]

    if geometry["type"] != "Polygon":
        raise ValueError(
            f"Unsupported AOI geometry: {geometry['type']}"
        )

    polygon = [
        (float(x), float(y))
        for x, y in geometry["coordinates"][0]
    ]

    return point_in_polygon(point, polygon)