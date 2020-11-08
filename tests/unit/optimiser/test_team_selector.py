import numpy as np
import pytest

from footbot.optimiser.team_selector import construct_player_position_weights
from footbot.optimiser.team_selector import construct_player_team_weights
from footbot.optimiser.team_selector import get_elements_from_vector
from footbot.optimiser.team_selector import get_sorted_safe_web_names
from footbot.optimiser.team_selector import select_team
from footbot.optimiser.team_selector import validate_optimisation_arguments


def test_get_elements_from_vector():
    vector = [0.0, 1.0]
    player_elements = [1, 2]

    assert get_elements_from_vector(vector, player_elements) == [2]

    with pytest.raises(Exception) as e:
        get_elements_from_vector([0.1], player_elements)
    assert "Vector contains values other than 0. and 1." in str(e.value)

    with pytest.raises(Exception) as e:
        get_elements_from_vector([0.0], player_elements)
    assert "`vector` and `player_elements` are different lengths" in str(e.value)


def test_validate_optimisation_arguments():

    kwargs = dict(
        total_budget=1000,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        existing_squad=[],
        transfer_penalty=4,
        transfer_limit=15,
    )

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "total_budget": -1})
    assert "`total_budget` must be positive" in str(e.value)

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "bench_factor": 0.11})
    assert "`first_team_factor` and `bench_factor` must sum to 1." in str(e.value)

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "vice_factor": 0.11})
    assert "`captain_factor` and `vice_factor` must sum to 1." in str(e.value)

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "existing_squad": [1]})
    assert "`existing_squad` must consist of 15 players or be an empty array" in str(
        e.value
    )

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "existing_squad": False})
    assert "`existing_squad` must consist of 15 players or be an empty array" in str(
        e.value
    )

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "transfer_penalty": -1})
    assert "`transfer_penalty` must be non-negative" in str(e.value)

    with pytest.raises(Exception) as e:
        validate_optimisation_arguments(**{**kwargs, "transfer_limit": 16})
    assert "`transfer_limit` must be an integer between 0 and 15" in str(e.value)


@pytest.fixture
def players():

    keepers = [
        {
            "element": 1,
            "key": 4,
            "value": 40,
            "element_type": 1,
            "team": 1,
            "safe_web_name": "alex",
        },
        {
            "element": 2,
            "key": 5,
            "value": 40,
            "element_type": 1,
            "team": 2,
            "safe_web_name": "ben",
        },
        {
            "element": 3,
            "key": 6,
            "value": 40,
            "element_type": 1,
            "team": 3,
            "safe_web_name": "carl",
        },
    ]

    defenders = [
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
            "key": 5,
            "value": 40,
            "element_type": 2,
            "team": 6,
            "safe_web_name": "fred",
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
            "element": 9,
            "key": 6,
            "value": 40,
            "element_type": 2,
            "team": 9,
            "safe_web_name": "ira",
        },
    ]

    midfielders = [
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
            "key": 5,
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
            "element": 14,
            "key": 6,
            "value": 40,
            "element_type": 3,
            "team": 14,
            "safe_web_name": "nick",
        },
        {
            "element": 15,
            "key": 6,
            "value": 40,
            "element_type": 3,
            "team": 15,
            "safe_web_name": "oli",
        },
    ]

    forwards = [
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
        {
            "element": 19,
            "key": 7,
            "value": 40,
            "element_type": 4,
            "team": 19,
            "safe_web_name": "sid",
        },
        {
            "element": 20,
            "key": 3,
            "value": 40,
            "element_type": 4,
            "team": 20,
            "safe_web_name": "tom",
        },
    ]

    return keepers + defenders + midfielders + forwards


def test_construct_player_position_matrix(players):
    m = np.array(
        [
            [
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            [
                0.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
            [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
            ],
        ]
    )

    assert np.array_equal(construct_player_position_weights(players), m)


def test_construct_player_team_matrix(players):
    m = np.identity(20)

    assert np.array_equal(construct_player_team_weights(players), m)


def test_select_team_from_scratch(players):

    first_team, bench, captain, vice, transfers = select_team(
        players, optimise_key="key", total_budget=600, transfer_penalty=0
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {
        "transfers_in": set(first_team + bench),
        "transfers_out": set(),
    }
    assert captain[0] in first_team
    assert vice[0] in first_team


def test_select_team_from_existing(players):

    first_team, bench, captain, vice, transfers = select_team(
        players,
        optimise_key="key",
        existing_squad=[1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        total_budget=600,
        transfer_penalty=0,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {3}, "transfers_out": {1}}
    assert captain[0] in first_team
    assert vice[0] in first_team


def test_select_team_transfer_penalty(players):
    squad = [2, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 1, 5, 6, 11]

    kwargs = dict(
        optimise_key="key",
        existing_squad=squad,
        total_budget=600,
        first_team_factor=1,
        bench_factor=0,
        captain_factor=1,
        vice_factor=0,
        transfer_penalty=1,
    )

    # transferring 2 for 3 is optimal
    first_team, bench, captain, vice, transfers = select_team(players, **kwargs)
    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}

    # transferring 2 for 3 is not optimal
    first_team, bench, captain, vice, transfers = select_team(
        players, **{**kwargs, "transfer_penalty": 1.1}
    )
    assert set(first_team) == {2, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}


def test_select_team_transfer_limit(players):
    squad = [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11]

    first_team, bench, captain, vice, transfers = select_team(
        players,
        optimise_key="key",
        total_budget=600,
        existing_squad=squad,
        transfer_penalty=0,
        transfer_limit=0,
    )

    assert set(first_team) == {2, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {1, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": set(), "transfers_out": set()}

    first_team, bench, captain, vice, transfers = select_team(
        players,
        optimise_key="key",
        existing_squad=squad,
        total_budget=600,
        transfer_penalty=0,
        transfer_limit=1,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {3}, "transfers_out": {1}}


def test_select_team_budget_constraint(players):

    for player in players:
        if player["element"] == 2:
            player["value"] = 41

    first_team, bench, captain, vice, transfers = select_team(
        players,
        optimise_key="key",
        existing_squad=[3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        total_budget=600,
        transfer_penalty=0,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {1, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {1}, "transfers_out": {2}}


def test_select_team_team_constraint(players):

    for player in players:
        if player["element"] in [2, 18, 19]:
            player["team"] = 3

    first_team, bench, captain, vice, transfers = select_team(
        players, optimise_key="key", total_budget=600, transfer_penalty=0
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {1, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}


def test_select_team_captain_vice_in_first_team(players):
    for player in players:
        if player["element"] in [1]:
            player["key"] = 11
        if player["element"] in [2]:
            player["key"] = 10

    first_team, bench, captain, vice, transfers = select_team(
        players, optimise_key="key", total_budget=600, transfer_penalty=0
    )

    assert captain[0] in first_team
    assert vice[0] in first_team


def test_get_sorted_safe_web_names(players):

    assert get_sorted_safe_web_names([16, 10, 4, 1], players) == [
        "alex",
        "dan",
        "jack",
        "pete",
    ]
