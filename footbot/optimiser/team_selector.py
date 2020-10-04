import json
import logging

import cvxpy as cp
import numpy as np
import pandas as pd
import requests

from footbot.data import utils

logger = logging.getLogger(__name__)


def select_team(
    players,
    total_budget=1000,
    optimise_key="predicted_total_points",
    captain_factor=1,
    vice_factor=0.5,
    bench_factor=0.1,
    existing_squad_elements=None,
    transfer_penalty=4,
    transfer_limit=15,
):
    """
    solve team selection from scratch
    players is an array of dicts
    """

    # munge player data
    player_elements = np.array([i["element"] for i in players])
    player_points = np.array([i[optimise_key] for i in players])
    player_costs = np.array([[i["value"] for i in players]])
    player_position = np.array([i["element_type"] for i in players])
    player_club = np.array([i["team"] for i in players])

    if existing_squad_elements:
        existing_squad = np.array(
            [1 if i in existing_squad_elements else 0 for i in player_elements]
        )

        if sum(existing_squad) != 15:
            raise Exception

    # weight matrix for player positions
    player_position_weights = np.zeros((4, len(players)))
    for i in range(0, 4):
        for j in range(0, len(players)):
            if player_position[j] == i + 1:
                player_position_weights[i, j] = 1
            else:
                player_position_weights[i, j] = 0

    # weight matrix for player clubs
    player_club_weights = np.zeros((20, len(players)))
    for i in range(0, 20):
        for j in range(0, len(players)):
            if player_club[j] == i + 1:
                player_club_weights[i, j] = 1
            else:
                player_club_weights[i, j] = 0

    # overall weight matrix
    player_weights = np.concatenate((player_costs, player_club_weights), axis=0)

    # capacity vector
    squad_cost_capacity = [total_budget]
    squad_club_capacity = [3] * 20
    squad_capacity = np.array(squad_cost_capacity + squad_club_capacity)

    # variables for objective function
    first_team = cp.Variable(len(players), boolean=True)
    captain = cp.Variable(len(players), boolean=True)
    vice = cp.Variable(len(players), boolean=True)
    bench = cp.Variable(len(players), boolean=True)

    # objective function (no existing squad)
    objective = (
        player_points @ first_team
        + captain_factor * player_points @ captain
        + vice_factor * player_points @ vice
        + bench_factor * player_points @ bench
    )

    # optimisation constraints (no existing squad)
    constraints = [
        # cost and club constraints
        player_weights @ (first_team + bench) <= squad_capacity,
        # position constraints
        player_position_weights @ (first_team + bench) == [2, 5, 5, 3],
        player_position_weights @ first_team >= [1, 3, 3, 1],
        player_position_weights @ first_team <= [1, 5, 5, 3],
        # player number constraints
        np.ones(len(players)) @ first_team == 11,
        np.ones(len(players)) @ captain == 1,
        np.ones(len(players)) @ vice == 1,
        np.ones(len(players)) @ bench == 4,
        # selected players not on both first team and bench
        first_team + bench <= np.ones(len(players)),
        # squad contains captain
        first_team + bench - captain >= np.zeros(len(players)),
        # captain and vice different players
        captain + vice <= np.ones(len(players)),
        # squad contains vice
        first_team + bench - vice >= np.zeros(len(players)),
    ]

    # update objective function and constraints if existing squad
    if existing_squad_elements:
        objective = objective - transfer_penalty * (
            15 - existing_squad @ (first_team + bench)
        )

        constraints.append(15 - existing_squad @ (first_team + bench) <= transfer_limit)

    # optimisation problem
    squad_prob = cp.Problem(cp.Maximize(objective), constraints)

    # solve optimisation problem
    squad_prob.solve(solver="GLPK_MI")

    # get first team elements
    first_team_selection = [int(round(j)) for j in first_team.value]
    first_team_selection_indices = [
        i for i, j in enumerate(first_team_selection) if j == 1
    ]
    first_team_selection_elements = list(player_elements[first_team_selection_indices])
    # get captain element
    captain_selection = [int(round(j)) for j in captain.value]
    captain_selection_indices = [i for i, j in enumerate(captain_selection) if j == 1]
    captain_selection_elements = list(player_elements[captain_selection_indices])

    vice_selection = [int(round(j)) for j in vice.value]
    vice_selection_indices = [i for i, j in enumerate(vice_selection) if j == 1]
    vice_selection_elements = list(player_elements[vice_selection_indices])

    # get bench elements
    bench_selection = [int(round(j)) for j in bench.value]
    bench_selection_indices = [i for i, j in enumerate(bench_selection) if j == 1]
    bench_selection_elements = list(player_elements[bench_selection_indices])

    if existing_squad_elements:
        transfers = {
            "transfers_in": set(
                first_team_selection_elements + bench_selection_elements
            )
            - set(existing_squad_elements),
            "transfers_out": set(existing_squad_elements)
            - set(first_team_selection_elements + bench_selection_elements),
        }
    else:
        transfers = {"transfers_in": set(), "transfers_out": set()}

    return (
        first_team_selection_elements,
        captain_selection_elements,
        vice_selection_elements,
        bench_selection_elements,
        transfers,
    )


