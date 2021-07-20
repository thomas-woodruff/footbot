import pytest
import random

from footbot.optimiser.select_team import construct_picks_list
from footbot.optimiser.select_team import sort_players_into_position


@pytest.fixture
def first_team():
    first_team = [
        {
            "element": 1,
            "key": 4,
            "value": 40,
            "element_type": 1,
            "team": 1,
            "safe_web_name": "alex",
        },
        {
            "element": 4,
            "key": 4,
            "value": 40,
            "element_type": 2,
            "team": 4,
            "safe_web_name": "dan",
        },
        {
            "element": 5,
            "key": 5,
            "value": 40,
            "element_type": 2,
            "team": 5,
            "safe_web_name": "ed",
        },
        {
            "element": 6,
            "key": 5.25,
            "value": 40,
            "element_type": 2,
            "team": 6,
            "safe_web_name": "fred",
        },
        {
            "element": 10,
            "key": 4,
            "value": 40,
            "element_type": 3,
            "team": 10,
            "safe_web_name": "jack",
        },
        {
            "element": 11,
            "key": 5.5,
            "value": 40,
            "element_type": 3,
            "team": 11,
            "safe_web_name": "kane",
        },
        {
            "element": 12,
            "key": 6,
            "value": 40,
            "element_type": 3,
            "team": 12,
            "safe_web_name": "lee",
        },
        {
            "element": 13,
            "key": 6,
            "value": 40,
            "element_type": 3,
            "team": 13,
            "safe_web_name": "matt",
        },

        {
            "element": 16,
            "key": 4,
            "value": 40,
            "element_type": 4,
            "team": 16,
            "safe_web_name": "pete",
        },
        {
            "element": 17,
            "key": 6,
            "value": 40,
            "element_type": 4,
            "team": 17,
            "safe_web_name": "quinn",
        },
        {
            "element": 18,
            "key": 6.5,
            "value": 40,
            "element_type": 4,
            "team": 18,
            "safe_web_name": "rich",
        },
    ]

    return first_team


@pytest.fixture
def bench():

    bench = [
        {
            "element": 2,
            "key": 5,
            "value": 40,
            "element_type": 1,
            "team": 2,
            "safe_web_name": "ben",
        },
        {
            "element": 7,
            "key": 6,
            "value": 40,
            "element_type": 2,
            "team": 7,
            "safe_web_name": "george",
        },
        {
            "element": 8,
            "key": 6,
            "value": 40,
            "element_type": 2,
            "team": 8,
            "safe_web_name": "hugh",
        },
        {
            "element": 14,
            "key": 6,
            "value": 40,
            "element_type": 3,
            "team": 14,
            "safe_web_name": "nick",
        },
    ]

    return bench


def test_sort_players_into_position(first_team):

    shuffled_first_team = first_team.copy()
    random.shuffle(shuffled_first_team)

    assert sort_players_into_position(shuffled_first_team) == first_team


def test_construct_picks_list(first_team, bench):

    captain = first_team[-1:]
    vice = first_team[-2:]

    expected = [
        {
            "element": 1,
            "position": 1,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 4,
            "position": 2,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 5,
            "position": 3,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 6,
            "position": 4,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 10,
            "position": 5,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 11,
            "position": 6,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 12,
            "position": 7,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 13,
            "position": 8,
            "is_captain": False,
            "is_vice_captain": False
        },

        {
            "element": 16,
            "position": 9,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 17,
            "position": 10,
            "is_captain": False,
            "is_vice_captain": True
        },
        {
            "element": 18,
            "position": 11,
            "is_captain": True,
            "is_vice_captain": False
        },
        {
            "element": 2,
            "position": 12,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 7,
            "position": 13,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 8,
            "position": 14,
            "is_captain": False,
            "is_vice_captain": False
        },
        {
            "element": 14,
            "position": 15,
            "is_captain": False,
            "is_vice_captain": False
        },
    ]

    # shuffle inputs to test sorting
    random.shuffle(first_team)
    random.shuffle(bench)

    assert construct_picks_list(first_team, bench, captain, vice) == expected
    # assert expected == expected
