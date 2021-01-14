import numpy as np
import pytest

from footbot.research.utils.simulator import get_elements_df
from footbot.research.utils.simulator import get_results_df
from footbot.research.utils.simulator import make_team_selection
from footbot.research.utils.simulator import make_transfers
from footbot.research.utils.simulator import simulate_event
from footbot.research.utils.simulator import simulate_events

test_season = "1920"
test_event = 1
test_events = [1, 2, 3]
dataset = "integration_tests"


@pytest.fixture(scope="session")
def elements_df(client):
    return get_elements_df(test_season, test_event, client)


def test_get_elements_df(elements_df):

    assert set(elements_df.columns) == {
        "element_all",
        "safe_web_name",
        "element_type",
        "team",
        "value",
    }
    assert len(elements_df) == 558
    assert len(elements_df["element_all"]) == len(
        elements_df["element_all"].drop_duplicates()
    )


def test_get_results_df(client):
    df = get_results_df(test_season, test_event, client)

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


@pytest.fixture()
def predictions_df(client):

    predictions_df = get_predictions_df(test_season, test_event, client)

    return predictions_df


def test_make_transfers_from_scratch(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        event=test_event,
        events_to_look_ahead=0,
        existing_squad=[],
        total_budget=1000,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=15,
        wildcard=False,
        free_hit=False,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    assert existing_squad != []


def test_make_transfers_from_existing(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        event=test_event,
        events_to_look_ahead=0,
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
        wildcard=False,
        free_hit=False,
        predictions_df=predictions_df,
        elements_df=elements_df,
    )

    assert existing_squad != []


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

    assert first_team != []
    assert bench != []
    assert captain != []
    assert vice != []


def test_simulate_event(predictions_df, client):

    output = simulate_event(
        season=test_season,
        event=test_event,
        purchase_price_dict={},
        all_predictions_df=predictions_df,
        existing_squad=[],
        bank=None,
        transfers_made=None,
        events_to_look_ahead=0,
        events_to_look_ahead_from_scratch=0,
        first_team_factor=0.9,
        bench_factor=0.1,
        captain_factor=0.9,
        vice_factor=0.1,
        transfer_penalty=0,
        transfer_limit=1,
        wildcard=False,
        events_to_look_ahead_wildcard=0,
        free_hit=False,
        events_to_look_ahead_free_hit=0,
        revert_team=False,
        existing_squad_revert=[],
        triple_captain=False,
        bench_boost=False,
        client=client,
    )

    assert output


def test_simulate_events_save_predictions(client):

    output = simulate_events(
        season=test_season,
        events=test_events,
        get_predictions_df=get_predictions_df,
        events_to_look_ahead=0,
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
        events_to_look_ahead_free_hit=0,
        triple_captain_events=[],
        bench_boost_events=[],
        dataset=dataset,
        table="test_predictions_save",
        save_new_predictions=True,
        client=client,
    )

    assert output


def test_simulate_events_retrieve_predictions(client):

    simulation_results_arr = simulate_events(
        season=test_season,
        events=test_events,
        get_predictions_df=get_predictions_df,
        events_to_look_ahead=0,
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
        events_to_look_ahead_free_hit=0,
        triple_captain_events=[],
        bench_boost_events=[],
        dataset=dataset,
        table="test_predictions_retrieve",
        save_new_predictions=False,
        client=client,
    )

    total_event_points = sum(i["event_points"] for i in simulation_results_arr)

    assert total_event_points == 160
