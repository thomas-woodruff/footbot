import logging

import cvxpy as cp
import numpy as np
import requests

from footbot.data.utils import get_current_event
from footbot.data.utils import run_templated_query
from footbot.data.utils import set_up_bigquery

logger = logging.getLogger(__name__)


def get_elements_from_vector(vector, player_elements):
    """
    Convert array of indicators into array of player identifiers.

    :param vector: An array containing an indicator for every player
    :param player_elements: An array containing an identifier for every player
    :return: An array containing only elements where corresponding indicator is on
    """

    if any([v not in [0.0, 1.0] for v in vector]):
        raise Exception("Vector contains values other than 0. and 1.")

    if len(vector) != len(player_elements):
        raise Exception("`vector` and `player_elements` are different lengths")

    return [e for e, v in zip(player_elements, vector) if v]


def validate_optimisation_arguments(
    total_budget,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    existing_squad,
    transfer_penalty,
    transfer_limit,
):
    """
    Validate arguments passed to optimiser.

    :param total_budget: Total budget available, i.e. total team value + bank
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param existing_squad: An array of player identifiers for the existing squad.
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :return:
    """
    if total_budget <= 0:
        raise Exception("`total_budget` must be positive")

    if first_team_factor + bench_factor != 1.0:
        raise Exception("`first_team_factor` and `bench_factor` must sum to 1.")

    if captain_factor + vice_factor != 1.0:
        raise Exception("`captain_factor` and `vice_factor` must sum to 1.")

    if (not existing_squad and existing_squad != []) or (
        existing_squad and len(existing_squad) != 15
    ):
        raise Exception(
            "`existing_squad` must consist of 15 players or be an empty array"
        )

    if transfer_penalty < 0:
        raise Exception("`transfer_penalty` must be non-negative")

    if transfer_limit not in range(0, 16):
        raise Exception("`transfer_limit` must be an integer between 0 and 15")


def construct_player_position_weights(players):
    """
    Construct a matrix indicating which players are in which positions.
    The matrix consists of a row for each position (4) and a column for each player.
    If a player occupies a position, the corresponding element is 1, otherwise 0.

    :param players: An array of dictionaries of player data
    :return: Matrix of player weights
    """

    player_position_weights = np.zeros((4, len(players)))

    for i, element_type in enumerate(range(1, 5)):
        for j, player in enumerate(players):
            if player["element_type"] == element_type:
                player_position_weights[i, j] = 1
            else:
                player_position_weights[i, j] = 0

    return player_position_weights


def construct_player_team_weights(players):
    """
    Construct a matrix indicating which players belong to which teams.
    The matrix consists of a row for each team (20) and a column for each player.
    If a player belongs to a team, the corresponding element is 1, otherwise 0.

    :param players: An array of dictionaries of player data
    :return: Matrix of player weights
    """

    player_team_weights = np.zeros((20, len(players)))

    for i, element_type in enumerate(range(1, 21)):
        for j, player in enumerate(players):
            if player["team"] == element_type:
                player_team_weights[i, j] = 1
            else:
                player_team_weights[i, j] = 0

    return player_team_weights


def sort_bench(bench, players, optimise_key):
    """
    Sort bench players by keeper first, then descending values of optimise key.

    :param bench: An array of elements for players on the bench
    :param players: An array of dictionaries of player data
    :param optimise_key: The variable to optimise for
    :return: A sorted array of elements
    """

    elements = [
        (i["element"], i["element_type"], i[optimise_key])
        for i in players
        if i["element"] in bench
    ]

    return [
        i[0]
        for i in sorted(
            elements, key=lambda x: (1 if x[1] == 1 else 0, x[2]), reverse=True
        )
    ]


def select_team(
    players,
    optimise_key="predicted_total_points",
    existing_squad=[],
    total_budget=1000,
    first_team_factor=0.9,
    bench_factor=0.1,
    captain_factor=0.9,
    vice_factor=0.1,
    transfer_penalty=4,
    transfer_limit=15,
):
    """
    Select the optimal team of players within constraints.

    :param players: An array of dictionaries of player data
    :param optimise_key: The variable to optimise for
    :param existing_squad: An array of player identifiers for the existing squad.
    :param total_budget: Total budget available, i.e. total team value + bank
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :return: A tuple of arrays for first team, bench, captain and vice and a dict of transfers
    """

    validate_optimisation_arguments(
        total_budget,
        first_team_factor,
        bench_factor,
        captain_factor,
        vice_factor,
        existing_squad,
        transfer_penalty,
        transfer_limit,
    )

    player_elements = np.array([i["element"] for i in players])
    player_points = np.array([i[optimise_key] for i in players])
    player_costs = np.array([[i["value"] for i in players]])

    player_position_weights = construct_player_position_weights(players)
    player_team_weights = construct_player_team_weights(players)

    # vector variables for objective function
    first_team_v = cp.Variable(len(players), boolean=True)
    captain_v = cp.Variable(len(players), boolean=True)
    vice_v = cp.Variable(len(players), boolean=True)
    bench_v = cp.Variable(len(players), boolean=True)
    # existing squad is not a variable that we choose
    # it is a vector of constants we provide
    existing_squad_v = np.array(
        [1.0 if i in existing_squad else 0.0 for i in player_elements]
    )
    num_transfers_v = 15 - existing_squad_v @ (first_team_v + bench_v)

    objective = (
        first_team_factor * player_points @ first_team_v
        + bench_factor * player_points @ bench_v
        + captain_factor * player_points @ captain_v
        + vice_factor * player_points @ vice_v
        - transfer_penalty * num_transfers_v
    )

    constraints = [
        # cost constraint
        player_costs @ (first_team_v + bench_v) <= [total_budget],
        # team constraints
        player_team_weights @ (first_team_v + bench_v) <= [3] * 20,
        # position constraints
        player_position_weights @ (first_team_v + bench_v) == [2, 5, 5, 3],
        player_position_weights @ first_team_v >= [1, 3, 3, 1],
        player_position_weights @ first_team_v <= [1, 5, 5, 3],
        # player number constraints
        np.ones(len(players)) @ first_team_v == 11,
        np.ones(len(players)) @ captain_v == 1,
        np.ones(len(players)) @ vice_v == 1,
        np.ones(len(players)) @ bench_v == 4,
        # selected players not on both first team and bench
        first_team_v + bench_v <= np.ones(len(players)),
        # captain and vice different players
        captain_v + vice_v <= np.ones(len(players)),
        # squad contains captain
        first_team_v + bench_v - captain_v >= np.zeros(len(players)),
        # squad contains vice
        first_team_v + bench_v - vice_v >= np.zeros(len(players)),
        # number of transfers must not exceed limit
        num_transfers_v <= transfer_limit,
    ]

    # solve optimisation problem
    squad_prob = cp.Problem(cp.Maximize(objective), constraints)
    squad_prob.solve(solver="GLPK_MI")

    first_team = get_elements_from_vector(first_team_v.value, player_elements)
    bench = sort_bench(
        get_elements_from_vector(bench_v.value, player_elements), players, optimise_key
    )
    captain = get_elements_from_vector(captain_v.value, player_elements)
    vice = get_elements_from_vector(vice_v.value, player_elements)
    transfers = {
        "transfers_in": set(first_team + bench) - set(existing_squad),
        "transfers_out": set(existing_squad) - set(first_team + bench),
    }

    return (
        first_team,
        bench,
        captain,
        vice,
        transfers,
    )


