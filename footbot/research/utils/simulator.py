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


def get_all_elements_df(season, client):
    """
    Gets position, price and team data for players for a given season.
    :param season: Gameweek season
    :param client: BigQuery client
    :return: Dataframe of player metadata
    """

    sql_template_path = os.path.join(Path(__file__).parents[0], "all_elements_data.sql")

    df = run_templated_query(sql_template_path, dict(season=season), client)

    return df


def get_all_results_df(season, client):
    """
    Gets points and minutes data for players for a given season.
    :param season: Gameweek season
    :param client: BigQuery client
    :return: Dataframe of points and minutes data by player
    """

    sql_template_path = os.path.join(Path(__file__).parents[0], "all_results_data.sql")

    df = run_templated_query(sql_template_path, dict(season=season), client)

    return df


def aggregate_predictions(predictions_df, start_event, end_event, weight):
    """
    Calculates weighted sum of point predictions for multiple gameweeks.
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param start_event: First gameweek event
    :param end_event: Last gameweek event
    :param weight: weight for exponential decay of points
    :return: Dataframe of points predictions by player
    """

    predictions_df = predictions_df.copy()
    predictions_df = predictions_df.loc[
        predictions_df["event"].between(start_event, end_event), :
    ]

    predictions_df["weight"] = weight ** (predictions_df["event"] - start_event)

    predictions_df["predicted_total_points"] = (
        predictions_df["predicted_total_points"] * predictions_df["weight"]
    )

    predictions_df = predictions_df.groupby(["element_all"], as_index=False)[
        ["predicted_total_points"]
    ].sum()

    return predictions_df


def get_team_selector_input(
    predictions_df, elements_df, start_event, end_event, weight
):
    """
    Get input for team selector.
    :param predictions_df: Dataframe of points predictions by player, gameweek
    :param elements_df: Dataframe of player metadata
    :param start_event: First gameweek event
    :param end_event: Last gameweek event
    :param weight: weight for exponential decay of points
    :return: Array of dicts of predicted points and player data
    """

    agg_predictions_df = aggregate_predictions(
        predictions_df, start_event, end_event, weight
    )

    players_df = elements_df.join(
        agg_predictions_df.set_index("element_all"),
        on="element_all",
    )

    # we may not make predictions for all players
    players_df["predicted_total_points"] = players_df["predicted_total_points"].fillna(
        0
    )

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
    weight,
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
    :param weight: weight for exponential decay of points
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
        predictions_df, elements_df, event, event + events_to_look_ahead, weight
    )

    first_team, bench, _, _, transfers = select_team(
        players,
        optimise_key="predicted_total_points",
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
    players = get_team_selector_input(
        predictions_df, elements_df, event, event, weight=1.0
    )

    first_team, bench, captain, vice, _ = select_team(
        players,
        optimise_key="predicted_total_points",
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


def make_new_predictions_event(
    season, event, get_predictions_df, client
):
    logger.info(f"making predictions as of event {event}")
    predictions_df = get_predictions_df(season, event, client)
    predictions_df["prediction_event"] = event

    return predictions_df



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
        predictions_df = make_new_predictions_event(season, event, get_predictions_df, client)
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


def validate_all_predictions_df(all_predictions_df):
    """
    Check for duplicate predictions.
    :param all_predictions_df: Dataframe of points predictions by player, gameweek, prediction event
    :return: None
    """

    distinct_entries = len(
        all_predictions_df[
            [
                "prediction_event",
                "event",
                "element_all",
                "opponent_team",
            ]
        ].drop_duplicates()
    )

    if len(all_predictions_df) != distinct_entries:
        raise Exception("`all_predictions_df` contains duplicate entries")


def simulate_event(
    *,
    event,
    purchase_price_dict,
    all_elements_df,
    all_predictions_df,
    all_results_df,
    existing_squad,
    bank,
    transfers_made,
    events_to_look_ahead,
    weight,
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
):
    """
    Simulate a specified gameweek.
    :param event: Gameweek event
    :param purchase_price_dict: Dictionary of purchase prices of players in the squad
    :param all_elements_df: Dataframe of player data by player, gameweek
    :param all_predictions_df: Dataframe of points predictions by player, gameweek, prediction event
    :param all_results_df: Dataframe of results by player, gameweek
    :param existing_squad: Array of elements representing squad from previous gameweek simulation
    :param bank: Budget in bank
    :param transfers_made: Number of transfers made in previous gameweek
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param weight: weight for exponential decay of points
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
    :return: Simulation outcomes
    """

    elements_df = all_elements_df.copy()
    elements_df = elements_df.loc[elements_df["event"] == event, :]
    elements_df = elements_df.drop(columns=["event"])
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
        weight=weight,
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

    results_df = all_results_df.copy()
    results_df = results_df.loc[results_df["event"] == event, :]
    results_df = results_df.drop(columns=["event"])

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
    events,
    all_elements_df,
    all_predictions_df,
    all_results_df,
    events_to_look_ahead,
    weight,
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
):
    """
    Simulate multiple gameweeks.
    :param events: Gameweek events
    :param all_elements_df: Dataframe of player data by player, gameweek
    :param all_predictions_df: Dataframe of points predictions by player, gameweek, prediction event
    :param all_results_df: Dataframe of results by player, gameweek
    :param events_to_look_ahead: Number of future gameweeks to consider
    :param weight: weight for exponential decay of points
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
    :return: Simulation outcomes
    """

    if events[0] != 1:
        raise Exception("simulation must start at event 1")

    all_elements_df = all_elements_df.copy()

    validate_all_predictions_df(all_predictions_df)
    all_predictions_df = all_predictions_df.copy()

    all_results_df = all_results_df.copy()

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
            event=event,
            purchase_price_dict=purchase_price_dict,
            all_elements_df=all_elements_df,
            all_predictions_df=all_predictions_df,
            all_results_df=all_results_df,
            existing_squad=first_team + bench,
            bank=bank,
            transfers_made=transfers_made,
            events_to_look_ahead=events_to_look_ahead,
            weight=weight,
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
