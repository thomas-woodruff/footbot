import pandas as pd
import pytest

from footbot.research.utils.simulator import aggregate_predictions
from footbot.research.utils.simulator import get_points_calculator_input
from footbot.research.utils.simulator import get_team_selector_input
from footbot.research.utils.simulator import make_transfers
from footbot.research.utils.simulator import set_event_state


def test_aggregate_predictions():
    predictions_df = pd.DataFrame(
        [
            {"element_all": 1, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 1, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 1, "event": 3, "predicted_total_points": 3.0},
            {"element_all": 2, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 2, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 2, "event": 4, "predicted_total_points": 3.0},
            {"element_all": 3, "event": 1, "predicted_total_points": 1.0},
            {"element_all": 3, "event": 2, "predicted_total_points": 2.0},
            {"element_all": 3, "event": 2, "predicted_total_points": 3.0},
            {"element_all": 3, "event": 3, "predicted_total_points": 3.0},
        ]
    )

    df = aggregate_predictions(predictions_df, 1, 3)

    expected_df = pd.DataFrame(
        [
            {"element_all": 1, "avg_predicted_total_points": 2.0},
            {"element_all": 2, "avg_predicted_total_points": 1.0},
            {"element_all": 3, "avg_predicted_total_points": 3.0},
        ]
    )

    pd.testing.assert_frame_equal(df, expected_df)


def test_get_team_selector_input():
    predictions_df = pd.DataFrame(
        [{"element_all": 1, "event": 1, "predicted_total_points": 1.0}]
    )

    elements_df = pd.DataFrame(
        [
            {"element_all": 1, "element_type": 1, "team": 1, "value": 10.0},
            {"element_all": 2, "element_type": 4, "team": 3, "value": 7.5},
        ]
    )

    players = get_team_selector_input(predictions_df, elements_df, 1, 1)

    expected_players = [
        {
            "element": 1,
            "element_type": 1,
            "team": 1,
            "value": 10.0,
            "avg_predicted_total_points": 1.0,
        },
        {
            "element": 2,
            "element_type": 4,
            "team": 3,
            "value": 7.5,
            "avg_predicted_total_points": 0.0,
        },
    ]

    assert players == expected_players


def test_get_points_calculator_input():
    results_df = pd.DataFrame(
        [
            {"element_all": 1, "minutes": 60, "total_points": 4},
            {"element_all": 2, "minutes": 90, "total_points": 5},
            {"element_all": 4, "minutes": 45, "total_points": 8},
        ]
    )

    elements_df = pd.DataFrame(
        [
            {"element_all": 1, "element_type": 1, "team": 1, "value": 10.0},
            {"element_all": 2, "element_type": 1, "team": 3, "value": 7.5},
            {"element_all": 3, "element_type": 1, "team": 3, "value": 7.5},
            {"element_all": 4, "element_type": 1, "team": 3, "value": 7.5},
        ]
    )

    first_team = [1, 2, 3]
    bench = [4]
    captain = [1]
    vice = [2]

    expected_first_team_dict = [
        {
            "element_all": 1,
            "element_type": 1,
            "minutes": 60,
            "total_points": 4,
            "is_captain": True,
            "is_vice": False,
        },
        {
            "element_all": 2,
            "element_type": 1,
            "minutes": 90,
            "total_points": 5,
            "is_captain": False,
            "is_vice": True,
        },
        {
            "element_all": 3,
            "element_type": 1,
            "minutes": 0,
            "total_points": 0,
            "is_captain": False,
            "is_vice": False,
        },
    ]

    expected_bench_dict = [
        {
            "element_all": 4,
            "element_type": 1,
            "minutes": 45,
            "total_points": 8,
            "is_captain": False,
            "is_vice": False,
        },
    ]

    first_team_dict, bench_dict = get_points_calculator_input(
        results_df, elements_df, first_team, bench, captain, vice
    )

    assert first_team_dict == expected_first_team_dict
    assert bench_dict == expected_bench_dict


