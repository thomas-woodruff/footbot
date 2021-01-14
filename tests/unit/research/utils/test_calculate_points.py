import pytest

from footbot.research.utils.calculate_points import calculate_points


@pytest.fixture()
def first_team():
    return [
        {
            "element": 1,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 2,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 3,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 4,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 5,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 6,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 7,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 8,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 9,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 10,
            "is_captain": False,
            "is_vice": True,
            "total_points": 1,
        },
        {
            "element": 11,
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
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 15,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 13,
            "is_captain": False,
            "is_vice": False,
            "total_points": 1,
        },
        {
            "element": 14,
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


def test_calculate_points_wildcard(first_team, bench):

    assert calculate_points(first_team, bench, 15, 0, wildcard=True) == 12


def test_calculate_points_free_hit(first_team, bench):

    assert calculate_points(first_team, bench, 15, 0, free_hit=True) == 12
