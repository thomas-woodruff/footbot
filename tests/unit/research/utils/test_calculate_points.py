import pytest

from footbot.research.utils.calculate_points import calculate_points


@pytest.fixture()
def first_team():
    return [
        {
            "element": 1,
            "element_type": 1,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 2,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 3,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 4,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 5,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 6,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 7,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 8,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 9,
            "element_type": 4,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 10,
            "element_type": 4,
            "minutes": 90,
            "is_captain": False,
            "is_vice": True,
            "total_points": 1,
        },
        {
            "element": 11,
            "element_type": 4,
            "minutes": 90,
            "is_captain": True,
            "is_vice": False,
            "total_points": 1,
        },
    ]


@pytest.fixture()
def bench():
    return [
        {
            "element": 12,
            "element_type": 1,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 15,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 13,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 14,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
    ]


def test_calculate_points_no_chips(first_team, bench):

    assert calculate_points(first_team, bench, 1, 1) == 12
    assert calculate_points(first_team, bench, 0, 1) == 12
    assert calculate_points(first_team, bench, 2, 1) == 8
    assert calculate_points(first_team, bench, 3, 1) == 4


def test_calculate_points_triple_captain(first_team, bench):
    assert calculate_points(first_team, bench, 1, 1, triple_captain=True) == 13


def test_calculate_points_bench_boost(first_team, bench):
    assert calculate_points(first_team, bench, 1, 1, bench_boost=True) == 16
