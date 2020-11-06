import pytest
from footbot.research.utils.subs import check_valid_formation, make_subs


@pytest.fixture()
def first_team():
    return [
        {"element": 1, "element_type": 1, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 2, "element_type": 2, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 3, "element_type": 2, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 4, "element_type": 2, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 5, "element_type": 3, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 6, "element_type": 3, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 7, "element_type": 3, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 8, "element_type": 3, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 9, "element_type": 4, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 10, "element_type": 4, "minutes": 90, "is_captain": 0, "is_vice": 1},
        {"element": 11, "element_type": 4, "minutes": 90, "is_captain": 1, "is_vice": 0},
    ]


@pytest.fixture()
def bench():
    return [
        {"element": 12, "element_type": 1, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 15, "element_type": 3, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 13, "element_type": 2, "minutes": 90, "is_captain": 0, "is_vice": 0},
        {"element": 14, "element_type": 2, "minutes": 90, "is_captain": 0, "is_vice": 0},
    ]


def test_check_valid_formation_valid(first_team):

    assert check_valid_formation(first_team)


def test_check_valid_formation_invalid(first_team):
    for player in first_team:
        if player["element"] in [4]:
            player["element_type"] = 3

    assert not check_valid_formation(first_team)


def test_make_subs_no_subs(first_team, bench):
    ft, b = make_subs(first_team, bench)
    ft = [i['element'] for i in ft]
    b = [i['element'] for i in b]

    expected_ft = [i['element'] for i in first_team]
    expected_b = [i['element'] for i in bench]

    assert set(ft) == set(expected_ft)
    assert set(b) == set(expected_b)


def test_make_subs_all_subs(first_team, bench):
    for player in first_team:
        if player["element"] in [1, 8, 11]:
            player["minutes"] = 0

    ft, b = make_subs(first_team, bench)
    ft = [i['element'] for i in ft]
    b = [i['element'] for i in b]

    ft_expected = [12, 2, 3, 4, 5, 6, 7, 15, 9, 10, 13]
    b_expected = [1, 8, 11, 14]

    assert set(ft) == set(ft_expected)
    assert set(b) == set(b_expected)


def test_make_subs_some_subs(first_team, bench):
    for player in first_team:
        if player["element"] in [2, 3, 4]:
            player["minutes"] = 0

    ft, b = make_subs(first_team, bench)
    ft = [i['element'] for i in ft]
    b = [i['element'] for i in b]

    ft_expected = [1, 13, 14, 4, 5, 6, 7, 8, 9, 10, 11]
    b_expected = [12, 2, 3, 15]

    assert set(ft) == set(ft_expected)
    assert set(b) == set(b_expected)