@pytest.fixture
def elements_df():

    return pd.DataFrame(
        [
            {
                "element_all": 1,
                "value": 40,
                "element_type": 1,
                "team": 1,
            },
            {
                "element_all": 2,
                "value": 40,
                "element_type": 1,
                "team": 2,
            },
            {
                "element_all": 3,
                "value": 40,
                "element_type": 1,
                "team": 3,
            },
            {
                "element_all": 4,
                "value": 40,
                "element_type": 2,
                "team": 4,
            },
            {
                "element_all": 5,
                "value": 40,
                "element_type": 2,
                "team": 5,
            },
            {
                "element_all": 6,
                "value": 40,
                "element_type": 2,
                "team": 6,
            },
            {
                "element_all": 7,
                "value": 40,
                "element_type": 2,
                "team": 7,
            },
            {
                "element_all": 8,
                "value": 40,
                "element_type": 2,
                "team": 8,
            },
            {
                "element_all": 9,
                "value": 40,
                "element_type": 2,
                "team": 9,
            },
            {
                "element_all": 10,
                "value": 40,
                "element_type": 3,
                "team": 10,
            },
            {
                "element_all": 11,
                "value": 40,
                "element_type": 3,
                "team": 11,
            },
            {
                "element_all": 12,
                "value": 40,
                "element_type": 3,
                "team": 12,
            },
            {
                "element_all": 13,
                "value": 40,
                "element_type": 3,
                "team": 13,
            },
            {
                "element_all": 14,
                "value": 40,
                "element_type": 3,
                "team": 14,
            },
            {
                "element_all": 15,
                "value": 40,
                "element_type": 3,
                "team": 15,
            },
            {
                "element_all": 16,
                "value": 40,
                "element_type": 4,
                "team": 16,
            },
            {
                "element_all": 17,
                "value": 40,
                "element_type": 4,
                "team": 17,
            },
            {
                "element_all": 18,
                "value": 40,
                "element_type": 4,
                "team": 18,
            },
            {
                "element_all": 19,
                "value": 40,
                "element_type": 4,
                "team": 19,
            },
            {
                "element_all": 20,
                "value": 40,
                "element_type": 4,
                "team": 20,
            },
        ]
    )


@pytest.fixture
def predictions_df():

    return pd.DataFrame(
        [
            {
                "element_all": 1,
                "event": 1,
                "predicted_total_points": 4,
            },
            {
                "element_all": 2,
                "event": 1,
                "predicted_total_points": 5,
            },
            {
                "element_all": 3,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 4,
                "event": 1,
                "predicted_total_points": 4,
            },
            {
                "element_all": 5,
                "event": 1,
                "predicted_total_points": 5,
            },
            {
                "element_all": 6,
                "event": 1,
                "predicted_total_points": 5,
            },
            {
                "element_all": 7,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 8,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 9,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 10,
                "event": 1,
                "predicted_total_points": 4,
            },
            {
                "element_all": 11,
                "event": 1,
                "predicted_total_points": 5,
            },
            {
                "element_all": 12,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 13,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 14,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 15,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 16,
                "event": 1,
                "predicted_total_points": 4,
            },
            {
                "element_all": 17,
                "event": 1,
                "predicted_total_points": 6,
            },
            {
                "element_all": 18,
                "event": 1,
                "predicted_total_points": 6.5,
            },
            {
                "element_all": 19,
                "event": 1,
                "predicted_total_points": 7,
            },
            {
                "element_all": 20,
                "event": 1,
                "predicted_total_points": 3,
            },
        ]
    )


def test_set_event_state_first_event(elements_df):

    assert set_event_state(1, [], None, None, False, False, [], elements_df,) == (
        [],
        1000,
        1,
        [],
    )


def test_set_event_state_single_transfer(elements_df):

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        400,
        1,
        False,
        False,
        [],
        elements_df,
    ) == (
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        1000,
        1,
        [],
    )


def test_set_event_state_no_transfers(elements_df):

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        400,
        0,
        False,
        False,
        [],
        elements_df,
    ) == (
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        1000,
        2,
        [],
    )


def test_set_event_state_many_transfers(elements_df):

    assert set_event_state(
        2,
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        400,
        3,
        False,
        False,
        [],
        elements_df,
    ) == (
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        1000,
        1,
        [],
    )


def test_make_transfers_from_scratch(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [],
        600,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        15,
        False,
        False,
        predictions_df,
        elements_df,
    )

    assert set(existing_squad) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11}
    assert bank == 0
    assert transfers == {
        "transfers_in": set(existing_squad),
        "transfers_out": set(),
    }


def test_make_transfers_from_existing(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        600,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        1,
        False,
        False,
        predictions_df,
        elements_df,
    )

    assert set(existing_squad) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11}
    assert bank == 0
    assert transfers == {
        "transfers_in": {3},
        "transfers_out": {1},
    }


def test_make_transfers_wildcard(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        600,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        0,
        True,
        False,
        predictions_df,
        elements_df,
    )

    assert set(existing_squad) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11}
    assert bank == 0
    assert transfers == {
        "transfers_in": {3},
        "transfers_out": {1},
    }


def test_make_transfers_free_hit(elements_df, predictions_df):

    existing_squad, bank, transfers = make_transfers(
        1,
        0,
        [1, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11],
        600,
        0.9,
        0.1,
        0.9,
        0.1,
        0,
        0,
        False,
        True,
        predictions_df,
        elements_df,
    )

    assert set(existing_squad) == {3, 7, 8, 9, 12, 13, 14, 15, 17, 18, 19, 2, 5, 6, 11}
    assert bank == 0
    assert transfers == {
        "transfers_in": {3},
        "transfers_out": {1},
    }
