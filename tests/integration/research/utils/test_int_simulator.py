import numpy as np
import pytest

from footbot.data.utils import run_query
from footbot.data.utils import write_to_table
from footbot.research.utils.simulator import get_elements_df
from footbot.research.utils.simulator import get_results_df
from footbot.research.utils.simulator import make_team_selection
from footbot.research.utils.simulator import make_transfers
from footbot.research.utils.simulator import simulate_event
from footbot.research.utils.simulator import simulate_events


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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
        season="1920",
        event=1,
        purchase_price_dict={},
        all_predictions_df=predictions_df,
        first_team=None,
        bench=None,
        bank=None,
        transfers_made=None,
        events_to_look_ahead=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        triple_captain=False,
        bench_boost=False,
        client=client,
    )


def test_simulate_events_save_predictions(client):

    output = simulate_events(
        season=1920,
        events=[1, 2, 3],
        get_predictions_df=get_predictions_df,
        events_to_look_ahead=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        dataset="integration_tests",
        table="test_predictions_save",
        save_new_predictions=True,
        client=client,
    )

    assert output


def test_simulate_events_retrieve_predictions(client):

    events = [1, 2, 3]
    dataset = "integration_tests"
    table = "test_predictions_retrieve"

    simulation_results_arr = simulate_events(
        season=1920,
        events=events,
        get_predictions_df=get_predictions_df,
        events_to_look_ahead=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        dataset=dataset,
        table=table,
        save_new_predictions=False,
        client=client,
    )

    total_event_points = sum(i["event_points"] for i in simulation_results_arr)

    assert total_event_points == 104
