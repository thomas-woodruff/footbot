import pandas as pd
import pytest

from footbot.data.utils import run_query
from footbot.research.utils.simulator import get_all_elements_df
from footbot.research.utils.simulator import get_all_results_df
from footbot.research.utils.simulator import make_new_predictions
from footbot.research.utils.simulator import make_team_selection
from footbot.research.utils.simulator import make_transfers
from footbot.research.utils.simulator import simulate_event
from footbot.research.utils.simulator import simulate_events

test_season = "1920"
test_event = 1
test_events = [1, 2, 3]
dataset = "integration_tests"


@pytest.fixture(scope="session")
def all_elements_df(client):

    all_elements_df = get_all_elements_df(test_season, client)

    return all_elements_df


@pytest.fixture(scope="session")
def all_predictions_df(client):

    all_predictions_df = run_query(
        f"SELECT * FROM `footbot-001.{dataset}.test_predictions_retrieve`", client
    )

    return all_predictions_df


@pytest.fixture(scope="session")
def all_results_df(client):

    all_results_df = get_all_results_df(test_season, client)

    return all_results_df


@pytest.fixture(scope="session")
def elements_df(all_elements_df):

    elements_df = all_elements_df.copy()
    elements_df = elements_df.loc[elements_df["event"] == test_event, :]

    return elements_df


@pytest.fixture(scope="session")
def predictions_df(all_predictions_df):

    predictions_df = all_predictions_df.copy()
    predictions_df = predictions_df.loc[
        predictions_df["prediction_event"] == test_event, :
    ]

    return predictions_df


def test_get_all_elements_df(all_elements_df):

    assert set(all_elements_df.columns) == {
        "event",
        "element_all",
        "safe_web_name",
        "element_type",
        "team",
        "value",
    }
    assert len(all_elements_df) == 23534
    assert len(all_elements_df) == len(
        all_elements_df[["event", "element_all"]].drop_duplicates()
    )


def test_get_all_results_df(all_results_df):

    assert set(all_results_df.columns) == {
        "event",
        "element_all",
        "minutes",
        "total_points",
    }
    assert len(all_results_df) == 22275
    assert len(all_results_df) == len(
        all_results_df[["event", "element_all"]].drop_duplicates()
    )