def get_private_entry_data(entry, authenticated_session):
    """
    Get private entry data using specified credentials.

    Private entry data includes recent squad changes, players prices and bank balance.

    :param entry: Team identifier
    :param authenticated_session: Requests session authenticated with FPL credentials
    :return: Dictionary of private entry data
    """

    logger.info("getting private entry data")
    private_data = authenticated_session.get(
        f"https://fantasy.premierleague.com/api/my-team/{entry}"
    ).json()

    return private_data


def get_public_entry_data(entry):
    """
    Get public entry data.

    Public entry data does not include recent squad changes, players prices and bank balance.

    :param entry: Team identifier
    :return: Dictionary of public entry data
    """

    current_event = get_current_event()
    if current_event == 0:
        raise Exception('No publicly available data before season starts')

    logger.info("getting entry data")
    entry_request = requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/event/{current_event}/picks/"
    )
    public_data = entry_request.json()

    return public_data


def get_sorted_safe_web_names(elements, players, is_sorted=True):
    """
    Get players names for a list of elements and sort by position.

    :param elements: An array of elements
    :param players: An array of dictionaries of player data
    :param is_sorted: Optionally sort by position
    :return: An array of names ordered by position
    """

    if is_sorted:
        return [
            i["safe_web_name"]
            for i in sorted(players, key=lambda x: x["element_type"])
            if i["element"] in elements
        ]
    else:
        return [
            p["safe_web_name"] for e in elements for p in players if e == p["element"]
        ]


def optimise_entry(
    entry,
    total_budget=1000,
    first_team_factor=0.9,
    bench_factor=0.1,
    captain_factor=0.9,
    vice_factor=0.1,
    transfer_penalty=4,
    transfer_limit=15,
    start_event=1,
    end_event=38,
    authenticated_session=None,
):
    """
    Select the optimal team and transfers for a specified entry.

    If credentials are provided, use private entry data.

    :param entry: Team identifier
    :param total_budget: Total budget available, i.e. total team value + bank
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :param start_event: Start of event range to optimiser over
    :param end_event: End of event range to optimiser over
    :param authenticated_session: Requests session authenticated with FPL credentials
    :return: Dictionary of team selection decisions
    """

    logger.info("getting predictions")
    client = set_up_bigquery()
    players = run_templated_query(
        "./footbot/optimiser/sql/optimiser.sql",
        dict(start_event=start_event, end_event=end_event),
        client,
    ).to_dict("records")

    if authenticated_session:
        private_data = get_private_entry_data(entry, authenticated_session)
        existing_squad = [i["element"] for i in private_data["picks"]]
        team_value = np.sum([i["selling_price"] for i in private_data["picks"]])
        bank = private_data["transfers"]["bank"]
        total_budget = team_value + bank

        # update player values with selling prices for players in existing squad
        for player in players:
            for pick in private_data["picks"]:
                if player["element"] == pick["element"]:
                    player["value"] = pick["selling_price"]

    else:
        public_data = get_public_entry_data(entry)
        existing_squad = [i["element"] for i in public_data["picks"]]

    logger.info("optimising team")
    (first_team, bench, captain, vice, transfers,) = select_team(
        players,
        optimise_key="average_points",
        existing_squad=existing_squad,
        total_budget=total_budget,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
    )

    first_team = [p for p in players if p['element'] in first_team]
    bench = [p for p in players if p['element'] in bench]
    captain = [p for p in players if p['element'] in captain]
    vice = [p for p in players if p['element'] in vice]
    transfers_in = [p for p in players if p['element'] in transfers['transfers_in']]
    transfers_out = [p for p in players if p['element'] in transfers['transfers_out']]

    return {
        "first_team": first_team,
        "bench": bench,
        "captain": captain,
        "vice": vice,
        "transfers_in": transfers_in,
        "transfers_out": transfers_out,
    }
