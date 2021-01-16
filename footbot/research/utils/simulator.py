import logging
import os
from pathlib import Path

import pandas as pd

from footbot.data.utils import run_templated_query
from footbot.data.utils import write_to_table
from footbot.optimiser.team_selector import select_team
from footbot.research.utils.calculate_points import calculate_points
from footbot.research.utils.price_changes import calculate_team_value
from footbot.research.utils.price_changes import (
    update_player_values_with_selling_prices,
)
from footbot.research.utils.subs import make_subs
from footbot.research.utils.subs import pick_captain

logger = logging.getLogger(__name__)


def get_elements_df(season, event, client):
    """
    Gets position, price and team data for players for a given gameweek.
    :param season: Gameweek season
    :param event: Gameweek event
    :param client: BigQuery client
    :return: Dataframe of player metadata
    """

    sql_template_path = os.path.join(Path(__file__).parents[0], "element_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def get_results_df(season, event, client):
    """
    Gets points and minutes data for players for a given gameweek.
    :param season: Gameweek season
    :param event: Gameweek event
    :param client: BigQuery client
    :return: Dataframe of points and minutes data by player
    """

    sql_template_path = os.path.join(Path(__file__).parents[0], "results_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def aggregate_predictions(predictions_df, start_event, end_event):
    """
    Averages point predictions for multiple gameweeks.
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param start_event: First gameweek event
    :param end_event: Last gameweek event
    :return: Dataframe of points predictions by player
    """

    num_events = end_event - start_event + 1

    predictions_df = predictions_df.copy()
    predictions_df = predictions_df.loc[
        predictions_df["event"].between(start_event, end_event), :
    ]

    predictions_df = predictions_df.groupby(["element_all"], as_index=False)[
        ["predicted_total_points"]
    ].sum()

    predictions_df["avg_predicted_total_points"] = (
        predictions_df["predicted_total_points"] / num_events
    )
    predictions_df = predictions_df.drop(["predicted_total_points"], axis=1)

    return predictions_df


def get_team_selector_input(predictions_df, elements_df, start_event, end_event):
    """
    Get input for team selector.
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param elements_df: Dataframe of player metadata
    :param start_event: First gameweek event
    :param end_event: Last gameweek event
    :return: Array of dicts of predicted points and player data
    """

    agg_predictions_df = aggregate_predictions(predictions_df, start_event, end_event)

    players_df = elements_df.join(
        agg_predictions_df.set_index("element_all"),
        on="element_all",
    )

    # we may not make predictions for all players
    players_df["avg_predicted_total_points"] = players_df[
        "avg_predicted_total_points"
    ].fillna(0)

    # team selector expects "element" instead of "element_all"
    players_df = players_df.rename(columns={"element_all": "element"})

    players = players_df.to_dict(orient="records")

    return players


def get_points_calculator_input(
    results_df, elements_df, first_team, bench, captain, vice
):
    """
    Get input for points calculation.
    :param results_df: Dataframe of points and minutes data by player
    :param elements_df: Dataframe of player metadata
    :param first_team: Array of elements representing first team
    :param bench: Array of elements representing bench
    :param captain: Array of elements representing captain
    :param vice: Array of elements representing vice
    :return: Array of dicts representing first team, bench
    """

    results_df = elements_df.join(
        results_df.set_index("element_all"),
        on="element_all",
    )

    # fill in minutes and total_points for players missing from results_df
    # e.g. players that don't have fixtures in that event
    results_df = results_df.fillna(0)

    results_df = results_df.drop(columns=["team", "value"])

    results_df["is_captain"] = results_df["element_all"].apply(
        lambda x: x == captain[0]
    )
    results_df["is_vice"] = results_df["element_all"].apply(lambda x: x == vice[0])

    first_team_dicts = results_df.loc[
        results_df["element_all"].isin(first_team), :
    ].to_dict(orient="records")
    bench_dicts = results_df.loc[results_df["element_all"].isin(bench), :].to_dict(
        orient="records"
    )

    return first_team_dicts, bench_dicts


def set_event_state(
    event,
    existing_squad,
    bank,
    transfers_made,
    wildcard_events,
    free_hit_events,
    existing_squad_revert,
    triple_captain_events,
    bench_boost_events,
    events_to_look_ahead,
    events_to_look_ahead_from_scratch,
    events_to_look_ahead_wildcard,
    transfer_penalty,
    transfer_limit,
    elements_df,
):
    """
    Set simulator variables based on previous gameweek simulations.
    :param event: Gameweek event
    :param existing_squad: Array of elements representing first team and bench
    :param bank: Budget in bank
    :param transfers_made: Number of transfers made in previous gameweek
    :param wildcard_events: Array of events on which to play wildcard chips
    :param events_to_look_ahead_wildcard: Number of future gameweeks to consider when using
    wildcard chip
    :param free_hit_events: Array of events on which to play free hit chips
    :param existing_squad_revert: Array of elements representing squad to revert to
    :param triple_captain_events: Array of events on which to play triple captain chips
    :param bench_boost_events: Array of events on which to play bench boost chips
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param events_to_look_ahead_from_scratch: Number of future gameweeks to consider when choosing
    team from scratch
    :param events_to_look_ahead_wildcard: Number of future gameweeks to consider when using
    wildcard chip
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :param elements_df: Dataframe of player metadata
    :return: Simulator variables for current simulation
    """

    if event == 1:
        total_budget = 1000
        free_transfers_available = 15
        existing_squad = []
        events_to_look_ahead = events_to_look_ahead_from_scratch
        transfer_limit = 15
        transfer_penalty = 0
    else:
        team_value = calculate_team_value(existing_squad, elements_df)
        total_budget = team_value + bank
        free_transfers_available = 2 if transfers_made == 0 else 1

    if event in wildcard_events:
        if event == 1:
            raise Exception("wildcard chip cannot be played on first event")
        free_transfers_available = 15
        events_to_look_ahead = events_to_look_ahead_wildcard
        transfer_limit = 15
        transfer_penalty = 0

    if event in free_hit_events:
        if event == 1:
            raise Exception("free hit chip cannot be played on first event")
        free_transfers_available = 15
        events_to_look_ahead = 0
        existing_squad_revert = existing_squad.copy()
        transfer_limit = 15
        transfer_penalty = 0

    if event - 1 in free_hit_events:
        existing_squad = existing_squad_revert.copy()
        existing_squad_revert = []

    if event in triple_captain_events:
        triple_captain = True
    else:
        triple_captain = False

    if event in bench_boost_events:
        bench_boost = True
    else:
        bench_boost = False

    return (
        existing_squad,
        total_budget,
        free_transfers_available,
        existing_squad_revert,
        triple_captain,
        bench_boost,
        events_to_look_ahead,
        transfer_penalty,
        transfer_limit,
    )


def make_transfers(
    event,
    events_to_look_ahead,
    existing_squad,
    total_budget,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    transfer_penalty,
    transfer_limit,
    predictions_df,
    elements_df,
):
    """
    Make transfers for current gameweek simulation.
    :param event: Current gameweek event
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param existing_squad: Array of elements representing existing squad
    :param total_budget: Total budget available, i.e. total team value + bank
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param elements_df: Dataframe of player metadata
    :return: Outcome of transfer decisions
    """

    players = get_team_selector_input(
        predictions_df, elements_df, event, event + events_to_look_ahead
    )

    first_team, bench, _, _, transfers = select_team(
        players,
        optimise_key="avg_predicted_total_points",
        existing_squad=existing_squad,
        total_budget=total_budget,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
    )

    existing_squad = first_team + bench

    team_value = calculate_team_value(first_team + bench, elements_df)

    bank = total_budget - team_value

    return existing_squad, bank, transfers


def make_team_selection(
    event,
    existing_squad,
    total_budget,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    predictions_df,
    elements_df,
):
    """
    Make team selection for current gameweek simulation, i.e. first team, bench, captain and vice.
    :param event: Current gameweek event
    :param existing_squad: Array of elements representing existing squad
    :param total_budget: Total budget available, i.e. total team value + bank
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param elements_df: Dataframe of player metadata
    :return: Outcome of team selection decisions
    """
    players = get_team_selector_input(predictions_df, elements_df, event, event)

    first_team, bench, captain, vice, _ = select_team(
        players,
        optimise_key="avg_predicted_total_points",
        existing_squad=existing_squad,
        total_budget=total_budget,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        transfer_penalty=0,
        transfer_limit=0,
    )

    return first_team, bench, captain, vice


def make_new_predictions(
    season, events, get_predictions_df, dataset, table, save_new_predictions, client
):
    """
    Retrieve existing predictions from BigQuery or make new ones and save them to BigQuery.
    :param season: Gameweek season
    :param events: Gameweek events
    :param get_predictions_df: Function to make predictions
    :param dataset: BigQuery dataset to write to
    :param table: BigQuery table to write to
    :param save_new_predictions: Boolean indicating whether new predictions should be saved
    :param client: BigQuery client
    :return: Dataframe of points predictions by player, gameweek, prediction event
    """

    predictions_df_arr = []

    for event in events:
        logger.info(f"writing predictions as of event {event}")

        predictions_df = get_predictions_df(season, event, client)

        predictions_df["prediction_event"] = event

        predictions_df_arr.append(predictions_df)

    all_predictions_df = pd.concat(predictions_df_arr).reset_index(drop=True)

    if save_new_predictions:
        write_to_table(
            dataset,
            table,
            all_predictions_df,
            client,
            truncate_table=True,
        )

    return all_predictions_df


def simulate_event(
    *,
    season,
    event,
    purchase_price_dict,
    all_predictions_df,
    existing_squad,
    bank,
    transfers_made,
    events_to_look_ahead,
    events_to_look_ahead_from_scratch,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    transfer_penalty,
    transfer_limit,
    wildcard_events,
    events_to_look_ahead_wildcard,
    free_hit_events,
    existing_squad_revert,
    triple_captain_events,
    bench_boost_events,
    client,
):
    """
    Simulate a specified gameweek.
    :param season: Gameweek season
    :param event: Gameweek event
    :param purchase_price_dict: Dictionary of purchase prices of players in the squad
    :param all_predictions_df: Dataframe of points predictions by player, gameweek, prediction event
    :param existing_squad: Array of elements representing squad from previous gameweek simulation
    :param bank: Budget in bank
    :param transfers_made: Number of transfers made in previous gameweek
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param events_to_look_ahead_from_scratch: Number of future gameweeks to consider when choosing
    team from scratch
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :param wildcard_events: Array of events on which to play wildcard chips
    :param events_to_look_ahead_wildcard: Number of future gameweeks to consider when using
    wildcard chip
    :param free_hit_events: Array of events on which to play free hit chips
    :param existing_squad_revert: Array of elements representing squad to revert to
    :param triple_captain_events: Array of events on which to play triple captain chips
    :param bench_boost_events: Array of events on which to play bench boost chips
    :param client: BigQuery client
    :return: Simulation outcomes
    """

    elements_df = get_elements_df(season, event, client)
    update_player_values_with_selling_prices(elements_df, purchase_price_dict)

    predictions_df = all_predictions_df.copy()
    predictions_df = predictions_df.loc[predictions_df["prediction_event"] == event, :]

    (
        existing_squad,
        total_budget,
        free_transfers_available,
        existing_squad_revert,
        triple_captain,
        bench_boost,
        events_to_look_ahead,
        transfer_penalty,
        transfer_limit,
    ) = set_event_state(
        event=event,
        existing_squad=existing_squad,
        bank=bank,
        transfers_made=transfers_made,
        wildcard_events=wildcard_events,
        free_hit_events=free_hit_events,
        existing_squad_revert=existing_squad_revert,
        triple_captain_events=triple_captain_events,
        bench_boost_events=bench_boost_events,
        events_to_look_ahead=events_to_look_ahead,
        events_to_look_ahead_from_scratch=events_to_look_ahead_from_scratch,
        events_to_look_ahead_wildcard=events_to_look_ahead_wildcard,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
        elements_df=elements_df,
    )

    existing_squad, bank, transfers = make_transfers(
        event=event,
        events_to_look_ahead=events_to_look_ahead,
        existing_squad=existing_squad,
        total_budget=total_budget,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        transfer_penalty=transfer_penalty,
        transfer_limit=transfer_limit,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )
    transfers_made = len(transfers["transfers_in"])

    first_team, bench, captain, vice = make_team_selection(
        event=event,
        existing_squad=existing_squad,
        total_budget=total_budget,
        first_team_factor=first_team_factor,
        bench_factor=bench_factor,
        captain_factor=captain_factor,
        vice_factor=vice_factor,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    results_df = get_results_df(season, event, client)

    first_team_dicts, bench_dicts = get_points_calculator_input(
        results_df, elements_df, first_team, bench, captain, vice
    )
    first_team_dicts = pick_captain(first_team_dicts)
    first_team_dicts, bench_dicts = make_subs(first_team_dicts, bench_dicts)

    event_points = calculate_points(
        first_team_dicts=first_team_dicts,
        bench_dicts=bench_dicts,
        transfers_made=transfers_made,
        free_transfers_available=free_transfers_available,
        triple_captain=triple_captain,
        bench_boost=bench_boost,
    )

    return (
        event_points,
        first_team,
        bench,
        captain,
        vice,
        transfers,
        bank,
        transfers_made,
        existing_squad_revert,
        predictions_df,
        results_df,
        elements_df,
    )


def simulate_events(
    *,
    season,
    events,
    all_predictions_df,
    events_to_look_ahead,
    events_to_look_ahead_from_scratch,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    transfer_penalty,
    transfer_limit,
    wildcard_events,
    events_to_look_ahead_wildcard,
    free_hit_events,
    triple_captain_events,
    bench_boost_events,
    client,
):
    """
    Simulate multiple gameweeks.
    :param season: Gameweek season
    :param events: Gameweek events
    :param all_predictions_df: Dataframe of points predictions by player, gameweek, prediction event
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param events_to_look_ahead_from_scratch: Number of future gameweeks to consider when choosing
    team from scratch
    :param first_team_factor: The probability a player on the first team will play
    :param bench_factor: The probability a player on the bench will play
    :param captain_factor: The probability the captain will play
    :param vice_factor: The probability the captain will not play
    :param transfer_penalty: The cost in points of transferring a player
    :param transfer_limit: The limit to the number of transfers that can be made
    :param wildcard_events: Array of events on which to play wildcard chips
    :param events_to_look_ahead_wildcard: Number of future gameweeks to consider when using
    wildcard chip
    :param free_hit_events: Array of events on which to play free hit chips
    :param triple_captain_events: Array of events on which to play triple captain chips
    :param bench_boost_events: Array of events on which to play bench boost chips
    :param client: BigQuery client
    :return: Simulation outcomes
    """

    if events[0] != 1:
        raise Exception("simulation must start at event 1")

    all_predictions_df = all_predictions_df.copy()

    purchase_price_dict = {}
    first_team = []
    bench = []
    bank = None
    transfers_made = None
    existing_squad_revert = []

    simulation_results_arr = []

    for event in events:

        logger.info(f"simulating event {event}")

        (
            event_points,
            first_team,
            bench,
            captain,
            vice,
            transfers,
            bank,
            transfers_made,
            existing_squad_revert,
            predictions_df,
            results_df,
            elements_df,
        ) = simulate_event(
            season=season,
            event=event,
            purchase_price_dict=purchase_price_dict,
            all_predictions_df=all_predictions_df,
            existing_squad=first_team + bench,
            bank=bank,
            transfers_made=transfers_made,
            events_to_look_ahead=events_to_look_ahead,
            events_to_look_ahead_from_scratch=events_to_look_ahead_from_scratch,
            first_team_factor=first_team_factor,
            bench_factor=bench_factor,
            captain_factor=captain_factor,
            vice_factor=vice_factor,
            transfer_penalty=transfer_penalty,
            transfer_limit=transfer_limit,
            wildcard_events=wildcard_events,
            events_to_look_ahead_wildcard=events_to_look_ahead_wildcard,
            free_hit_events=free_hit_events,
            existing_squad_revert=existing_squad_revert,
            triple_captain_events=triple_captain_events,
            bench_boost_events=bench_boost_events,
            client=client,
        )

        simulation_results_arr.append(
            {
                "event": event,
                "event_points": event_points,
                "first_team": first_team,
                "bench": bench,
                "captain": captain,
                "vice": vice,
                "transfers": transfers,
                "bank": bank,
                "transfers_made": transfers_made,
                "predictions_df": predictions_df,
                "results_df": results_df,
                "elements_df": elements_df,
            }
        )

    return simulation_results_arr