def test_make_transfers_from_scratch(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        event=test_event,
        events_to_look_ahead=0,
        weight=1.0,
        existing_squad=[],
        total_budget=1000,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=15,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    assert set(existing_squad) == {
        416,
        669,
        841,
        659,
        717,
        51,
        1051,
        273,
        126,
        304,
        67,
        771,
        451,
        714,
        1022,
    }
    assert bank == 0
    assert transfers == {
        "transfers_in": {
            416,
            67,
            771,
            451,
            841,
            714,
            717,
            304,
            273,
            659,
            51,
            1022,
            1051,
            669,
            126,
        },
        "transfers_out": set(),
    }


def test_make_transfers_from_existing(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        event=test_event,
        events_to_look_ahead=0,
        weight=1.0,
        existing_squad=[
            213,
            78,
            1175,
            295,
            753,
            1105,
            1200,
            266,
            512,
            394,
            312,
            463,
            401,
            717,
            118,
        ],
        total_budget=1000,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    assert set(existing_squad) == {
        1200,
        213,
        266,
        512,
        841,
        1175,
        118,
        394,
        717,
        312,
        78,
        401,
        753,
        463,
        1105,
    }
    assert bank == 120
    assert transfers == {"transfers_in": {841}, "transfers_out": {295}}


def test_make_team_selection(elements_df, predictions_df):

    first_team, bench, captain, vice = make_team_selection(
        event=test_event,
        existing_squad=[
            213,
            78,
            1175,
            295,
            753,
            1105,
            1200,
            266,
            512,
            394,
            312,
            463,
            401,
            717,
            118,
        ],
        total_budget=1000,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    assert set(first_team) == {1200, 213, 266, 512, 1175, 118, 394, 717, 312, 78, 1105}
    assert set(bench) == {295, 401, 753, 463}
    assert set(captain) == {717}
    assert set(vice) == {312}


def get_predictions_df(season, event, client):

    predictions_df = pd.DataFrame(
        [
            {
                "element_all": 1,
                "event": event,
                "prediction_event": event,
                "predicted_total_points": 10.0,
                "safe_web_name": "alan",
            }
        ]
    )

    return predictions_df


def test_make_new_predictions(client):

    table = "test_predictions_save"

    all_predictions_df = make_new_predictions(
        test_season, test_events, get_predictions_df, dataset, table, True, client
    )
    all_predictions_df = all_predictions_df.sort_values(
        ["prediction_event", "event", "element_all"]
    ).reset_index(drop=True)

    saved_df = run_query(f"SELECT * FROM `footbot-001.{dataset}.{table}`", client)
    saved_df = saved_df.sort_values(
        ["prediction_event", "event", "element_all"]
    ).reset_index(drop=True)

    assert set(all_predictions_df["prediction_event"].unique()) == set(test_events)
    pd.testing.assert_frame_equal(all_predictions_df, saved_df)


def test_simulate_event(all_elements_df, all_predictions_df, all_results_df, client):

    output = simulate_event(
        event=test_event,
        purchase_price_dict={},
        all_elements_df=all_elements_df,
        all_predictions_df=all_predictions_df,
        all_results_df=all_results_df,
        existing_squad=[],
        bank=None,
        transfers_made=None,
        events_to_look_ahead=0,
        weight=1.0,
        events_to_look_ahead_from_scratch=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        wildcard_events=[],
        events_to_look_ahead_wildcard=0,
        free_hit_events=[],
        existing_squad_revert=[],
        triple_captain_events=[],
        bench_boost_events=[],
    )

    assert output


def test_simulate_events(all_elements_df, all_predictions_df, all_results_df, client):

    simulation_results_arr = simulate_events(
        events=test_events,
        all_elements_df=all_elements_df,
        all_predictions_df=all_predictions_df,
        all_results_df=all_results_df,
        events_to_look_ahead=0,
        weight=1.0,
        events_to_look_ahead_from_scratch=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        wildcard_events=[],
        events_to_look_ahead_wildcard=0,
        free_hit_events=[],
        triple_captain_events=[],
        bench_boost_events=[],
    )

    total_event_points = sum(i["event_points"] for i in simulation_results_arr)

    assert total_event_points == 160


def test_simulate_events_wildcard(
    all_elements_df, all_predictions_df, all_results_df, client
):

    simulation_results_arr = simulate_events(
        events=test_events,
        all_elements_df=all_elements_df,
        all_predictions_df=all_predictions_df,
        all_results_df=all_results_df,
        events_to_look_ahead=0,
        weight=1.0,
        events_to_look_ahead_from_scratch=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=0,
        wildcard_events=[2],
        events_to_look_ahead_wildcard=0,
        free_hit_events=[],
        triple_captain_events=[],
        bench_boost_events=[],
    )

    squad_event_1 = (
        simulation_results_arr[0]["first_team"] + simulation_results_arr[0]["bench"]
    )
    squad_event_2 = (
        simulation_results_arr[1]["first_team"] + simulation_results_arr[1]["bench"]
    )
    squad_event_3 = (
        simulation_results_arr[2]["first_team"] + simulation_results_arr[2]["bench"]
    )

    assert set(squad_event_1) != set(squad_event_2)
    assert set(squad_event_2) == set(squad_event_3)  # we enforce no transfers


def test_simulate_events_free_hit(
    all_elements_df, all_predictions_df, all_results_df, client
):

    simulation_results_arr = simulate_events(
        events=test_events,
        all_elements_df=all_elements_df,
        all_predictions_df=all_predictions_df,
        all_results_df=all_results_df,
        events_to_look_ahead=0,
        weight=1.0,
        events_to_look_ahead_from_scratch=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=0,
        wildcard_events=[],
        events_to_look_ahead_wildcard=0,
        free_hit_events=[2],
        triple_captain_events=[],
        bench_boost_events=[],
    )

    squad_event_1 = (
        simulation_results_arr[0]["first_team"] + simulation_results_arr[0]["bench"]
    )
    squad_event_2 = (
        simulation_results_arr[1]["first_team"] + simulation_results_arr[1]["bench"]
    )
    squad_event_3 = (
        simulation_results_arr[2]["first_team"] + simulation_results_arr[2]["bench"]
    )

    assert set(squad_event_1) == set(squad_event_3)  # we enforce no transfers
    assert set(squad_event_1) != set(squad_event_2)
