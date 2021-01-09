import os
from pathlib import Path

from footbot.data.utils import run_templated_query
from footbot.optimiser.team_selector import select_team
from footbot.research.utils.price_changes import calculate_team_value
from footbot.research.utils.price_changes import (
    update_player_values_with_selling_prices,
)


def get_elements_df(season, event, client):

    sql_template_path = os.path.join(Path(__file__).parents[0], "element_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def get_results_df(season, event, client):

    sql_template_path = os.path.join(Path(__file__).parents[0], "results_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def aggregate_predictions(predictions_df, start_event, end_event):

    num_events = end_event - start_event + 1

    predictions_df = predictions_df.copy()
    predictions_df = predictions_df[
        predictions_df["event"].between(start_event, end_event)
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

    first_team_dict = results_df.loc[
        results_df["element_all"].isin(first_team), :
    ].to_dict(orient="records")
    bench_dict = results_df.loc[results_df["element_all"].isin(bench), :].to_dict(
        orient="records"
    )

    return first_team_dict, bench_dict


def set_event_state(event, first_team, bench, bank, transfers, elements_df):
    if event == 1:
        existing_squad = None
        total_budget = 1000
        free_transfers_available = 1
    else:
        existing_squad = first_team + bench
        team_value = calculate_team_value(first_team + bench, elements_df)
        total_budget = team_value + bank
        free_transfers_available = 2 if len(transfers["transfers_in"]) == 0 else 1

    return existing_squad, total_budget, free_transfers_available


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


def simulate_event(
    season,
    event,
    purchase_price_dict,
    get_predictions_df,
    first_team,
    bench,
    bank,
    transfers,
    events_to_look_ahead,
    first_team_factor,
    bench_factor,
    captain_factor,
    vice_factor,
    transfer_penalty,
    transfer_limit,
    client,
):

    elements_df = get_elements_df(season, event, client)
    update_player_values_with_selling_prices(elements_df, purchase_price_dict)

    predictions_df = get_predictions_df(season, event, client)

    existing_squad, total_budget, free_transfers_available = set_event_state(
        event, first_team, bench, bank, transfers, elements_df
    )

    existing_squad, bank, transfers = make_transfers(
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
    )

    first_team, bench, captain, vice = make_team_selection(
        event,
        existing_squad,
        total_budget,
        first_team_factor,
        bench_factor,
        captain_factor,
        vice_factor,
        predictions_df,
        elements_df,
    )

    results_df = get_results_df(season, event, client)

    # make subs
    # first_team_dict =

    # calculate points
    # return transfers, selections, points and anything else (state)
