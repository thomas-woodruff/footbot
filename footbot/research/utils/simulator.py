import os
from pathlib import Path

from footbot.data.utils import run_templated_query
from footbot.data.utils import set_up_bigquery
from footbot.research.utils.price_changes import calculate_team_value


def get_element_data(season, event, client):

    sql_template_path = os.path.join(Path(__file__).parents[0], "element_data.sql")

    df = run_templated_query(
        sql_template_path, dict(season=season, event=event), client
    )

    return df


def get_results_data(season, event, client):

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


def get_team_selector_input(predictions_df, element_data_df, start_event, end_event):
    agg_predictions_df = aggregate_predictions(predictions_df, start_event, end_event)

    players_df = element_data_df.join(
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


def set_event_state(event, first_team, bench, bank, transfers_made, element_data_df):
    if event == 1:
        existing_squad_elements = None
        total_budget = 1000
        free_transfers_available = 1
    else:
        existing_squad_elements = first_team + bench
        team_value = calculate_team_value(first_team + bench, element_data_df)
        total_budget = team_value + bank
        free_transfers_available = 2 if transfers_made == 0 else 1

    event_state = dict(
        existing_squad_elements=existing_squad_elements,
        total_budget=total_budget,
        free_transfers_available=free_transfers_available,
    )

    return event_state
