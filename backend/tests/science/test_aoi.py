from app.core.science.aoi import point_in_aoi


def test_point_inside_aoi():
    point = (4355000, 1095000)

    assert point_in_aoi(point) is True


def test_point_outside_aoi():
    point = (4400000, 1120000)

    assert point_in_aoi(point) is False