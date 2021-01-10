import os
from pathlib import Path

import numpy as np
import pytest

from footbot.data.utils import run_query
from footbot.data.utils import set_up_bigquery
from footbot.data.utils import write_to_table
from footbot.research.utils.simulator import get_elements_df
from footbot.research.utils.simulator import get_results_df
from footbot.research.utils.simulator import make_team_selection
from footbot.research.utils.simulator import make_transfers
from footbot.research.utils.simulator import simulate_event
from footbot.research.utils.simulator import simulate_events


@pytest.fixture
def client():
    secrets_path = os.path.join(
        Path(__file__).parents[4], "secrets/service_account.json"
    )
    return set_up_bigquery(secrets_path)


@pytest.fixture
def elements_df(client):
    return get_elements_df("1920", 1, client)


def test_get_elements_df(elements_df):

    assert set(elements_df.columns) == {"element_all", "element_type", "team", "value"}
    assert len(elements_df) == 558
    assert len(elements_df["element_all"]) == len(
        elements_df["element_all"].drop_duplicates()
    )


def test_get_results_df(client):
    df = get_results_df("1920", 1, client)

    assert set(df.columns) == {"element_all", "minutes", "total_points"}
    assert len(df) == 525
    assert len(df["element_all"]) == len(df["element_all"].drop_duplicates())


def get_predictions_df(season, event, client):

    predictions_df = get_elements_df(season, event, client)
    predictions_df = predictions_df.drop(columns=["element_type", "team", "value"])
    predictions_df["event"] = event
    predictions_df["prediction_event"] = event
    predictions_df["predicted_total_points"] = np.random.normal(
        size=len(predictions_df)
    )

    return predictions_df


@pytest.fixture
def predictions_df(client):

    predictions_df = get_predictions_df("1920", 1, client)

    return predictions_df


def test_make_transfers_from_scratch(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [],
        1000,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        15,
        predictions_df,
        elements_df,
    )

    assert existing_squad != []


def test_make_transfers_from_existing(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [163, 112, 1331, 281, 965, 1176, 1417, 1141, 514, 1439, 282, 1210, 127, 417, 5],
        1000,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        1,
        predictions_df,
        elements_df,
    )

    assert existing_squad != []


def test_make_team_selection(elements_df, predictions_df):

    first_team, bench, captain, vice = make_team_selection(
        1,
        [163, 112, 1331, 281, 965, 1176, 1417, 1141, 514, 1439, 282, 1210, 127, 417, 5],
        1000,
        0.9,
        0.1,
        0.9,
        0.1,
        predictions_df,
        elements_df,
    )

    assert first_team != []
    assert bench != []
    assert captain != []
    assert vice != []


def test_simulate_event(predictions_df, client):

    simulate_event(
        "1920",
        1,
        {},
        predictions_df,
        None,
        None,
        None,
        None,
        0,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        1,
        False,
        False,
        client,
    )


def test_simulate_events_save_predictions(client):

    simulate_events(
        1920,
        [1, 2, 3],
        get_predictions_df,
        0,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        1,
        "integration_tests",
        "test_predictions_save",
        True,
        client,
    )


def test_simulate_events_retrieve_predictions(client):

    events = [1, 2, 3]
    dataset = "integration_tests"
    table = "test_predictions_retrieve"

    run_query(f"DELETE FROM `footbot-001.{dataset}.{table}` WHERE true", client)

    for event in events:
        df = get_predictions_df("1920", event, client)
        write_to_table(
            dataset,
            table,
            df,
            client,
        )

    simulate_events(
        1920,
        events,
        get_predictions_df,
        0,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        1,
        dataset,
        table,
        False,
        client,
    )