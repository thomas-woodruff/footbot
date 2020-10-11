import numpy as np
import pytest

from footbot.optimiser.team_selector import construct_player_position_weights
from footbot.optimiser.team_selector import construct_player_team_weights
from footbot.optimiser.team_selector import get_elements_from_vector
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


keepers = [
    {"element": 1, "key": 4, "value": 40, "element_type": 1, "team": 1},
    {"element": 2, "key": 5, "value": 40, "element_type": 1, "team": 2},
    {"element": 3, "key": 6, "value": 40, "element_type": 1, "team": 3},
]

defenders = [
    {"element": 4, "key": 4, "value": 40, "element_type": 2, "team": 4},
    {"element": 5, "key": 5, "value": 40, "element_type": 2, "team": 5},
    {"element": 6, "key": 5, "value": 40, "element_type": 2, "team": 6},
    {"element": 7, "key": 6, "value": 40, "element_type": 2, "team": 7},
    {"element": 8, "key": 6, "value": 40, "element_type": 2, "team": 8},
    {"element": 9, "key": 6, "value": 40, "element_type": 2, "team": 9},
]

midfielders = [
    {"element": 10, "key": 4, "value": 40, "element_type": 3, "team": 10},
    {"element": 11, "key": 5, "value": 40, "element_type": 3, "team": 11},
    {"element": 12, "key": 6, "value": 40, "element_type": 3, "team": 12},
    {"element": 13, "key": 6, "value": 40, "element_type": 3, "team": 13},
    {"element": 14, "key": 6, "value": 40, "element_type": 3, "team": 14},
    {"element": 15, "key": 6, "value": 40, "element_type": 3, "team": 15},
]

forwards = [
    {"element": 16, "key": 4, "value": 40, "element_type": 4, "team": 16},
    {"element": 17, "key": 6, "value": 40, "element_type": 4, "team": 17},
    {"element": 18, "key": 6.5, "value": 40, "element_type": 4, "team": 18},
    {"element": 19, "key": 7, "value": 40, "element_type": 4, "team": 19},
    {"element": 20, "key": 3, "value": 40, "element_type": 4, "team": 20},
]

players = keepers + defenders + midfielders + forwards


def test_construct_player_position_matrix():
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


def test_construct_player_team_matrix():
    m = np.identity(20)

    assert np.array_equal(construct_player_team_weights(players), m)


def test_select_team_from_scratch():

    first_team, bench, captain, vice, transfers = select_team(
        players, total_budget=600, optimise_key="key", transfer_penalty=0
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {
        "transfers_in": set(first_team + bench),
        "transfers_out": set(),
    }


def test_select_team_from_existing():

    first_team, bench, captain, vice, transfers = select_team(
        players,
        total_budget=600,
        optimise_key="key",
        existing_squad=[1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        transfer_penalty=0,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {3}, "transfers_out": {1}}


def test_select_team_transfer_penalty():
    squad = [2, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 1, 5, 6, 11]

    kwargs = dict(
        total_budget=600,
        optimise_key="key",
        existing_squad=squad,
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


def test_select_team_transfer_limit():
    squad = [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11]

    first_team, bench, captain, vice, transfers = select_team(
        players,
        total_budget=600,
        optimise_key="key",
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
        total_budget=600,
        optimise_key="key",
        existing_squad=squad,
        transfer_penalty=0,
        transfer_limit=1,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {2, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {3}, "transfers_out": {1}}


def test_select_team_budget_constraint():

    players_edit = players.copy()
    for player in players_edit:
        if player["element"] == 2:
            player["value"] = 41

    first_team, bench, captain, vice, transfers = select_team(
        players_edit,
        total_budget=600,
        optimise_key="key",
        existing_squad=[3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        transfer_penalty=0,
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {1, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
    assert transfers == {"transfers_in": {1}, "transfers_out": {2}}


def test_select_team_team_constraint():

    players_edit = players.copy()
    for player in players_edit:
        if player["element"] in [2, 18, 19]:
            player["team"] = 3

    first_team, bench, captain, vice, transfers = select_team(
        players_edit, total_budget=600, optimise_key="key", transfer_penalty=0
    )

    assert set(first_team) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19}
    assert set(bench) == {1, 5, 6, 11}
    assert set(captain) == {19}
    assert set(vice) == {18}
