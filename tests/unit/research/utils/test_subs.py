import pytest

from footbot.research.utils.subs import check_valid_formation
from footbot.research.utils.subs import make_subs
from footbot.research.utils.subs import pick_captain


@pytest.fixture()
def first_team_dicts():
    return [
        {
            "element_all": 1,
            "element_type": 1,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 2,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 3,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 4,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 5,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 6,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 7,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 8,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 9,
            "element_type": 4,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 10,
            "element_type": 4,
            "minutes": 90,
            "is_captain": False,
            "is_vice": True,
        },
        {
            "element_all": 11,
            "element_type": 4,
            "minutes": 90,
            "is_captain": True,
            "is_vice": False,
        },
    ]


@pytest.fixture()
def bench_dicts():
    return [
        {
            "element_all": 12,
            "element_type": 1,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 15,
            "element_type": 3,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 13,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
        {
            "element_all": 14,
            "element_type": 2,
            "minutes": 90,
            "is_captain": False,
            "is_vice": False,
        },
    ]


def test_check_valid_formation_valid(first_team_dicts):

    assert check_valid_formation(first_team_dicts)


def test_check_valid_formation_invalid(first_team_dicts):
    for player in first_team_dicts:
        if player["element_all"] in [4]:
            player["element_type"] = 3

    assert not check_valid_formation(first_team_dicts)


def test_make_subs_no_subs(first_team_dicts, bench_dicts):
    ft, b = make_subs(first_team_dicts, bench_dicts)
    ft = [i["element_all"] for i in ft]
    b = [i["element_all"] for i in b]

    expected_ft = [i["element_all"] for i in first_team_dicts]
    expected_b = [i["element_all"] for i in bench_dicts]

    assert set(ft) == set(expected_ft)
    assert set(b) == set(expected_b)


def test_make_subs_all_subs(first_team_dicts, bench_dicts):
    for player in first_team_dicts:
        if player["element_all"] in [1, 8, 11]:
            player["minutes"] = 0

    ft, b = make_subs(first_team_dicts, bench_dicts)
    ft = [i["element_all"] for i in ft]
    b = [i["element_all"] for i in b]

    ft_expected = [12, 2, 3, 4, 5, 6, 7, 15, 9, 10, 13]
    b_expected = [1, 8, 11, 14]

    assert set(ft) == set(ft_expected)
    assert set(b) == set(b_expected)


def test_make_subs_some_subs(first_team_dicts, bench_dicts):
    for player in first_team_dicts:
        if player["element_all"] in [2, 3, 4]:
            player["minutes"] = 0

    ft, b = make_subs(first_team_dicts, bench_dicts)
    ft = [i["element_all"] for i in ft]
    b = [i["element_all"] for i in b]

    ft_expected = [1, 13, 14, 4, 5, 6, 7, 8, 9, 10, 11]
    b_expected = [12, 2, 3, 15]

    assert set(ft) == set(ft_expected)
    assert set(b) == set(b_expected)


def test_pick_captain_no_change(first_team_dicts):
    ft = pick_captain(first_team_dicts)
    c = [i["element_all"] for i in ft if i["is_captain"]]
    v = [i["element_all"] for i in ft if i["is_vice"]]

    assert c == [11]
    assert v == [10]


def test_pick_captain_sub(first_team_dicts):
    for player in first_team_dicts:
        if player["is_captain"]:
            player["minutes"] = 0

    ft = pick_captain(first_team_dicts)
    c = [i["element_all"] for i in ft if i["is_captain"]]
    v = [i["element_all"] for i in ft if i["is_vice"]]

    assert c == [10]
    assert v == []


def test_pick_captain_both_missing(first_team_dicts):
    for player in first_team_dicts:
        if player["is_captain"] or player["is_vice"]:
            player["minutes"] = 0

    ft = pick_captain(first_team_dicts)
    c = [i["element_all"] for i in ft if i["is_captain"]]
    v = [i["element_all"] for i in ft if i["is_vice"]]

    assert c == []
    assert v == []
