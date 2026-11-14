import numpy as np
from affine import Affine

from app.api.terrain import build_heightmap_payload


def test_heightmap_is_downsampled_and_keeps_mars_transform():
    dem = np.arange(100, dtype=float).reshape(10, 10)
    slope = np.full((10, 10), 4.5, dtype=float)
    dem[0, 0] = np.nan

    payload = build_heightmap_payload(
        {
            "dem": dem,
            "slope": slope,
            "transform": Affine(20, 0, 4_350_000, 0, -20, 1_100_000),
        },
        max_dimension=4,
    )

    assert payload["width"] == 4
    assert payload["height"] == 4
    assert payload["crs"] == "Mars_2000_Sphere_Equirectangular"
    assert payload["coordinate_units"] == "meters"
    assert payload["transform"] == [20.0, 0.0, 4_350_000.0, 0.0, -20.0, 1_100_000.0]
    assert payload["elevation_m"][0][0] is None
    assert payload["slope_deg"][1][1] == 4.5
    assert payload["valid_mask"][0][0] is False


def test_heightmap_does_not_exceed_source_dimensions():
    dem = np.array([[1.0, 2.0], [3.0, 4.0]])
    slope = np.ones((2, 2))

    payload = build_heightmap_payload(
        {
            "dem": dem,
            "slope": slope,
            "transform": Affine(20, 0, 100, 0, -20, 200),
        },
        max_dimension=256,
    )

    assert payload["width"] == 2
    assert payload["height"] == 2
    assert payload["elevation_m"] == [[1.0, 2.0], [3.0, 4.0]]