def optimise_entry(
    entry,
    total_budget=1000,
    bench_factor=0.1,
    transfer_penalty=4,
    transfer_limit=15,
    start_event=1,
    end_event=38,
    private=False,
):
    """
    optimise a given entry based on their picks
    for the current event
    """

    logger.info("getting current event")
    bootstrap_request = requests.get(
        "https://fantasy.premierleague.com/api/bootstrap-static/"
    )
    bootstrap_data = bootstrap_request.json()

    # if no events are current, current event is zero
    # season has yet to start
    current_event = 0
    for event in [i for i in bootstrap_data["events"] if i["is_current"]]:
        # otherwise, take event id of event that is current
        current_event = event["id"]

    logger.info("getting entry data")
    entry_request = requests.get(
        f"https://fantasy.premierleague.com/api/entry/{entry}/event/{current_event}/picks/"
    )
    entry_data = entry_request.json()
    existing_squad_elements = [i["element"] for i in entry_data["picks"]]

    with open("./footbot/optimiser/sql/optimiser.sql", "r") as sql_file:
        sql = sql_file.read()

    logger.info("getting predictions")
    client = utils.set_up_bigquery()
    df = utils.run_query(
        sql.format(start_event=start_event, end_event=end_event), client
    )

    if private:
        session = requests.session()

        with open("./secrets/fpl_login.json") as secrets_file:
            secrets = json.loads(secrets_file.read())

        payload = {
            "redirect_uri": "https://fantasy.premierleague.com/a/login",
            "app": "plfpl-web",
        }
        payload.update(secrets)
        logger.info("authenticating for entry")
        session.post("https://users.premierleague.com/accounts/login/", data=payload)

        logger.info("getting private entry data")
        private_data = session.get(
            f"https://fantasy.premierleague.com/api/my-team/{entry}"
        ).json()
        private_df = pd.DataFrame(private_data["picks"])[["element", "selling_price"]]

        existing_squad_elements = list(private_df["element"].values)

        total_budget = private_df["selling_price"].sum()

        df = df.join(private_df.set_index("element"), on="element")
        df["value"] = df["selling_price"].fillna(df["value"])
        df = df.drop("selling_price", axis=1)

    players = df.to_dict("records")

    logger.info("optimising team")
    (
        first_team_selection_elements,
        captain_selection_elements,
        vice_selection_elements,
        bench_selection_elements,
        transfers,
    ) = select_team(
        players,
        optimise_key="average_points",
        total_budget=total_budget,
        bench_factor=bench_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
        existing_squad_elements=existing_squad_elements,
    )

    first_team = list(
        df[df["element"].isin(first_team_selection_elements)]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    captain = list(
        df[df["element"].isin(captain_selection_elements)]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    vice = list(
        df[df["element"].isin(vice_selection_elements)]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    bench = list(
        df[df["element"].isin(bench_selection_elements)]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    transfers_in = list(
        df[df["element"].isin(transfers["transfers_in"])]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    transfers_out = list(
        df[df["element"].isin(transfers["transfers_out"])]
        .sort_values("element_type")["safe_web_name"]
        .values
    )

    return {
        "first_team": first_team,
        "captain": captain,
        "vice": vice,
        "bench": bench,
        "transfers_in": transfers_in,
        "transfers_out": transfers_out,
    }
